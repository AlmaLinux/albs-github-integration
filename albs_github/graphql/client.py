import logging
from typing import (
    Dict,
    List,
    Optional,
    Tuple,
    Union,
)

import aiohttp
import jmespath

from .models import *
from .mutations import *
from .queries import *

FieldsReturnType = Dict[str, Union[BaseField, SingleSelectProjectField]]


class BaseGHGraphQLClient:
    def __init__(self, github_token: str, verbose: bool = False):
        self.__github_token = github_token
        self.headers = {
            'Authorization': f'Bearer {self.__github_token}',
            'Accept': 'application/vnd.github+json',
        }
        self.__api_url = 'https://api.github.com/graphql'
        logger_level = logging.DEBUG if verbose else logging.INFO
        self.__logger = logging.getLogger(__name__)
        self.__logger.setLevel(logger_level)

    async def make_request(
        self,
        query: str,
        variables: Optional[dict] = None,
    ) -> dict:
        payload = {'query': query}
        if variables:
            payload['variables'] = variables
        async with aiohttp.request(
            'POST',
            self.__api_url,
            json=payload,
            headers=self.headers,
        ) as response:
            resp_json = await response.json()
            return resp_json

    @property
    def github_token(self) -> str:
        return self.__github_token


class IntegrationsGHGraphQLClient(BaseGHGraphQLClient):
    def __init__(
        self,
        github_token: str,
        organization_name: str,
        project_number: int,
        default_repository_name: str,
    ):
        super().__init__(github_token)
        self.__org_name = organization_name
        self.__project_number = project_number
        self.__project_id = None
        self.__default_repo_name = default_repository_name
        self.__default_repository_id = None
        self.__base_query_variables = {
            'org_name': self.__org_name,
            'project_number': self.__project_number,
            'repo_name': default_repository_name,
        }
        self.__issues_cache = {}
        self.__issues_content_cache = {}
        self.__fields_cache = {}

    @property
    def organization(self) -> str:
        return self.__org_name

    @property
    def project_number(self) -> int:
        return self.__project_number

    @property
    def project_id(self) -> Optional[str]:
        return self.__project_id

    @property
    def repository_id(self) -> Optional[str]:
        return self.__default_repository_id

    @staticmethod
    def parse_project_data(response: dict) -> Union[Dict, List]:
        return jmespath.search('data.organization.projectV2', response)

    async def get_project_fields(
        self, reload: bool = False
    ) -> FieldsReturnType:
        if self.__fields_cache and not reload:
            return self.__fields_cache
        self.__fields_cache = {}
        data_query = 'data.organization.projectV2.fields.nodes'
        raw_data = await self.make_request(
            QUERY_ORG_PROJECT_FIELDS,
            variables=self.__base_query_variables,
        )
        project_fields_data = jmespath.search(data_query, raw_data)
        for field in project_fields_data:
            if field['__typename'] == 'ProjectV2SingleSelectField':
                field_obj = SingleSelectProjectField(**field)
            else:
                field_obj = BaseField(**field)
            self.__fields_cache[field_obj.name] = field_obj
        return self.__fields_cache

    async def get_project_issues(self, reload: bool = False):
        def parse_project_items(payload: dict):
            for item_data in payload['items']['nodes']:
                content_data = item_data.pop('content', {})
                if content_data.get('__typename') == 'DraftIssue':
                    content = DraftIssueContent(**content_data)
                elif content_data.get('__typename') == 'Issue':
                    content = IssueContent(**content_data)
                else:
                    content = PullRequestContent(**content_data)
                project_item = ProjectItem(**item_data)
                project_item.content = content
                project_item.project_id = self.__project_id
                project_item.fields = {}
                # Search for connected repository
                for field in item_data['fieldValues']['nodes']:
                    type_name = field.get('__typename')
                    if type_name == 'ProjectV2ItemFieldRepositoryValue':
                        project_item.repository_id = field['repository']['id']
                        continue

                    field_name = field["field"]["name"]
                    filed_value = (
                        field["name"]
                        if type_name
                        == "ProjectV2ItemFieldSingleSelectValue"
                        else field["text"]
                    )

                    project_item.fields[field_name] = {
                        "name": field_name,
                        "value": filed_value,
                        "filed_id": field["field"]["id"],
                        "value_id": field["id"]
                    }
                self.__issues_cache[project_item.id] = project_item
                self.__issues_content_cache[content.id] = project_item

        if self.__issues_cache and not reload:
            return self.__issues_cache

        self.__issues_cache = {}
        query = generate_project_issues_query()
        raw_data = await self.make_request(
            query,
            variables=self.__base_query_variables,
        )
        project_data = self.parse_project_data(raw_data)
        self.__project_id = project_data['id']
        page_info = project_data['items']['pageInfo']
        parse_project_items(project_data)
        while page_info['hasNextPage']:
            cursor = page_info['endCursor']
            query = generate_project_issues_query(next_cursor=cursor)
            raw_data = await self.make_request(
                query,
                variables=self.__base_query_variables,
            )
            project_data = self.parse_project_data(raw_data)
            page_info = project_data['items']['pageInfo']
            parse_project_items(project_data)
        return self.__issues_cache

    async def get_project_content_issues(self, reload: bool = False):
        if reload:
            await self.get_project_issues(reload = True)
        return self.__issues_content_cache

    async def initialize(self):
        await self.get_project_fields()
        await self.get_project_issues()
        repository_data = await self.make_request(
            QUERY_ORG_REPOSITORY_INFO,
            variables=self.__base_query_variables,
        )
        self.__default_repository_id = jmespath.search(
            'data.organization.repository.id',
            repository_data,
        )

    async def __set_single_select_field(
        self,
        column_name: str,
        option_name: str,
        issue_id: str,
    ):
        column: SingleSelectProjectField = self.__fields_cache.get(column_name)
        if not column:
            raise ValueError(f'Incorrect column name: {column_name}')
        option = None
        for opt in column.options:
            if opt.name == option_name:
                option = opt
                break
        if not option:
            ValueError(
                f'Incorrect option for the column {column_name}: {option_name}'
            )
        mutation = generate_project_field_modification_mutation(
            value_type='single_select'
        )
        variables = {
            'project_id': self.__project_id,
            'item_id': issue_id,
            'field_id': column.id,
            'option_id': option.id,
        }
        await self.make_request(mutation, variables=variables)

    async def set_text_field(
        self,
        issue_id: str,
        field_name: str,
        field_value: str,
    ):
        field: BaseField = self.__fields_cache.get(field_name)
        if not field:
            raise ValueError(f'No such field: {field_name}')
        variables = {
            'project_id': self.__project_id,
            'item_id': issue_id,
            'field_id': field.id,
            'text': field_value,
        }
        mutation = generate_project_field_modification_mutation()
        await self.make_request(mutation, variables=variables)

    async def set_issue_status(self, issue_id: str, status: str):
        await self.__set_single_select_field('Status', status, issue_id)

    async def set_issue_platform(self, issue_id: str, platform_name: str):
        await self.__set_single_select_field(
            'Platform',
            platform_name,
            issue_id,
        )

    async def create_issue(
        self,
        title: str,
        body: str,
        initial_status: str = 'Todo',
        repository_id: Optional[str] = None,
    ) -> Tuple[str, str]:
        repo_id = repository_id or self.__default_repository_id
        # Validate inputs
        if not title:
            raise ValueError('Issue title cannot be empty string')
        if not body:
            raise ValueError('Issue body cannot be empty string')
        # Create issue on the repository
        variables = {'repository_id': repo_id, 'title': title, 'body': body}
        response = await self.make_request(
            MUTATION_CREATE_ISSUE,
            variables=variables,
        )
        new_issue_id = jmespath.search('data.createIssue.issue.id', response)

        # Create project item
        variables = {
            'project_id': self.__project_id,
            'github_item_id': new_issue_id,
        }
        response = await self.make_request(
            MUTATION_CREATE_PROJECT_ITEM,
            variables=variables,
        )
        project_item_id = jmespath.search(
            'data.addProjectV2ItemById.item.id', response
        )
        await self.set_issue_status(project_item_id, initial_status)
        return new_issue_id, project_item_id

    async def create_comment(
        self,
        body: str,
        item_id: str,
    ):
        # Validate inputs
        if not item_id:
            raise ValueError('Item ID cannot be empty string')
        if not body:
            raise ValueError('Comment body cannot be empty string')
        variables = {'github_item_id': item_id, 'body': body}
        response = await self.make_request(
            MUTATION_ADD_COMMENT,
            variables=variables,
        )
        return response

    async def serach_issues(self, query: str):
        if not query:
            raise ValueError('Query cannot be empty string')
        org_name = self.__org_name
        repo_name = self.__default_repo_name
        variables = {
            'query': f"{query} repo:{org_name}/{repo_name} state:open",
        }
        response = await self.make_request(
            QUERY_SEARCH_ISSUE,
            variables=variables,
        )
        return response

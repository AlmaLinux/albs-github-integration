from typing import List, Optional, Union

from pydantic import BaseModel

__all__ = [
    'BaseContent',
    'BaseField',
    'DraftIssueContent',
    'IssueContent',
    'ProjectItem',
    'PullRequestContent',
    'SingleSelectOption',
    'SingleSelectProjectField',
]


class SingleSelectOption(BaseModel):
    id: str
    name: str
    description: Optional[str]


class BaseField(BaseModel):
    __typename: str
    id: str
    name: str

    @property
    def type_name(self) -> str:
        return self.__typename


class BaseContent(BaseModel):
    id: str
    body: str
    title: str


class SingleSelectProjectField(BaseField):
    options: List[SingleSelectOption]


class DraftIssueContent(BaseContent):
    pass


class IssueContent(BaseContent):
    id: str
    number: int
    state: str


class PullRequestContent(BaseContent):
    number: int


class ProjectItem(BaseModel):
    id: str
    type: str
    content: Optional[
        Union[DraftIssueContent, IssueContent, PullRequestContent]] = None
    project_id: Optional[str] = None
    repository_id: Optional[str] = None
    fields: Optional[dict] = None

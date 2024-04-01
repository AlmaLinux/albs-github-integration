# This file contains functions that create queries to the GitHub GraphQL API
from typing import Optional

__all__ = [
    'QUERY_ORG_PROJECT_FIELDS',
    'QUERY_SEARCH_ISSUE',
    'QUERY_ORG_REPOSITORY_INFO',
    'generate_project_issues_query',
]

QUERY_SEARCH_ISSUE = """
query SearchIssue($query: String!) {
  search(
    type: ISSUE
    query: $query
    last: 30
  ) {
    issueCount
    edges {
      node {
        ... on Issue {
          id
          title
          body
          number
        }
      }
    }
  }
}
""".strip()

QUERY_ORG_PROJECT_FIELDS = """
query GetOrgProjectFields($org_name: String!, $project_number: Int!) {
    organization(login: $org_name) {
        projectV2(number: $project_number) {
            fields(first: 100) {
                nodes {
                    ... on ProjectV2FieldCommon {
                        __typename
                        name
                        id
                    }
                    ... on ProjectV2SingleSelectField {
                        name
                        options {
                            id
                            name
                            description
                        }
                    }
                }
            }
        }
    }
}
""".strip()

QUERY_ORG_PROJECT_ISSUES_TEMPLATE = """
query GetOrgProjectIssues($org_name: String!, $project_number: Int!) {
    organization(login: $org_name) {
        projectV2(number: $project_number) {
            title
            id
            items(%s) {
                pageInfo {
                    startCursor
                    endCursor
                    hasNextPage
                }
                nodes {
                    type
                    id
                    content {
                        __typename
                        ... on Issue {
                            id
                            body
                            state
                            title
                            number
                        }
                        ... on DraftIssue {
                            body
                            title
                            id
                        }
                        ... on PullRequest{
                            id
                            number
                            title
                            body
                        }
                    }
                    fieldValues(first: 100) {
                        nodes {
                            __typename
                            ... on ProjectV2ItemFieldTextValue {
                                id
                                text
                                field {
                                    __typename
                                    ... on ProjectV2Field {
                                        id
                                        name
                                    }
                                }
                            }
                            ... on ProjectV2ItemFieldSingleSelectValue {
                                id
                                name
                                optionId
                                field {
                                    __typename
                                    ... on ProjectV2SingleSelectField {
                                        id
                                        name
                                    }
                                }
                            }
                            ... on ProjectV2ItemFieldRepositoryValue {
                                repository {
                                    id
                                    name
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
"""

QUERY_ORG_REPOSITORY_INFO = """
query GetRepositoryInfo ($org_name: String!, $repo_name: String!){
    organization(login: $org_name) {
        repository (name: $repo_name) {
            id
        }
    }
}
""".strip()


def generate_project_issues_query(next_cursor: Optional[str] = None) -> str:
    if next_cursor:
        insert = f'first: 100, after: "{next_cursor}"'
    else:
        insert = 'first: 100'
    query = QUERY_ORG_PROJECT_ISSUES_TEMPLATE % insert
    return query

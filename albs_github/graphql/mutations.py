__all__ = [
    'generate_project_field_modification_mutation',
    'MUTATION_ADD_COMMENT',
    'MUTATION_CREATE_ISSUE',
    'MUTATION_ADD_COMMENT_TO_ISSUE',
    'MUTATION_CREATE_PROJECT_ITEM',
]

CHANGE_PROJECT_FIELD_VALUE_TEMPLATE = """
mutation ChangeProjectItemFieldValue(%s) {
    updateProjectV2ItemFieldValue (
        input: {
            projectId: $project_id
            itemId: $item_id
            fieldId: $field_id
            value: %s
        }
    ){
        projectV2Item {
            id
        }
    }
}
"""


def generate_project_field_modification_mutation(
    value_type: str = 'text'
) -> str:
    allowed = ('text', 'number', 'date', 'single_select', 'iteration')
    if value_type not in allowed:
        raise ValueError(f'Incorrect value type: {value_type}')
    if value_type == 'text':
        params_string = ('$project_id: ID!, $item_id: ID!, $field_id: ID!, '
                         '$text: String!')
        mutation_value = '{text: $text}'
    elif value_type == 'number':
        params_string = ('$project_id: ID!, $item_id: ID!, $field_id: ID!, '
                         '$number: Float!')
        mutation_value = '{number: $number}'
    elif value_type == 'date':
        params_string = ('$project_id: ID!, $item_id: ID!, $field_id: ID!, '
                         '$date: Date!')
        mutation_value = '{date: $date}'
    elif value_type == 'single_select':
        params_string = ('$project_id: ID!, $item_id: ID!, $field_id: ID!, '
                         '$option_id: String!')
        mutation_value = '{singleSelectOptionId: $option_id}'
    else:
        params_string = ('$project_id: ID!, $item_id: ID!, $field_id: ID!, '
                         '$iteration_id: String!')
        mutation_value = '{iterationId: $iteration_id}'
    mutation_string = CHANGE_PROJECT_FIELD_VALUE_TEMPLATE % (
        params_string, mutation_value)
    return mutation_string.strip()


MUTATION_ADD_COMMENT_TO_ISSUE = """
mutation AddCommentOnIssue($issue_id: ID!, $body_content: String!) {
    addComment (
        input: {
            body: $body_content,
            subjectId: $issue_id
        }
    ) {
        subject {
            id
        }
    }
}
""".strip()

MUTATION_CREATE_ISSUE = """
mutation CreateIssue($title: String!, $repository_id: ID!, $body: String!) {
    createIssue(
        input: {
            title: $title
            repositoryId: $repository_id
            body: $body
        }
    ){
        issue {
            id
        }
    }
}
""".strip()

# Comment can be added to different entities in GitHub
# (issue, pull request, draft, etc.), so $github_item_id parameter
# should be filled accordingly
MUTATION_ADD_COMMENT = """
mutation AddComment($body: String!, $github_item_id: ID!){
    addComment (
        input: {
            body: $body,
            subjectId: $github_item_id
        }
    ) {
        subject {
            id
        }
    }
}
""".strip()

MUTATION_CREATE_PROJECT_ITEM = """
mutation CreateProjectItem($project_id: ID!, $github_item_id: ID!) {
    addProjectV2ItemById(
        input: {
            projectId: $project_id
            contentId: $github_item_id
        }
    ) {
        item {
            id
        }
    }
}
""".strip()

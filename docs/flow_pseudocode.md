

# user input




def process_user_input_with_no_repo(user_message): # chat processor when no integrated repo is activated
    category = categorize_message(user_message) -> IntegratedRepo | Chat # integrated repo is one of the integrated repos. another option is simple chat
    if category is IntegratedRepo:
        actiavte_integrated_repo(category) # displays integrated repo, inserts integrated repo show command results into context
        tools = get_integrated_repo_toolset(category) # gets set of justfile tools
        respond_to_user(user_message, tools = tools) # get user response, execute tool calls if any
        loop_integrated_repo_input()

def loop_integrated_repo(user_message): # chat procesor when an integrated repo is activated
    tools = get_integrated_repo_toolset(self.integrated_repo)
    respond_to_user(user_message, tools = tools) # get user response, execute tool calls if any


def integrate_repo(repo_location):
    repo_metadata = examine_repo(repo_location): RepoMetadata
    # repo metadata include:
    # purpose of the repo
    # which just command should be the "show" command
    # PRD of view pane
    review_result = review_with_user(repo_metadata)
    if review_result == APPROVED:
        persist_repo_metadata
    else:
        # iterate with user until acceptance

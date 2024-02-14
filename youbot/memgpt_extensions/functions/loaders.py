import os
from memgpt.cli.cli_load import store_docs
from memgpt.cli.cli import attach
from llama_hub.github_repo import GithubClient, GithubRepositoryReader


def load_github_repo(self, owner: str, repo: str) -> str:
    """Function to load a Github repo into archival memory

    Args:
        owner (str): github owner of repo. For example, cpacker
        repo (str): name of repo, for example, MemGPT

    Returns:
        str: Response to query about the repo.
    """

    github_client = GithubClient(os.getenv("GITHUB_TOKEN"))
    loader = GithubRepositoryReader(
        github_client,
        owner=owner,
        repo=repo,
        filter_directories=([".github"], GithubRepositoryReader.FilterType.EXCLUDE),
        verbose=True,
        concurrent_requests=10,
    )
    docs = loader.load_data(branch="main")
    self.agent_state.user_id
    datasource_name = f"{owner}/{repo}"
    store_docs(datasource_name, docs, self.agent_state.user_id)
    attach(self.agent_state.name, datasource_name, self.agent_state.user_id)


def query_github_repo_loading(self, owner: str, repo: str, query: str) -> str:
    """Loads embeddings for a repo, and asks LLM's queries about it.

    Args:
        owner (str): owner of repo
        repo (str): name of repo
        query (str): description of repo

    Returns:
        str: response to query
    """
    import pickle
    import os

    from llama_index import download_loader, VectorStoreIndex

    download_loader("GithubRepositoryReader")

    from llama_hub.github_repo import GithubClient, GithubRepositoryReader

    docs = None

    dir = os.path.join("/tmp", "repo", owner, repo)
    if not os.path.exists(dir):
        os.makedirs(dir)

    pkl_path = os.path.join(dir, "docs.pkl")

    if os.path.exists(pkl_path):
        with open(pkl_path, "rb") as f:
            docs = pickle.load(f)

    if docs is None:
        github_client = GithubClient(os.getenv("GITHUB_TOKEN"))
        loader = GithubRepositoryReader(
            github_client,
            owner=owner,
            repo=repo,
            filter_directories=([".github"], GithubRepositoryReader.FilterType.EXCLUDE),
            filter_file_extensions=([".py"], GithubRepositoryReader.FilterType.INCLUDE),
            verbose=True,
            concurrent_requests=10,
        )

        docs = loader.load_data(branch="main")

        with open(pkl_path, "wb") as f:
            pickle.dump(docs, f)

    index = VectorStoreIndex.from_documents(docs)

    query_engine = index.as_query_engine()
    response = query_engine.query(query)
    print(response)


if __name__ == "__main__":

    class Querier(object):
        pass

    setattr(
        Querier, "query_github_repo_without_loading", query_github_repo_without_loading
    )
    Querier().query_github_repo_without_loading(
        "cpacker", "MemGPT", "how is the system prompt loaded into the agent?"
    )

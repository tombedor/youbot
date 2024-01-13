import pickle
import os

from llama_index import download_loader, VectorStoreIndex
download_loader("GithubRepositoryReader")

from llama_hub.github_repo import GithubClient, GithubRepositoryReader


def query_github_repo(owner: str, repo: str, query: str) -> str:
    """Function to answer queries about a github repository. First call may take time as embeddings must be generated.

    Args:
        owner (str): github owner of repo. For example, cpacker
        repo (str): name of repo, for example, MemGPT
        query (str): question to answer about repo. For example, "what doe the agent class do?"

    Returns:
        str: Response to query about the repo.
    """
    dir = os.path.join('/tmp', owner, repo)
    if not os.path.exists(dir):
        os.makedirs(dir)
    doc_path = os.path.join(dir, "docs.pkl")
    
    
    docs = None
    if os.path.exists(doc_path):
        with open(doc_path, "rb") as f:
            docs = pickle.load(f)

    if docs is None:
        github_client = GithubClient(os.getenv("GITHUB_TOKEN"))
        loader = GithubRepositoryReader(
            github_client,
            owner =                  "cpacker",
            repo =                   "MemGPT",
            filter_directories =     ([".github"], GithubRepositoryReader.FilterType.EXCLUDE),
            filter_file_extensions = ([".py"], GithubRepositoryReader.FilterType.INCLUDE),
            verbose =                True,
            concurrent_requests =    10,
        )

        docs = loader.load_data(branch="main")

        with open(doc_path, "wb") as f:
            pickle.dump(docs, f)

    index = VectorStoreIndex.from_documents(docs)

    query_engine = index.as_query_engine()
    return query_engine.query(query)

if __name__ == "__main__":
    print(query_github_repo("cpacker", "MemGPT", "how is the agent memory configured?"))
    print(query_github_repo("cpacker", "MemGPT", "how are personas used?"))
    
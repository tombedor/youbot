import os
from typing import List
from llama_index import (
    SimpleDirectoryReader,
    VectorStoreIndex,
    StorageContext,
)
from llama_index.vector_stores.faiss import FaissVectorStore

import logging
import sys

import json

from pathlib import Path

import psycopg2

from llama_index.service_context import ServiceContext
import llama_index
import faiss


logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logging.getLogger().addHandler(logging.StreamHandler(stream=sys.stdout))


service_context = ServiceContext.from_defaults()
service_context.llm.model = 'gpt-4-0613'
llama_index.global_service_context = service_context


WIKI_ROOT = Path("/Users/tbedor/Development/obsidian/")
WIKI_PAGE_ROOT = os.path.join(WIKI_ROOT, 'tbedor', 'Wiki')
WIKI_METADATA_ROOT = os.path.join(WIKI_ROOT, "metadata")



# dimensions of text-ada-embedding-002
d = 1536
faiss_index = faiss.IndexFlatL2(d)

documents = SimpleDirectoryReader("/Users/tbedor/Development/obsidian/", recursive=True).load_data()

vector_store = FaissVectorStore(faiss_index=faiss_index)
storage_context = StorageContext.from_defaults(vector_store=vector_store)
index = VectorStoreIndex.from_documents(
    documents, storage_context=storage_context
)
index.storage_context.persist()



query_engine = index.as_query_engine()


EXCLUDED_PAGES = [
    "Geography and places/Catgories.md",
    "Main.md"    
]
wiki_paths = [str(p.relative_to(WIKI_PAGE_ROOT)) for p in list(Path(WIKI_PAGE_ROOT).rglob("*.md"))]
wiki_paths = [p for p in wiki_paths if p not in EXCLUDED_PAGES]
wiki_paths_str = ",".join(wiki_paths)

def get_new_topics_for_fact(fact:str) -> str:
    query = f"""
    I have a private wikipedia with {len(wiki_paths)} pages.
    
    I have a fact, and I wish to determine whether it contains information about any topics that are not already covered in the wikipedia.
    
    The fact is: {fact}
    
    The existing pages are: {wiki_paths_str}
    
    Some examples of new pages that could be created are: other people, places, or events that are not already covered in the wikipedia.
    
    Response with a json object with two keys:
    path: the path of the new page. It should match the format of the other paths. It MUST be a markdown file.
    content: the initial content of the new page, in markdown format.
    
    
    If no new page should be created, please respond with an empty json object.
    """
    
    response = query_engine.query(query)
    dict = json.loads(response.response)
    if len(dict) > 0:
        path = dict['path']
        content = dict['content']
        full_path = os.path.join(WIKI_PAGE_ROOT, path)
        
        # make sure path is a markdown file
        if not path.endswith(".md"):
            return f"Path {path} is not a markdown file. Please respond with a path that ends with '.md'."
        
        with open(full_path, "w") as f:
            f.write(content)
    return response.response


def get_relevant_current_pages_for_fact(fact:str) -> List[str]:
    query = f"""
    I have a private wikipedia with {len(wiki_paths)} pages.

    I have a fact, and I wish to determine which pages the fact is relevant to.

    Please respond with a list of pages that the fact might be relevant to. Infer the topic of the page from the file path of the page, or from the page current contents.

    The fact is: {fact}

    The pages are: {wiki_paths_str}


    The response should be a list of pages, with the following information:
    page: the path to the page
    score: a number between 0 and 1, indicating the relevance of the fact to the page. You MUST provide a score
    reason: a string explaining why the page is relevant to the fact. You MUST provide a reason.


    """ + """Your response should be in JSON format, here is an example of a valid response:
    [
        {"page": "/path/to/page", "score": 0.5, "reason": "The reason that the page is relevant'."},
        
    ]
    """

    response = query_engine.query(query)
    response_dict = json.loads(response.response)
    pages = [p["page"] for p in response_dict if p['score'] > 0.5]
    return pages


def update_page_with_fact(page_path: str, fact: str):
    full_path = os.path.join(WIKI_PAGE_ROOT, page_path)

        
    if os.path.getsize(full_path) > 0:
        with open(full_path, "r") as f:
            current_contents = f.read()
        current_page_content_fragment = f"Incorporate the fact into the current page content: {current_contents}"
    else:
        current_page_content_fragment = "The page is currently empty. Incorporate the fact into the page content."
    
    query = f"""
    I have a private wikipedia. One such page is {page_path}.
    
    I have a fact that I wish to incorporate into the page. If the fact is already in the page, no changes should be made.
    
    The fact is: {fact}
    
    Your output should be the new content of the page, in markdown format.
    
    """ + current_page_content_fragment
    
    response = query_engine.query(query)
    
    with open(full_path, "w") as f:
        f.write(response.response)
    return response.response

def edit_page(full_path: str):
    """Edits and organizes the page

    Args:
        full_path (str): the full path to the page.
    """
    
    if os.path.getsize(full_path) > 0:
        with open(full_path, "r") as f:
            current_contents = f.read()
    else:
        current_contents = "The page is currently empty."
        
    dir = os.path.dirname(full_path)
    sibling_pages = ", ".join([p for p in wiki_paths if os.path.dirname(os.path.join(WIKI_PAGE_ROOT, p)) == dir and p not in full_path])
    
    relative_path = Path(full_path).relative_to(WIKI_PAGE_ROOT)
    
    query = f"""
    I have a private wikipedia with a page called: {relative_path}. I wish to edit and organize the page.
    
    The page should be organized and edited, such that it is easy to read and understand.
    
    Irrelevant information should be removed. 
    
    The page should begin with an introduction that describes what kind of information is contained within the page.
    
    The page's sibling pages are: {sibling_pages}. Content in {relative_path} should not repeat information that would better fit in sibling pages.
    
    This is the page's content:
    
    f{current_contents}
    
    Your response should be the content of the new page, in Markdown format.
    """
    
    response = query_engine.query(query).response
    with open(full_path, "w") as f:
        f.write(response)
    return response

def fetch_facts() -> List[str]:
    # query postgres for facts
    with psycopg2.connect(os.getenv("POSTGRES_URL")) as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT TEXT FROM memgpt_archival_memory_agent UNION ALL SELECT TEXT FROM memgpt_recall_memory_agent;")
            return [r[0] for r in cursor.fetchall()]    
        
def add_facts_to_pages(facts: List[str]):
    i = 0
    for fact in facts:
        i += 1
        print(f"Fact {i}/{len(facts)}")
        relevant_pages = get_relevant_current_pages_for_fact(fact)
        for page in relevant_pages:
            new_page_content = update_page_with_fact(page, fact)
            print(new_page_content)
            
def edit_pages():
    for wiki_path in wiki_paths:
        full_path = os.path.join(WIKI_PAGE_ROOT, wiki_path)
        edit_page(full_path)
        print("Edited page: ", full_path)
    
    
    
if __name__ == "__main__":
    facts = fetch_facts()
    print(f"found {len(facts)} facts")
    add_facts_to_pages(facts)
    for fact in facts:
        get_new_topics_for_fact(fact)

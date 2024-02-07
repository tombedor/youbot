import os
from typing import List
from celery import Celery
from llama_index import (
    SimpleDirectoryReader,
    VectorStoreIndex,
    StorageContext,
)
from llama_index.vector_stores.faiss import FaissVectorStore

import logging
import sys

import json

from pathlib import Path, PosixPath

import psycopg2

from llama_index.service_context import ServiceContext
import llama_index
import faiss

app = Celery('wiki', broker="redis://localhost:6379/0")

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logging.getLogger().addHandler(logging.StreamHandler(stream=sys.stdout))


service_context = ServiceContext.from_defaults()
service_context.llm.model = 'gpt-4-0613'
llama_index.global_service_context = service_context


WIKI_ROOT = PosixPath("/Users/tbedor/Development/obsidian/")
WIKI_PAGE_ROOT = PosixPath(os.path.join(WIKI_ROOT, 'tbedor', 'Wiki'))
WIKI_METADATA_ROOT = PosixPath(os.path.join(WIKI_ROOT, "metadata"))


class WikiPage:
    
    EXCLUDED_PAGES = [
        PosixPath("Geography and places/Catgories.md"),
        PosixPath("Overview.md")    
    ]
    
    @classmethod
    def all(cls) -> List["WikiPage"]:
        return [WikiPage(p) for p in list(Path(WIKI_PAGE_ROOT).rglob("*.md")) if WikiPage(p).relative_path not in cls.EXCLUDED_PAGES]
    
    
    def __init__(self, path: PosixPath):
        if type(path) != PosixPath:
            raise ValueError(f"Path {path} is not a PosixPath. Please respond with a PosixPath.")
        if path.suffix != ".md":
            raise ValueError(f"Path {path} is not a markdown file. Please respond with a path that ends with '.md'.")
        
        if path.is_absolute():
            self.relative_path = PosixPath(Path(path).relative_to(WIKI_ROOT))
            self.absolute_path = path
        else:
            self.relative_path = path
            self.absolute_path = PosixPath(os.path.join(WIKI_PAGE_ROOT, path))
        self.parent_path = self.absolute_path.parent
        
        if WIKI_PAGE_ROOT not in self.absolute_path.parents:
            raise ValueError(f"Path {path} is not within the wiki directory. Please respond with a path that is within the wiki directory: {WIKI_PAGE_ROOT}")
        
    def get_title(self) -> str:
        return str(self.relative_path).replace("/", " ").replace(".md", "")
        
    def get_content(self) -> str:
        if os.path.getsize(self.absolute_path) > 0:
            with open(self.absolute_path, "r") as f:
                return f.read()
        else:
            return None
        
    def get_sibling_pages(self) -> List[str]:
        return [p for p in WikiPage.all() if p.absolute_path.parent == self.parent_path and p.absolute_path != self.absolute_path]
    
    def get_child_pages(self) -> List[str]:
        return [p for p in WikiPage.all() if os.path.dirname(p.parent_path) == self.parent_path]
                
    def replace_content(self, new_content: str):
        with open(self.absolute_path, "w") as f:
            f.write(new_content)    
            
    def to_dict(self) -> dict:
        return {
            "absolute_path": str(self.absolute_path),
        }
        
    @classmethod        
    def from_dict(cls, d: dict):
        return WikiPage(PosixPath(d["absolute_path"]))

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


def get_new_topics_for_fact(fact: str) -> str:
    pages = WikiPage.all()
    
    query = f"""
    I have a private wikipedia with {len(pages)} pages.
    
    I have a fact, and I wish to determine whether it contains information about any topics that are not already covered in the wikipedia.
    
    The fact is: {fact}
    
    The existing pages are: {[p.relative_path for p in pages]}
    
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
        
        if not path.endswith(".md"):
            return f"Path {path} is not a markdown file. Please respond with a path that ends with '.md'."
        else:
            WikiPage(path).replace_content(content)
            
    return response.response


def get_relevant_current_pages_for_fact(fact:str) -> List[WikiPage]:
    pages = WikiPage.all()
    
    query = f"""
    I have a private wikipedia with {len(pages)} pages.

    I have a fact, and I wish to determine which pages the fact is relevant to.

    Please respond with a list of pages that the fact might be relevant to. Infer the topic of the page from the file path of the page, or from the page current contents.

    The fact is: {fact}

    The pages are: {[p.relative_path for p in pages]}


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
    pages = [WikiPage(PosixPath(p["page"])) for p in response_dict if p['score'] > 0.5]
    return pages

@app.task
def update_page_with_fact(wiki_page_arg: WikiPage | dict, fact: str):
    if type(wiki_page_arg) == dict:
        wiki_page = WikiPage.from_dict(wiki_page_arg)
    else:
        wiki_page = wiki_page_arg
    
    current_content = wiki_page.get_content() or "The page is currently empty."
    current_page_content_fragment = f"Incorporate the fact into the current page content: {current_content}"
    
    query = f"""
    I have a private wikipedia. One such page is {wiki_page.get_title()}.
    
    I have a fact that I wish to incorporate into the page. If the fact is already in the page, no changes should be made.
    
    The fact is: {fact}
    
    Your output should be the new content of the page, in markdown format.
    
    """ + current_page_content_fragment
    
    response = query_engine.query(query).response
    
    wiki_page.replace_content(response)
    return response.response


@app.task
def edit_page(page_arg: WikiPage | dict) -> str:
    """Edits and organizes the page

    Args:
        full_path (str): the full path to the page.
    """
    if type(page_arg) == dict:
        page = WikiPage.from_dict(page_arg)
    else:
        page = page_arg
    
    
    current_content = page.get_content() or "The page is currently empty."
    
    sibling_pages = ", ".join([p.get_title() for p in page.get_sibling_pages()])
    
    query = f"""
    I have a private wikipedia with a page called: {page.get_title()}. I wish to edit and organize the page.
    
    The page should be organized and edited, such that it is easy to read and understand.
    
    Irrelevant information should be removed. 
    
    The page should begin with an introduction that describes what kind of information is contained within the page.
    
    The page's sibling pages are: {sibling_pages}. Content in {page.get_title()} should not repeat information that would better fit in sibling pages.
    
    This is the page's content:
    
    f{current_content}
    
    Your response should be the content of the new page, in Markdown format.
    """
    
    response = query_engine.query(query).response
    
    page.replace_content(response)
    return response

def fetch_facts() -> List[str]:
    # query postgres for facts
    with psycopg2.connect(os.getenv("POSTGRES_URL")) as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT TEXT FROM memgpt_archival_memory_agent") #UNION ALL SELECT TEXT FROM memgpt_recall_memory_agent;")
            return [r[0] for r in cursor.fetchall()]    
        
@app.task
def add_facts_to_pages(fact: str) -> str:
    relevant_pages = get_relevant_current_pages_for_fact(fact)
    for page in relevant_pages:
        new_page_content = update_page_with_fact.delay(page.to_dict(), fact)
        print(new_page_content)
            
def edit_pages():
    for wiki_page in WikiPage.all():
        edit_page(wiki_page)
        print("Edited page: ", wiki_page.get_title())
    
    
    
if __name__ == "__main__":
    facts = fetch_facts()
    
    for f in facts:
        logging.info(f"Adding fact {f} to pages")
        add_facts_to_pages.delay(f)
    
    for page in WikiPage.all():
        logging.info(f"Editing page {page.absolute_path}")
        edit_page.delay(page.to_dict())

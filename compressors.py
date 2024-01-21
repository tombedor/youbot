from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import LLMChainExtractor
from langchain_openai import OpenAI

def foo(self):
    """prints foo
    """
    print('foo')

# def compress()
# llm = OpenAI(temperature=0)
# compressor = LLMChainExtractor.from_llm(llm)
# compression_retriever = ContextualCompressionRetriever(
#     base_compressor=compressor, base_retriever=retriever
# )

# compressed_docs = compression_retriever.get_relevant_documents(
#     "What did the president say about Ketanji Jackson Brown"
# )
# pretty_print_docs(compressed_docs)
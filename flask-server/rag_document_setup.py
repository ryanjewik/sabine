# %%
import getpass
import os
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

# %%
from langchain_core.documents import Document
import glob

# %%
os.environ["OPENAI_API_KEY"] = getpass.getpass("Enter your OpenAI API key: ")

# %%
MONDODB_URI = getpass.getpass("Enter your MongoDB connection string:")

# %%
mongodb_client = MongoClient(MONGODB_URI, server_api=ServerApi('1'))
mongodb_client.admin.command('ping')

# %%
docs = []
txt_folder = os.path.abspath(os.path.join(os.getcwd(), "../../game_information/"))
txt_files = glob.glob(os.path.join(txt_folder, "*.txt"))
for file_path in txt_files:
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    doc = Document(page_content=content, metadata={"source": os.path.basename(file_path)})
    docs.append(doc)
print(f"Loaded {len(txt_files)} txt files into docs.")

# %%
txt_folder = os.path.abspath(os.path.join(os.getcwd(), "../../player_script/player_profiles/"))
txt_files = glob.glob(os.path.join(txt_folder, "*.txt"))
for file_path in txt_files:
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    doc = Document(page_content=content, metadata={"source": os.path.basename(file_path)})
    docs.append(doc)
print(f"Loaded {len(txt_files)} txt files into docs.")

# %%
txt_folder = os.path.abspath(os.path.join(os.getcwd(), "../../S3_retrieval/match_stats/match_summaries/"))
txt_files = glob.glob(os.path.join(txt_folder, "*.txt"))
for file_path in txt_files:
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    doc = Document(page_content=content, metadata={"source": os.path.basename(file_path)})
    docs.append(doc)
print(f"Loaded {len(txt_files)} txt files into docs.")

# %%
len(docs)

# %%
from langchain_mongodb.retrievers import MongoDBAtlasParentDocumentRetriever
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

# %%
embedding_model = OpenAIEmbeddings(
    model="text-embedding-3-small",
    api_key=OPENAI_API_KEY,
)

# %%
DB_NAME = "sabine"
COLLECTION_NAME = "rag_docs"

# %%
def get_splitter(chunk_size: int) -> RecursiveCharacterTextSplitter:
    """
    Returns a token-based text splitter with overlap

    Args:
        chunk_size (_type_): Chunk size in number of tokens

    Returns:
        RecursiveCharacterTextSplitter: Recursive text splitter object
    """
    return RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        encoding_name="cl100k_base",
        chunk_size=chunk_size,
        chunk_overlap=20,
    )

# %%
parent_doc_retriever = MongoDBAtlasParentDocumentRetriever.from_connection_string(
    connection_string=MONGODB_URI,
    embedding_model=embedding_model,
    child_splitter=get_splitter(200),
    database_name=DB_NAME,
    collection_name=COLLECTION_NAME,
    text_key="page_content",
    search_kwargs={"top_k": 5},
)

# %%
import asyncio
from typing import Generator, List

# %%
BATCH_SIZE = 256
MAX_CONCURRENCY  =4

# %%
import openai
import re

async def process_batch(batch: Generator, semaphore: asyncio.Semaphore) -> None:
    """
    Ingest batches of documents into MongoDB, handling OpenAI rate limits.

    Args:
        batch (Generator): Chunk of documents to ingest
        semaphore (as): Asyncio semaphore
    """
    async with semaphore:
        while True:
            try:
                await parent_doc_retriever.aadd_documents(batch)
                print(f"Processed {len(batch)} documents")
                break  # Success, exit loop
            except openai.RateLimitError as e:
                wait_time = 60
                # Try to extract wait time from error message
                msg = str(e)
                match = re.search(r'try again in ([0-9.]+)s', msg)
                if match:
                    wait_time = float(match.group(1))
                print(f"Rate limit hit. Waiting {wait_time} seconds before retrying...")
                await asyncio.sleep(wait_time)

# %%
def get_batches(docs: List[Document], batch_size: int) -> Generator:
    """
    Return batches of documents to ingest into MongoDB

    Args:
        docs (List[Document]): List of LangChain documents
        batch_size (int): Batch size

    Yields:
        Generator: Batch of documents
    """
    for i in range(0, len(docs), batch_size):
        yield docs[i : i + batch_size]

# %%
async def process_docs(docs: List[Document]) -> List[None]:
    """
    Asynchronously ingest LangChain documents into MongoDB

    Args:
        docs (List[Document]): List of LangChain documents

    Returns:
        List[None]: Results of the task executions
    """
    semaphore = asyncio.Semaphore(MAX_CONCURRENCY)
    batches = get_batches(docs, BATCH_SIZE)

    tasks = []
    for batch in batches:
        tasks.append(process_batch(batch, semaphore))
    # Gather results from all tasks
    results = await asyncio.gather(*tasks)
    return results

# %%
collection = mongodb_client[DB_NAME][COLLECTION_NAME]
# Delete any existing documents from the collection
collection.delete_many({})
print("Deletion complete.")
# Ingest LangChain documents into MongoDB
results = await process_docs(docs)

# %%

from pymongo.errors import OperationFailure
from pymongo.operations import SearchIndexModel

# %%
VS_INDEX_NAME = "vector_index"

# %%
# Vector search index definition
model = SearchIndexModel(
    definition={
        "fields": [
            {
                "type": "vector",
                "path": "embedding",
                "numDimensions": 1536,
                "similarity": "cosine",
            }
        ]
    },
    name=VS_INDEX_NAME,
    type="vectorSearch",
)

# %%
# Check if the index already exists, if not create it
try:
    collection.create_search_index(model=model)
    print(
        f"Successfully created index {VS_INDEX_NAME} for collection {COLLECTION_NAME}"
    )
except OperationFailure:
    print(
        f"Duplicate index {VS_INDEX_NAME} found for collection {COLLECTION_NAME}. Skipping index creation."
    )



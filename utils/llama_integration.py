from llama_index.core import (
    SimpleDirectoryReader,
    VectorStoreIndex,
    StorageContext,
    load_index_from_storage,
    Settings,
)

from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core.ingestion import IngestionPipeline
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.extractors import TitleExtractor, QuestionsAnsweredExtractor
import os
from dotenv import load_dotenv
import asyncio

# Load environment variables
load_dotenv()

# Set up OpenAI API key
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    raise ValueError("OPENAI_API_KEY not found in environment variables")

# Configure global Settings
# Valid models: valid OpenAI model name in: o1-preview, o1-preview-2024-09-12, o1-mini, o1-mini-2024-09-12, gpt-4, gpt-4-32k, gpt-4-1106-preview, gpt-4-0125-preview, gpt-4-turbo-preview, gpt-4-vision-preview, gpt-4-1106-vision-preview, gpt-4-turbo-2024-04-09, gpt-4-turbo, gpt-4o, gpt-4o-2024-05-13, gpt-4o-2024-08-06, gpt-4o-mini, gpt-4o-mini-2024-07-18, gpt-4-0613, gpt-4-32k-0613, gpt-4-0314, gpt-4-32k-0314, gpt-3.5-turbo, gpt-3.5-turbo-16k, gpt-3.5-turbo-0125, gpt-3.5-turbo-1106, gpt-3.5-turbo-0613, gpt-3.5-turbo-16k-0613, gpt-3.5-turbo-0301, text-davinci-003, text-davinci-002, gpt-3.5-turbo-instruct, text-ada-001, text-babbage-001, text-curie-001, ada, babbage, curie, davinci, gpt-35-turbo-16k, gpt-35-turbo, gpt-35-turbo-0125, gpt-35-turbo-1106, gpt-35-turbo-0613, gpt-35-turbo-16k-0613
Settings.llm = OpenAI(model="gpt-4o", api_key=openai_api_key)

Settings.embed_model = OpenAIEmbedding(model="text-embedding-3-small")

# Create an ingestion pipeline with transformations
pipeline = IngestionPipeline(
    transformations=[
        SentenceSplitter(chunk_size=512, chunk_overlap=128),
        TitleExtractor(),
        QuestionsAnsweredExtractor(questions=5),
        Settings.embed_model,
    ]
)
def print_node_contents(index):
    print("\nNode Contents:")
    for node_id, node in index.docstore.docs.items():
        print(f"Node ID: {node_id}")
        print(f"Content: {node.get_content()[:100]}...")  # Print first 100 characters
        print(f"Metadata: {node.metadata}")
        print("-" * 50)

async def get_ai_response(user_input: str) -> str:
    """
    Integrate with LlamaIndex to generate an AI response.
    """
    index = update_or_create_index()
    query_engine = index.as_query_engine()
    response = await asyncio.to_thread(query_engine.query, user_input)
    return str(response)

def update_or_create_index(documents_dir="documents", force_reindex=False):
    """
    Update existing index or create a new one if it doesn't exist.
    """
    if force_reindex or not os.path.exists("storage"):
        if os.path.exists("storage"):
            import shutil
            shutil.rmtree("storage")
        print("Creating new index...")
        all_documents = SimpleDirectoryReader(documents_dir).load_data()
        nodes = pipeline.run(documents=all_documents)
        index = VectorStoreIndex(nodes)
        print(f"Created new index with {len(nodes)} nodes")
    else:
        print("Loading existing index...")
        storage_context = StorageContext.from_defaults(persist_dir="storage")
        index = load_index_from_storage(storage_context)
        
        # Check for new documents and update
        existing_docs = set(doc.get_content() for doc in index.docstore.docs.values())
        new_documents = [doc for doc in SimpleDirectoryReader(documents_dir).load_data() 
                         if doc.get_content() not in existing_docs]
        
        if new_documents:
            print(f"Found {len(new_documents)} new documents. Updating index...")
            new_nodes = pipeline.run(documents=new_documents)
            index.insert_nodes(new_nodes)
            print(f"Added {len(new_nodes)} new nodes to existing index")
        else:
            print("No new documents found. Index is up to date.")

    # Persist the index
    index.storage_context.persist("storage")
    print("Index persisted to storage")
    
   # print_node_contents(index)
    return index

# Usage example:
# reindex_database()
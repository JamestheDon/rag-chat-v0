from llama_index.core import (
    SimpleDirectoryReader,
    VectorStoreIndex,
    StorageContext,
    load_index_from_storage,
    Settings,
    get_response_synthesizer
)
<<<<<<< HEAD
=======
from llama_index.core.query_engine import RetrieverQueryEngine
>>>>>>> rag-chat-v0-streaming
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core.ingestion import IngestionPipeline
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.extractors import TitleExtractor, QuestionsAnsweredExtractor
import os
from dotenv import load_dotenv
import asyncio
import logging

# Load environment variables
ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')

if ENVIRONMENT == 'development':
    load_dotenv()
# Set up OpenAI API key
openai_api_key = os.getenv('OPENAI_API_KEY', 'default_dev_key')

# Configure LlamaIndex Settings
Settings.llm = OpenAI(model="gpt-4o-mini", api_key=openai_api_key)
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

# Global variable for the index
index = None

<<<<<<< HEAD
async def get_ai_response(user_input: str) -> str:
    """
    Generate an AI response using LlamaIndex.
    """
    global index
    if index is None:
        index = await update_or_create_index()
    query_engine = index.as_query_engine(similarity_top_k=10)
    response = await asyncio.to_thread(query_engine.query, user_input)
    return str(response)
=======
async def get_ai_response(user_message: str):
    logging.info(f"Processing message: {user_message}")
    index = update_or_create_index()
    synth = get_response_synthesizer(streaming=True)
    retriever = index.as_retriever(similarity_top_k=10)  # Add the parameter here
    query_engine = RetrieverQueryEngine(retriever=retriever, response_synthesizer=synth)
    logging.info("Querying the engine...")
    streaming_response = query_engine.query(user_message)
    logging.info("Got streaming response, starting to yield tokens...")
    token_count = 0
    for text in streaming_response.response_gen:
        token_count += 1
        logging.info(f"Yielding token {token_count}: {text}")
        yield text
    logging.info(f"Finished yielding {token_count} tokens")
>>>>>>> rag-chat-v0-streaming

async def update_or_create_index(documents_dir="documents", force_reindex=False):
    """
    Asynchronously update existing index or create a new one if it doesn't exist.
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
        new_documents = [
            doc for doc in SimpleDirectoryReader(documents_dir).load_data() 
            if doc.get_content() not in existing_docs
        ]
        
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
    return index
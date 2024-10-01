from llama_index.core import (
    SimpleDirectoryReader,
    VectorStoreIndex,
    StorageContext,
    load_index_from_storage,
    Settings,
    get_response_synthesizer
)
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.core.ingestion import IngestionPipeline
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.extractors import TitleExtractor, QuestionsAnsweredExtractor
import os
from dotenv import load_dotenv
import asyncio
import logging
import time
import httpx
import random
from llama_index.core.node_parser import NodeParser
from llama_index.core.schema import TextNode, NodeRelationship, RelatedNodeInfo
import uuid
import re
from httpx import AsyncClient

# Load environment variables
ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')

if ENVIRONMENT == 'development':
    load_dotenv()

# Configure logging based on the environment
if ENVIRONMENT == 'production':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
else:  # 'development' or any other environment
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

logging.info(f"Starting application in {ENVIRONMENT} environment")

# Create a persistent AsyncClient
async_client = httpx.AsyncClient(
    timeout=httpx.Timeout(300.0, connect=30.0),
    limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
)

async def initialize_ollama_with_retry(max_retries=5, initial_delay=1):
    for attempt in range(max_retries):
        try:
            llm = Ollama(
                model="llama3.2:1b", 
                base_url="http://localhost:11434",
                request_timeout=60.0
            )
            embed_model = OllamaEmbedding(
                model_name="llama3.2:1b",
                base_url="http://localhost:11434"
            )
            
            # Test the connection
            llm.complete("Test")  # Synchronous call
            embed_model.get_text_embedding("Test")  # Synchronous call
            
            return llm, embed_model
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {str(e)}")
            if attempt < max_retries - 1:
                delay = initial_delay * (2 ** attempt)  # Exponential backoff
                await asyncio.sleep(delay)
            else:
                raise Exception("Failed to initialize Ollama after multiple attempts")

async def initialize_settings():
    try:
        Settings.llm, Settings.embed_model = await initialize_ollama_with_retry()
        print("Ollama initialized successfully")
    except Exception as e:
        print(f"Failed to initialize Ollama: {str(e)}")
        # Handle the error (e.g., fall back to a different model or exit the application)


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

# We'll use the larger dimension to ensure we can accommodate both sizes
# EMBEDDING_DIM = 3072 # phi3.5
EMBEDDING_DIM = 2048 # llama3.2:1b

def ensure_embedding_shape(embedding):
    if isinstance(embedding, list):
        if len(embedding) == EMBEDDING_DIM:
            return embedding
        elif len(embedding) > EMBEDDING_DIM:
            return embedding[:EMBEDDING_DIM]
        else:
            return embedding + [0.0] * (EMBEDDING_DIM - len(embedding))
    else:
        # If the embedding is not a list, return a random embedding
        return [random.random() for _ in range(EMBEDDING_DIM)]

async def process_documents(documents, batch_size=5):
    nodes = []
    parser = SentenceSplitter(chunk_size=512, chunk_overlap=128)
    
    for i in range(0, len(documents), batch_size):
        batch = documents[i:i+batch_size]
        try:
            batch_nodes = parser.get_nodes_from_documents(batch)
            
            for j, node in enumerate(batch_nodes):
                node.node_id = str(uuid.uuid4())
                
                if j > 0:
                    node.relationships[NodeRelationship.PREVIOUS] = RelatedNodeInfo(node_id=batch_nodes[j-1].node_id)
                    batch_nodes[j-1].relationships[NodeRelationship.NEXT] = RelatedNodeInfo(node_id=node.node_id)
                
                try:
                    embedding = await asyncio.to_thread(Settings.embed_model.get_text_embedding, node.text)
                    node.embedding = ensure_embedding_shape(embedding)
                    logging.debug(f"Generated embedding for node {node.node_id} with length {len(node.embedding)}")
                except Exception as e:
                    logging.warning(f"Error generating embedding for node {node.node_id}: {str(e)}")
                    node.embedding = [random.random() for _ in range(EMBEDDING_DIM)]
                    logging.debug(f"Generated random embedding for node {node.node_id} with length {len(node.embedding)}")
            
            nodes.extend(batch_nodes)
            logging.debug(f"Processed batch {i//batch_size + 1}/{len(documents)//batch_size + 1}")
        except Exception as e:
            logging.error(f"Error processing batch: {str(e)}")
            continue
    
    return nodes

async def fix_existing_embeddings(index):
    for node_id, node in index.docstore.docs.items():
        if hasattr(node, 'embedding') and node.embedding is not None:
            node.embedding = ensure_embedding_shape(node.embedding)
    logging.info("Fixed existing embeddings in the index")

async def update_or_create_index(documents_dir="documents", force_reindex=False):
    logging.info(f"Updating or creating index. force_reindex: {force_reindex}")
    
    if not os.path.exists(documents_dir):
        logging.error(f"Documents directory '{documents_dir}' does not exist.")
        return None

    if force_reindex or not os.path.exists("storage"):
        if os.path.exists("storage"):
            import shutil
            shutil.rmtree("storage")
            logging.debug("Existing storage directory removed")
        
        logging.info("Creating new index...")
        try:
            all_documents = await asyncio.to_thread(SimpleDirectoryReader(input_dir=documents_dir).load_data)
            logging.debug(f"Loaded {len(all_documents)} documents from {documents_dir}")
            
            nodes = await process_documents(all_documents)
            logging.debug(f"Created {len(nodes)} nodes from documents")
            
            storage_context = StorageContext.from_defaults()
            index = VectorStoreIndex(nodes, storage_context=storage_context)
            
            os.makedirs("storage", exist_ok=True)
            await asyncio.to_thread(index.storage_context.persist, persist_dir="storage")
            
            logging.info(f"Created new index with {len(nodes)} nodes and persisted to storage")
        except Exception as e:
            logging.error(f"Error creating or persisting index: {str(e)}")
            return None
    else:
        logging.info("Loading existing index...")
        try:
            storage_context = StorageContext.from_defaults(persist_dir="storage")
            index = await asyncio.to_thread(load_index_from_storage, storage_context)
            logging.debug("Existing index loaded from storage")
            
            # Fix existing embeddings
            await fix_existing_embeddings(index)
            
            existing_docs = set(doc.get_content() for doc in index.docstore.docs.values())
            logging.debug(f"Found {len(existing_docs)} existing documents in the index")
            
            new_documents = [
                doc for doc in await asyncio.to_thread(SimpleDirectoryReader(input_dir=documents_dir).load_data)
                if doc.get_content() not in existing_docs
            ]
            
            if new_documents:
                logging.info(f"Found {len(new_documents)} new documents. Updating index...")
                new_nodes = await process_documents(new_documents)
                logging.debug(f"Created {len(new_nodes)} new nodes from new documents")
                
                await asyncio.to_thread(index.insert_nodes, new_nodes)
                await asyncio.to_thread(index.storage_context.persist, persist_dir="storage")
                logging.info(f"Added {len(new_nodes)} new nodes to existing index and persisted changes")
            else:
                logging.info("No new documents found. Index is up to date.")
        except Exception as e:
            logging.error(f"Error loading or updating existing index: {str(e)}")
            return None

    logging.info("Index operation completed")
    return index

# Modify the get_ai_response function to handle potential errors
async def get_ai_response(query: str):
    logging.info(f"Processing message: {query}")
    try:
        # Wait for Ollama connection to be established
        await is_ollama_connected.wait()

        index = await update_or_create_index()
        if index is None:
            yield "Error: Unable to create or update index."
            return

        query_embedding = await asyncio.to_thread(Settings.embed_model.get_text_embedding, query)
        query_embedding = ensure_embedding_shape(query_embedding)

        synth = get_response_synthesizer(streaming=True)
        retriever = index.as_retriever(similarity_top_k=10)
        query_engine = RetrieverQueryEngine.from_args(
            retriever=retriever,
            response_synthesizer=synth,
            streaming=True
        )
        
        streaming_response = await query_engine.aquery(query)
        
        buffer = ""
        async for text in streaming_response.async_response_gen():
            buffer += text
            words = buffer.split()
            if len(words) > 1:
                yield " ".join(words[:-1]) + " "
                buffer = words[-1]
        
        if buffer:
            yield buffer

    except Exception as e:
        logging.error(f"Error in get_ai_response: {str(e)}", exc_info=True)
        yield f"Error: {str(e)}"

async def shutdown():
    await async_client.aclose()

async def ensure_connection():
    while True:
        try:
            # Perform a simple GET request to check connection
            await async_client.get("http://localhost:11434/api/version")
            logging.info("Ollama connection is alive")
        except httpx.RequestError:
            logging.warning("Ollama connection lost, reconnecting...")
            await asyncio.sleep(5)  # Wait before retrying
        await asyncio.sleep(60)  # Check every 60 seconds

# Start the connection check in the background
asyncio.create_task(ensure_connection())

# Global variables
connection_check_task = None
is_ollama_connected = asyncio.Event()

async def check_ollama_connection():
    async with AsyncClient() as client:
        while True:
            try:
                response = await client.get("http://localhost:11434/api/version")
                if response.status_code == 200:
                    is_ollama_connected.set()
                    logging.info("Ollama connection is alive")
                else:
                    is_ollama_connected.clear()
                    logging.warning("Ollama connection lost")
            except Exception as e:
                is_ollama_connected.clear()
                logging.warning(f"Error checking Ollama connection: {str(e)}")
            await asyncio.sleep(60)  # Check every 60 seconds

def start_connection_check():
    global connection_check_task
    if connection_check_task is None or connection_check_task.done():
        connection_check_task = asyncio.create_task(check_ollama_connection())

# Make sure to call this function when your application starts
start_connection_check()
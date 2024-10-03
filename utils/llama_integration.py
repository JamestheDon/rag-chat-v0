from llama_index.core import (
    SimpleDirectoryReader,
    VectorStoreIndex,
    StorageContext,
    load_index_from_storage,
    Settings,
    get_response_synthesizer
)
from llama_index.core.query_engine import RetrieverQueryEngine
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

# Configure logging based on the environment
if ENVIRONMENT == 'production':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
else:  # 'development' or any other environment
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

logging.info(f"Starting application in {ENVIRONMENT} environment")

# Configure LlamaIndex Settings
Settings.llm = OpenAI(model="gpt-4-turbo-preview", api_key=openai_api_key)
Settings.embed_model = OpenAIEmbedding(model="text-embedding-3-small", api_key=openai_api_key)

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

async def get_ai_response(user_message: str):
    logging.info(f"Processing message: {user_message}")
    index = await update_or_create_index()
    
    synth = get_response_synthesizer(streaming=True)
    
    retriever = index.as_retriever(similarity_top_k=10)
    logging.debug(f"Retriever created with similarity_top_k=10")
    
    query_engine = RetrieverQueryEngine(retriever=retriever, response_synthesizer=synth)
    
    streaming_response = query_engine.query(user_message)
    
    buffer = ""
    for text in streaming_response.response_gen:
        buffer += text
        if buffer.endswith((" ", ".", "!", "?", "\n")):
            yield buffer
            buffer = ""
    
    if buffer:
        yield buffer

async def update_or_create_index(documents_dir="documents", force_reindex=False):
    global index
    logging.info(f"Updating or creating index. force_reindex: {force_reindex}")
    
    if force_reindex or not os.path.exists("storage"):
        if os.path.exists("storage"):
            import shutil
            shutil.rmtree("storage")
            logging.debug("Existing storage directory removed")
        logging.info("Creating new index...")
        all_documents = SimpleDirectoryReader(documents_dir).load_data()
        logging.debug(f"Loaded {len(all_documents)} documents from {documents_dir}")
        nodes = pipeline.run(documents=all_documents)
        logging.debug(f"Created {len(nodes)} nodes from documents")
        index = VectorStoreIndex(nodes)
        index.storage_context.persist()  # Add this line
        logging.info(f"Created new index with {len(nodes)} nodes and persisted to storage")
    else:
        logging.info("Loading existing index...")
        storage_context = StorageContext.from_defaults(persist_dir="storage")
        index = load_index_from_storage(storage_context)
        logging.debug("Existing index loaded from storage")
        
        # Check for new documents and update
        existing_docs = set(doc.get_content() for doc in index.docstore.docs.values())
        logging.debug(f"Found {len(existing_docs)} existing documents in the index")
        
        new_documents = [
            doc for doc in SimpleDirectoryReader(documents_dir).load_data() 
            if doc.get_content() not in existing_docs
        ]
        
        if new_documents:
            logging.info(f"Found {len(new_documents)} new documents. Updating index...")
            new_nodes = pipeline.run(documents=new_documents)
            logging.debug(f"Created {len(new_nodes)} new nodes from new documents")
            index.insert_nodes(new_nodes)
            index.storage_context.persist()  # Add this line
            logging.info(f"Added {len(new_nodes)} new nodes to existing index and persisted to storage")
        else:
            logging.info("No new documents found. Index is up to date.")

    return index
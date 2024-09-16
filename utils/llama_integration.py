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
Settings.llm = OpenAI(model="gpt-3.5-turbo", api_key=openai_api_key)
Settings.embed_model = OpenAIEmbedding()

# Create an ingestion pipeline with transformations
pipeline = IngestionPipeline(
    transformations=[
        SentenceSplitter(chunk_size=512, chunk_overlap=128),
        TitleExtractor(),
        QuestionsAnsweredExtractor(questions=3),
        Settings.embed_model,
    ]
)

async def get_ai_response(user_input: str) -> str:
    """
    Integrate with LlamaIndex to generate an AI response.
    """
    # Directory where documents are stored
    documents_dir = "documents"  # Replace with your documents directory

    # Check if the index storage exists; if not, build the index
    if not os.path.exists("storage"):
        # Load documents
        documents = SimpleDirectoryReader(documents_dir).load_data()
        # Process documents through the ingestion pipeline
        nodes = pipeline.run(documents=documents)
        # Build index from processed nodes
        index = VectorStoreIndex(nodes)
        # Persist the index to disk
        index.storage_context.persist("storage")
    else:
        # Load the index from storage
        storage_context = StorageContext.from_defaults(persist_dir="storage")
        index = load_index_from_storage(storage_context)

    # Create a query engine from the index
    query_engine = index.as_query_engine()

    # Query the index with the user input
    response = await asyncio.to_thread(query_engine.query, user_input)

    # Return the response as a string
    return str(response)

# Optionally, you can add a function to update the index with new documents
def update_index(new_documents):
    if not os.path.exists("storage"):
        # Create a new index
        nodes = pipeline.run(documents=new_documents)
        index = VectorStoreIndex.from_documents(new_documents)
    else:
        # Load existing index
        storage_context = StorageContext.from_defaults(persist_dir="storage")
        index = load_index_from_storage(storage_context)
        
        # Process new documents and add to existing index
        new_nodes = pipeline.run(documents=new_documents)
        index.insert_nodes(new_nodes)
    
    # Persist the index
    index.storage_context.persist("storage")
    
    return index
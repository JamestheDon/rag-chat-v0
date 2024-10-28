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
from llama_index.core.memory import ChatMemoryBuffer
import os
from dotenv import load_dotenv
import logging
import json
from llama_index.readers.file import UnstructuredReader
import asyncio
# Load environment variables
ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')

if ENVIRONMENT == 'development':
    load_dotenv()

# Set up OpenAI API key
#openai_api_key = os.getenv('OPENAI_API_KEY', 'default_dev_key')

# Configure logging based on the environment
if ENVIRONMENT == 'production':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
else:  # 'development' or any other environment
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

logging.info(f"Starting application in {ENVIRONMENT} environment")


LLM_TIMEOUT = 900.0  # 15 minutes for LLM requests
EMBEDDING_TIMEOUT = 900.0  # 15 minutes for embedding requests

#Settings.llm = Ollama(request_timeout=LLM_TIMEOUT, model="hf.co/bartowski/Llama-3.1-Nemotron-70B-Instruct-HF-GGUF:IQ1_M", base_url="http://localhost:11434",)
Settings.llm = Ollama(request_timeout=LLM_TIMEOUT, model="llama3.2:1b", base_url="http://localhost:11434",)
Settings.embed_model = OllamaEmbedding(request_timeout=EMBEDDING_TIMEOUT, model_name="nomic-embed-text", base_url="http://localhost:11434")
#Settings.embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")


# Create an ingestion pipeline with transformations
# Question Answering Extractor is using the DEFAULT_QUESTION_GEN_TMPL
'''
pipeline = IngestionPipeline(
    transformations=[
        SentenceSplitter(chunk_size=512, chunk_overlap=128),
        TitleExtractor(),
        QuestionsAnsweredExtractor(questions=5),
      #  ComplianceChecker(issues=5, prompt_template=COMPLIANCE_CHECKER_TMPL),
        Settings.embed_model,
    ]
)
'''
pipeline = IngestionPipeline(
    transformations=[
        SentenceSplitter(chunk_size=512, chunk_overlap=128, separator="|", paragraph_separator="[]"),
       # TitleExtractor(),
       # QuestionsAnsweredExtractor(questions=5),
       
        Settings.embed_model,
    ]
)

# Global variable for the index
index = None

async def get_ai_response(user_message: str):
    logging.info(f"Processing message: {user_message}")

    index = await update_or_create_index()
    
    #synth = get_response_synthesizer(streaming=True)
    
    # similarity_top_k=10 
    #retriever = index.as_retriever()
    memory = ChatMemoryBuffer.from_defaults(token_limit=1500)
    #logging.debug(f"Retriever created with similarity_top_k={similarity_top_k}")
    chat_engine = index.as_chat_engine(chat_mode="context", memory=memory, llm=Settings.llm, verbose=True, system_prompt="You are processing invoices in the LEDES1998B format. \
                                       Each invoice has the following structured data fields. Ensure that the extracted information aligns with each column name below: \
                                       INVOICE_DATE: The date the invoice was issued. \
                                       INVOICE_NUMBER: Unique identifier for the invoice. \
                                       CLIENT_ID: Identifier for the client. \
                                       LAW_FIRM_MATTER_ID: Identifier for the law firm’s matter or project. \
                                       INVOICE_TOTAL: Total amount on the invoice. \
                                       BILLING_START_DATE: Start date of the billing period covered by this invoice. \
                                       BILLING_END_DATE: End date of the billing period covered by this invoice. \
                                       INVOICE_DESCRIPTION: Brief description of the invoice contents or purpose. \
                                       LINE_ITEM_NUMBER: Unique identifier for each line item within the invoice. \
                                       EXP/FEE/INV_ADJ_TYPE: Type of line item adjustment or expense/fee indicator. \
                                       LINE_ITEM_NUMBER_OF_UNITS: Quantity of units for the line item. \
                                       LINE_ITEM_ADJUSTMENT_AMOUNT: Adjustment amount for the line item, if applicable. \
                                       LINE_ITEM_TOTAL: Total amount for the line item. \
                                       LINE_ITEM_DATE: Date associated with this line item’s activity or expense. \
                                       LINE_ITEM_TASK_CODE: Task code associated with this line item. \
                                       LINE_ITEM_EXPENSE_CODE: Expense code for this line item. \
                                       LINE_ITEM_ACTIVITY_CODE: Activity code for this line item. \
                                       TIMEKEEPER_ID: Identifier for the timekeeper or service provider. \
                                       LINE_ITEM_DESCRIPTION: Description of the line item. \
                                       LAW_FIRM_ID: Identifier for the law firm. \
                                       LINE_ITEM_UNIT_COST: Cost per unit of the line item. \
                                       TIMEKEEPER_NAME: Name of the timekeeper or service provider. \
                                       TIMEKEEPER_CLASSIFICATION: Classification of the timekeeper (e.g., partner, associate). \
                                       CLIENT_MATTER_ID: Identifier for the client’s matter or project. \
                                       Ensure consistency with this structure and capture all relevant details as labeled above. ")
    #query_engine = RetrieverQueryEngine(retriever=retriever, response_synthesizer=synth)
    streaming_response = chat_engine.stream_chat(user_message)
    #streaming_response = query_engine.query(user_message)
    
    buffer = ""
    for text in streaming_response.response_gen:
        buffer += text
        lines = buffer.split('\n')
        # Process complete lines
        while len(lines) > 1:
            line = lines.pop(0)
            if line:
                data = {
                    "type": "content",
                    "text": line + '\n'  # Add newline back to preserve formatting
                }
                json_data = json.dumps(data)
                yield f"data: {json_data}\n\n"
        
        buffer = lines[0] if lines else ""
    
    # Yield any remaining content in the buffer
    if buffer:
        data = {
            "type": "content",
            "text": buffer
        }
        json_data = json.dumps(data)
        yield f"data: {json_data}\n\n"
    
    end_data = {
        "type": "end"
    }
    end_json = json.dumps(end_data)
    yield f"data: {end_json}\n\n"

async def update_or_create_index(documents_dir="documents", force_reindex=False):
    global index
    logging.info(f"Updating or creating index. force_reindex: {force_reindex}")
    
    # Check if index exists in memory and storage directory exists
    if index is not None and os.path.exists("storage") and not force_reindex:
        logging.info("Index already exists in memory and storage. Skipping update.")
        return index
    
    if force_reindex or not os.path.exists("storage"):
        if os.path.exists("storage"):
            import shutil
            shutil.rmtree("storage")
            logging.debug("Existing storage directory removed")
        logging.info("Creating new index...")
        all_documents = SimpleDirectoryReader(documents_dir, file_extractor={
            ".pdf": UnstructuredReader(),
            ".html": UnstructuredReader(),
            ".txt": UnstructuredReader(),
        }).load_data(show_progress=True)
        logging.debug(f"Loaded {len(all_documents)} documents from {documents_dir}")
        nodes = pipeline.run(documents=all_documents)
        logging.debug(f"Created {len(nodes)} nodes from documents")
        index = VectorStoreIndex(nodes)
        index.storage_context.persist()  
        logging.info(f"Created new index with {len(nodes)} nodes and persisted to storage")
    else:
        logging.info("Loading existing index...")
        storage_context = StorageContext.from_defaults(persist_dir="storage")
        index = load_index_from_storage(storage_context)
        logging.debug("Existing index loaded from storage")
        
        # Only check for new documents if force_reindex is True
        if force_reindex:
            existing_docs = set(doc.get_content() for doc in index.docstore.docs.values())
            logging.debug(f"Found {len(existing_docs)} existing documents in the index")
            
            new_documents = [
                doc for doc in SimpleDirectoryReader(documents_dir, file_extractor={
                    ".pdf": UnstructuredReader(),
                    ".html": UnstructuredReader(),
                    ".eml": UnstructuredReader(),
                }).load_data(show_progress=True)
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
        else:
            logging.info("Skipping document check. Use force_reindex=True to check for new documents.")

    return index

async def main():
    async for response in get_ai_response("What invoice data do we have?"):
        print(response)

#if __name__ == "__main__":
#    asyncio.run(main())

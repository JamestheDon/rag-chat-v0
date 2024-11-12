from llama_index.core import VectorStoreIndex, Settings, SimpleDirectoryReader
from llama_index.readers.file import UnstructuredReader
from llama_index.llms.llama_cpp import LlamaCPP
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.llms.llama_cpp.llama_utils import (
    messages_to_prompt,
    completion_to_prompt,
)
from llama_index.core.memory import ChatMemoryBuffer
import json
import os
import asyncio
from dotenv import load_dotenv

load_dotenv()
# Get model path
manifest_path = os.getenv('LLAMA_MODEL_PATH')
with open(manifest_path, 'r') as f:
    manifest = json.load(f)
model_digest = manifest['layers'][0]['digest'].replace(":", "-")
model_path = os.path.join(os.getenv('LLAMA_MODEL_BLOB_PATH'), model_digest)

 
# Configure settings with specific chat format
Settings.llm = LlamaCPP(
    model_path=model_path,
    temperature=0.1,
    max_new_tokens=1024,
    context_window=3900,
    messages_to_prompt=messages_to_prompt,
    completion_to_prompt=completion_to_prompt,

)


# Settings.llm = Ollama(
#     model="llama3.2:1b",
#     base_url="http://localhost:11434"
# )

Settings.embed_model = OllamaEmbedding(
    model_name="nomic-embed-text", 
    base_url="http://localhost:11434"
)
data_dir = "documents"

# Move data loading and index creation outside the query function
data = SimpleDirectoryReader(input_dir=data_dir, file_extractor={
    ".txt": UnstructuredReader(),
    ".pdf": UnstructuredReader(),
}).load_data()

# Create index once
index = VectorStoreIndex.from_documents(documents=data, show_progress=True)
memory = ChatMemoryBuffer.from_defaults(token_limit=1500)
SYSTEM_PROMPT = "\
    You are an expert compliance officer that checks that invoices comply with the Bytedance Global Standard document rules: \
        *Invoicing Compliance Standards Extracted Rules* \
    1. **Uniform Task-Based Management System (UTBMS) Codes**: \
       - Use UTBMS codes for all invoice line items. \
       - Sufficiently detailed timekeeper descriptions for tasks performed. \
    2. **Actual Time Recording**: \
       - Record time in increments of 1/10 of an hour. \
       - Only pay for actual, reasonable, and necessary time spent completing a task or series of related tasks. \
    3. **Expense Minimization**: \
       - Minimize type, amount, and disbursement of costs when working on ByteDance matters. \
       - Audit expense billing records for ByteDance rendered services. \
    4. **Expense Invoicing**: \
       - Invoice at actual cost with no mark-up. \
       - Attach all receipts electronically to the submitted invoice. \
    5. **Reimbursable Expenses**: \
       - Expert Witness/Consultant Costs \
       - Express Package Delivery \
       - Messenger and Delivery Charges \
       - Necessary Court Fees \
       - Third-party Costs (with backup documentation) \
       - Travel Expenses (pre-approved by ByteDance) \
    6. **Third-Party Expenses**: \
       - Submit a copy of the third-party’s invoice as backup documentation. \
       - Maintain expense documentation and third-party invoices for a reasonable period. \
    7. **Out-of-Town Travel Expenses**: \
       - Seek approval from ByteDance before incurring charges. \
       - Make every effort to make reservations at least 14 days in advance. \
       - Use lowest fare available, moderately priced hotels, and reasonably priced ground transportation. \
    8. **Invoicing Process and Composition**: \
       - Submit one invoice per each matter for all services performed during a calendar month. \
       - Use Thomson Reuters Legal Tracker for invoice submissions. \
       - Include a LEDES compatible file with time and expense entries coded using UTBMS codes. \
       - Provide clear, comprehensive, and concise narrative descriptions of the nature and subject matter of services rendered. \
    9. **Invoice Line Item Requirements**: \
       - Charge date \
       - Unit(s) \
       - Unit cost \
    10. **Data Management and Security**: \
        - Protect confidential information shared by ByteDance. \
        - Comply with ByteDance’s Security Requirements (Appendix E). \
        - Provide information about information security practices and data privacy practices."
system_prompt="\
    You are an expert compliance officer with extensive knowledge of invoicing regulations. \
    Your task is to thoroughly analyze the provided invoicing compliance standards document and extract all specific rules and guidelines that each line item in an invoice must adhere to. \
    Present the extracted rules in a clear and organized manner for easy reference."

chat_engine = index.as_chat_engine(
    chat_mode="context", 
    memory=memory, 
    llm=Settings.llm, 
    verbose=True, 
    system_prompt=SYSTEM_PROMPT
)

async def get_ai_response(user_message: str):
    # Use the pre-created chat engine
    response = chat_engine.stream_chat(user_message)

    buffer = ""
    for text in response.response_gen:
        buffer += text
        lines = buffer.split('\n')
        # Process complete lines
        while len(lines) > 1:
            line = lines.pop(0)
            if line:
                data = {
                    "type": "content",
                    "text": line + '\n'
                }
                json_data = json.dumps(data)
                yield f"data: {json_data}\n\n"
            
        buffer = lines[0] if lines else ""
    
    # Yield any remaining content
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

# Test with properly formatted messages
#messages = [
#    {"role": "system", "content": "You are a helpful AI assistant."},
#    {"role": "user", "content": "Tell me a joke"}
#]

#response = chat_engine.chat(messages[1]["content"])
#print(response.response)

#response = Settings.llm.complete("Tell me a joke")
#print(response)

async def main():
    while True:
        user_input = input("\nEnter your question (or 'quit' to exit): ")
        if user_input.lower() == 'quit':
            break
            
        async for chunk in get_ai_response(user_input):
            # Parse the JSON data
            data = json.loads(chunk.replace('data: ', ''))
            if data['type'] == 'content':
                print(data['text'], end='', flush=True)
            elif data['type'] == 'end':
                break

if __name__ == "__main__":
    asyncio.run(main())
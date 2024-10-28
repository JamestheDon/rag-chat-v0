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

# Get model path
manifest_path = "/Users/turtle/.ollama/models/manifests/hf.co/bartowski/Llama-3.1-Nemotron-70B-Instruct-HF-GGUF/IQ1_M"
with open(manifest_path, 'r') as f:
    manifest = json.load(f)
model_digest = manifest['layers'][0]['digest'].replace(":", "-")
model_path = os.path.join("/Users/turtle/.ollama/models/blobs", model_digest)

 
# Configure settings with specific chat format
Settings.llm = LlamaCPP(
    model_path=model_path,
    temperature=0.1,
    max_new_tokens=256,
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

data = SimpleDirectoryReader(input_dir=data_dir).load_data()

print('data====>', data)
# Create index and chat engine
index = VectorStoreIndex.from_documents(documents=data, show_progress=True)

memory = ChatMemoryBuffer.from_defaults(token_limit=1500)

chat_engine = index.as_chat_engine(chat_mode="context", memory=memory, llm=Settings.llm, verbose=True, system_prompt="You are a helpful AI assistant that uses jokes to make people laugh.")

#response = chat_engine.chat("What information is in the document?")
response = chat_engine.stream_chat("What invoice data do we have?")

for token in response.response_gen:
    print(token, end="")
# Test with properly formatted messages
#messages = [
#    {"role": "system", "content": "You are a helpful AI assistant."},
#    {"role": "user", "content": "Tell me a joke"}
#]

#response = chat_engine.chat(messages[1]["content"])
#print(response.response)

#response = Settings.llm.complete("Tell me a joke")
#print(response)
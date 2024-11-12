from llama_index.core import VectorStoreIndex, Settings, SimpleDirectoryReader
from llama_index.readers.file import UnstructuredReader
from llama_index.core.ingestion import IngestionPipeline
from llama_index.core.node_parser import SentenceSplitter
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.ollama import OllamaEmbedding
from extractors.compliance_checker import ComplianceChecker, COMPLIANCE_CHECKER_TMPL

LLM_TIMEOUT = 10000.0  # 15 minutes for LLM requests
EMBEDDING_TIMEOUT = 10000.0  # 15 minutes for embedding requests

Settings.llm = Ollama(request_timeout=LLM_TIMEOUT, model="llama3.2:1b", base_url="http://localhost:11434",)
Settings.embed_model = OllamaEmbedding(request_timeout=EMBEDDING_TIMEOUT, model_name="nomic-embed-text", base_url="http://localhost:11434")

pipeline = IngestionPipeline(
    transformations=[
        SentenceSplitter(chunk_size=512, chunk_overlap=128, separator="|", paragraph_separator="[]"),
       # TitleExtractor(),
       # QuestionsAnsweredExtractor(questions=5),
       ComplianceChecker(issues=1, prompt_template=COMPLIANCE_CHECKER_TMPL),
        Settings.embed_model,
    ]
)

data_dir = "documents"

all_documents = SimpleDirectoryReader(input_dir=data_dir, file_extractor={
    ".txt": UnstructuredReader(),
}).load_data()

nodes = pipeline.run(documents=all_documents)


print('nodes====>', nodes[1].text)

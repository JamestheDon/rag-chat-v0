# Build and Run Instructions for `rag-chat-v0` Server

## Prerequisites

- Install Python 3.10 or higher
- Install `pip`
- (Optional) Install Docker Desktop if you plan to use Docker

1. **Clone the Repository**

 - **From Azure DevOps:**

     Make sure you have access to your Azure DevOps repository and have configured your credentials.

     ```bash
     git clone https://dev.azure.com/yourorganization/yourproject/_git/rag-chat-v0
     cd rag-chat-v0
     ```

 - **From GitHub:**

     ```bash
     git clone https://github.com/yourusername/rag-chat-v0.git
     cd rag-chat-v0
     ```

2. **Create a Virtual Environment**

   ```bash
   python -m venv .venv
   ```

3. **Activate the Virtual Environment**

   - On Windows:

     ```bash
     .venv\Scripts\activate
     ```

   - On macOS and Linux:

     ```bash
     source .venv/bin/activate
     ```

4. **Install Dependencies**

   ```bash
   pip install -r requirements.txt
   ```

## Running a local LLM
- Remove any openai api key from .env to protect from fallingback to openai for chat completion and embedding.
5. **Docker Ollama**
   - Using llama3.2:1b as the model
   - Pull the ollama base image
   ```bash
   docker pullollama/ollama
   ```
   - Name and run the container
   ```bash
   docker run -d -v ollama:/root/.ollama -p 11434:11434 --name <container_name> ollama/ollama
   ```
   - Verify there are no images yet in this base image: Should return an empty list.
   ```bash
   docker exec -it <container_name> ollama list
   ```
   - Now get a small language model for the <container_name> (this may take a while):
   ```bash

   docker exec -it <container_name> ollama run llama3.2:1b # this may take a while
   ```
   **Generate a response from the model:**
   ```bash
  curl http://localhost:11434/api/generate -d '{
  "model": "llama3.2",
      "prompt":"Why is the sky blue?"
   }'
   ```
   **Chat with the model:**
   ```bash
   curl http://localhost:11434/api/chat -d '{
  "model": "llama3.2",
  "messages": [
      { "role": "user", "content": "why is the sky blue?" }
    ]
  }'
  ```
  See the [API documentation](https://github.com/ollama/ollama?tab=readme-ov-file) for all endpoints.

  6. **Run the Server**
   
   ```bash
   uvicorn main:app --loop asyncio --reload --host 0.0.0.0 --port 8000
   ```

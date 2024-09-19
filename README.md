# Build and Run Instructions for `rag-chat-v0` Server

## Prerequisites

- Install Python 3.10 or higher
- Install `pip`
- (Optional) Install Docker Desktop if you plan to use Docker

### Install Docker Desktop(Optional)

- **For Windows and macOS:**
  - Download Docker Desktop from the [official website](https://www.docker.com/products/docker-desktop).
  - Run the installer and follow the on-screen instructions.
  - After installation, launch Docker Desktop to finish the setup.


## Setup Without Docker

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

5. **Set Up Environment Variables**

   Create a `.env` file in the project root directory and add necessary environment variables:

   ```ini
   OPENAI_API_KEY=your_openai_api_key
   ```

6. **Run the Server**

   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000
   ```

# Run Docker locally
- Build the docker image
```bash
# docker buildx build --platform linux/amd64,linux/arm64 -t rag-chat-v0-container/rag-chat-v0:latest --load .
./docker-build.sh # This will build the docker image.
```
- Run the docker image
```bash
#docker run -d -p 80:80 --name rag-chat-v0-container rag-chat-v0-container/rag-chat-v0:latest
# Set the OPENAI_API_KEY environment variable
export OPENAI_API_KEY=your_openai_api_key
# Run the docker-start.sh script
./docker-start.sh
```

# Build docker image for Azure
```bash
docker build --platform linux/amd64 -t azcontainerregistryxyz.azurecr.io/rag-chat-v0:latest .
```
- Push the docker image to the azure container registry
```bash
docker push azcontainerregistryxyz.azurecr.io/rag-chat-v0:latest
```

# Curl command to test the docker image
- register a user, save the token and use it to authenticate
```bash
curl -X POST "https://<your-azure-app-name>.azurewebsites.net/auth/register" \\
  -H "Content-Type: application/json" \\
  -d '{\
    "username": "james",\
    "full_name": "New User",\
    "email": "james@james.com",\
    "password": "james"\
  }'
```
# Query the chatbot
```bash
curl -X POST "https://<your-azure-app-name>.azurewebsites.net/chat/sendMessage" \
  -H "Authorization: Bearer <your-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "what are the dates for these invoices?"
  }'
```
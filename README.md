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

5. **Set Up Environment Variables**

   Create a `.env` file in the project root directory and add necessary environment variables:

   ```ini
   OPENAI_API_KEY=your_openai_api_key
   ```

6. **Run the Server**

   ```bash
   uvicorn main:app --loop asyncio --reload 
   ```
# Acceptable OpenAI Model names: 
o1-preview, o1-preview-2024-09-12, o1-mini, o1-mini-2024-09-12, gpt-4, gpt-4-32k, gpt-4-1106-preview, gpt-4-0125-preview, gpt-4-turbo-preview, gpt-4-vision-preview, gpt-4-1106-vision-preview, gpt-4-turbo-2024-04-09, gpt-4-turbo, gpt-4o, gpt-4o-2024-05-13, gpt-4o-2024-08-06, gpt-4o-mini, gpt-4o-mini-2024-07-18, gpt-4-0613, gpt-4-32k-0613, gpt-4-0314, gpt-4-32k-0314, gpt-3.5-turbo, gpt-3.5-turbo-16k, gpt-3.5-turbo-0125, gpt-3.5-turbo-1106, gpt-3.5-turbo-0613, gpt-3.5-turbo-16k-0613, gpt-3.5-turbo-0301, text-davinci-003, text-davinci-002, gpt-3.5-turbo-instruct, text-ada-001, text-babbage-001, text-curie-001, ada, babbage, curie, davinci, gpt-35-turbo-16k, gpt-35-turbo, gpt-35-turbo-0125, gpt-35-turbo-1106, gpt-35-turbo-0613, gpt-35-turbo-16k-0613
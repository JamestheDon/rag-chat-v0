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
   uvicorn main:app --host 0.0.0.0 --port 8000
   ```

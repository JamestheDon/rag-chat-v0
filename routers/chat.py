import logging
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from schemas import chat as chat_schemas
from utils.security import oauth2_scheme
from utils.llama_integration import get_ai_response, async_client

router = APIRouter(prefix="/chat", tags=["chat"])

@router.post("/sendMessage")
async def chat(message: chat_schemas.Message):
    logging.info(f"Received message: {message.content}")
    async def generate():
        try:
            async for token in get_ai_response(message.content):
                logging.info(f"Yielding token: {token}")
                yield f"data: {token}\n\n"
            logging.info("Finished generating response")
            yield "data: [END]\n\n"
        except Exception as e:
            logging.error(f"Error in generate: {str(e)}")
            yield f"data: Error: {str(e)}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")

@router.get("/getResponse", response_model=chat_schemas.Response)
async def get_response(token: str = Depends(oauth2_scheme)):
    try:
        # Use async_client to make a request to Ollama server
        response = await async_client.get("http://localhost:11434/api/version")
        version = response.json().get("version", "Unknown")
        return {"content": f"Ollama server version: {version}"}
    except Exception as e:
        logging.error(f"Error getting Ollama version: {str(e)}")
        raise HTTPException(status_code=500, detail="Error communicating with Ollama server")
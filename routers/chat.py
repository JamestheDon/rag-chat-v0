import json
import logging
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from schemas import chat as chat_schemas
from utils.security import oauth2_scheme
from utils.llama_integration import get_ai_response

router = APIRouter(prefix="/chat", tags=["chat"])

@router.post("/sendMessage")
async def chat(message: chat_schemas.Message):
    logging.info(f"Received message: {message.content}")
    async def generate():
        try:
            async for json_chunk in get_ai_response(message.content):
                yield f"data: {json_chunk}\n\n"
        except Exception as e:
            logging.error(f"Error in generate: {str(e)}")
            error_json = json.dumps({"type": "error", "text": str(e)})
            yield f"data: {error_json}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")

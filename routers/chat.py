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
            async for chunk in get_ai_response(message.content):
                # Optional: Log or process the JSON data
                try:
                    json_data = json.loads(chunk.replace('data:', ''))
                    logging.debug(f"Sending JSON chunk: {json_data}")
                except json.JSONDecodeError:
                    logging.warning(f"Failed to parse JSON from chunk: {chunk}")
                yield chunk
            logging.info("Finished generating response")
        except Exception as e:
            logging.error(f"Error in generate: {str(e)}")
            error_json = json.dumps({"type": "error", "text": str(e)})
            yield f"data:{error_json}\n"

    return StreamingResponse(generate(), media_type="text/event-stream")

@router.get("/getResponse", response_model=chat_schemas.Response)
async def get_response(token: str = Depends(oauth2_scheme)):
    # Retrieve the latest AI response (placeholder)
    return {"content": "Latest AI response will be here."}
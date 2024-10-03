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
                logging.info(f"Yielding chunk: {chunk}")
                yield f"data: {chunk}\n\n"
            logging.info("Finished generating response")
            yield "data: [END]\n\n"
        except Exception as e:
            logging.error(f"Error in generate: {str(e)}")
            yield f"data: Error: {str(e)}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")

@router.get("/getResponse", response_model=chat_schemas.Response)
async def get_response(token: str = Depends(oauth2_scheme)):
    # Retrieve the latest AI response (placeholder)
    return {"content": "Latest AI response will be here."}
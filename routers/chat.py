from fastapi import APIRouter, Depends, HTTPException
from schemas import chat as chat_schemas
from utils.security import oauth2_scheme
from utils.llama_integration import get_ai_response

router = APIRouter(prefix="/chat", tags=["chat"])

@router.post("/sendMessage", response_model=chat_schemas.Response)
async def send_message(
    message: chat_schemas.Message, token: str = Depends(oauth2_scheme)
):
    try:
        # Assuming get_ai_response is an async function
        response_text = await get_ai_response(message.content)
        return {"content": response_text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/getResponse", response_model=chat_schemas.Response)
async def get_response(token: str = Depends(oauth2_scheme)):
    # Retrieve the latest AI response (placeholder)
    return {"content": "Latest AI response will be here."}
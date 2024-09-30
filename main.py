import asyncio
import nest_asyncio
nest_asyncio.apply()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import auth, chat
from database import engine, Base
from utils.llama_integration import initialize_settings, update_or_create_index, shutdown
from contextlib import asynccontextmanager
import logging

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize settings
    await initialize_settings()
    
    # Create tables
    yield
    
    # Update or create index
    index = await update_or_create_index()
    if index is None:
        logging.error("Failed to create or update index")
    else:
        logging.info("Index created or updated successfully")
    
    # Shutdown
    await shutdown()

app = FastAPI(lifespan=lifespan)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React app's address
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(chat.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
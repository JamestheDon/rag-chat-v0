import nest_asyncio
nest_asyncio.apply()

import tracemalloc
tracemalloc.start()

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import auth, chat
from database import engine, Base
#from utils.llama_integration import update_or_create_index
from utils.llama_chat import update_or_create_index
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

import asyncio
import signal
import sys
import uvicorn
import nltk
import os
import sys

# Get the path to the virtual environment
venv_path = sys.prefix

# Set the NLTK data path to be inside the virtual environment
nltk_data_dir = os.path.join(venv_path, 'nltk_data')
os.makedirs(nltk_data_dir, exist_ok=True)

# Set the NLTK data path
nltk.data.path.append(nltk_data_dir)

# Download necessary NLTK data
nltk.download('punkt_tab', download_dir=nltk_data_dir, quiet=False)
nltk.download('averaged_perceptron_tagger_eng', download_dir=nltk_data_dir, quiet=False)
# Configure your async database engine
DATABASE_URL = "sqlite+aiosqlite:///./sql_app.db"  # Example for SQLite
async_engine = create_async_engine(DATABASE_URL, echo=True)

# Create an async session
AsyncSessionLocal = sessionmaker(
    bind=async_engine, expire_on_commit=False, class_=AsyncSession
)

# Define your lifespan function
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup code
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Initialize your index
    await update_or_create_index()

    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    yield  # The application runs during this yield

    # Shutdown code
    print("Cleaning up...")
    await async_engine.dispose()
    # Perform other cleanup tasks here

# Initialize the FastAPI app with the lifespan parameter
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

# Add this function
async def shutdown(loop, signal=None):
    if signal:
        signal_name = signal.name if hasattr(signal, 'name') else str(signal)
        print(f"Received exit signal {signal_name}...")
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    [task.cancel() for task in tasks]
    await asyncio.gather(*tasks, return_exceptions=True)
    loop.stop()

# Modify the signal_handler function
def signal_handler(sig, frame):
    loop = asyncio.get_event_loop()
    loop.create_task(shutdown(loop, signal=sig))

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    try:
        uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
    except KeyboardInterrupt:
        print("Received interrupt signal. Shutting down gracefully...")
        loop.run_until_complete(shutdown(loop))
    finally:
        loop.close()
        sys.exit(0)

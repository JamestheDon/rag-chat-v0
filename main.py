import nest_asyncio
nest_asyncio.apply()

import tracemalloc
tracemalloc.start()

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import auth, chat
from database import engine, Base
from utils.llama_integration import update_or_create_index

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

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
    update_or_create_index()

    yield  # The application runs during this yield

    # Shutdown code
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
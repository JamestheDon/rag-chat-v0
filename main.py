import nest_asyncio
nest_asyncio.apply()

import tracemalloc
tracemalloc.start()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import auth, chat
from database import engine, Base

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React app's address
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create database tables
Base.metadata.create_all(bind=engine)

# Include routers
app.include_router(auth.router)
app.include_router(chat.router)
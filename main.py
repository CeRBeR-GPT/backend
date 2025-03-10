import os
import uvicorn

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from src.users.routers import router as user_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    os.system("alembic upgrade head")

    yield


app = FastAPI(
    title="AI-Chat-Backend",
    lifespan=lifespan
)

origins = [
    "*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/ping")
async def ping_pong():
    return "pong"


app.include_router(user_router)

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0"
    )

import os
import uvicorn

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from contextlib import asynccontextmanager

from starlette.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware

from config_data.config import Config, load_config
from src.users.routers import router as user_router, auth_router

settings: Config = load_config(".env")


@asynccontextmanager
async def lifespan(app: FastAPI):
    os.system("alembic upgrade head")

    yield


middleware = [
    Middleware(SessionMiddleware, secret_key=settings.secrets.SECRET_KEY, same_site="lax", https_only=True)
]

origins = [
    "https://gpt.energy-cerber.ru",
    "http://localhost:3000",
    "https://api-gpt.energy-cerber.ru",
    "http://api-gpt.energy-cerber.ru",
]

app = FastAPI(
    title="AI-Chat-Backend",
    lifespan=lifespan,
    middleware=middleware
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

templates = Jinja2Templates(directory="templates")


@app.get("/ping")
async def ping_pong():
    return "pong"


app.include_router(auth_router)
app.include_router(user_router)


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0"
    )
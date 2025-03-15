import os
import uvicorn

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from starlette.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware

from config_data.config import Config, load_config
from src.users.routers import router as user_router, auth_router
from src.ai_chat.routers import router as chat_router
from src.transactions.routers import router as transaction_router

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


@app.get("/ping")
async def ping_pong():
    return "pong"


app.include_router(auth_router)
app.include_router(user_router)
app.include_router(chat_router)
app.include_router(transaction_router)

templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def get_chat_page(request: Request):
    return templates.TemplateResponse("chat.html", {"request": request})


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0"
    )

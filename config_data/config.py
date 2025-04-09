from dataclasses import dataclass
from pathlib import Path
from environs import Env

BASE_DIR = Path(__file__).parent.parent


@dataclass
class DataBase:
    DB_HOST: str
    DB_PORT: int
    DB_USER: str
    DB_PASS: str
    DB_NAME: str

    @property
    def DATABASE_URL(self):
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"


@dataclass
class RedisConf:
    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_DB: int
    REDIS_PASSWORD: str

    @property
    def REDIS_URL(self):
        return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"


@dataclass
class AuthJWT:
    private_key_path: Path = BASE_DIR / "certs" / "jwt-private.pem"
    public_key_path: Path = BASE_DIR / "certs" / "jwt-public.pem"
    algorithm: str = "RS256"
    access_token_expire_minutes: int = 20
    refresh_token_expire_days: int = 30


@dataclass
class EmailSender:
    EMAIL_NAME: str
    EMAIL_PASS: str
    MIN_CODE: int
    MAX_CODE: int
    ADMIN_EMAIL: str


@dataclass
class VariablesData:
    BACKEND_HOST: str
    VPS_IP: str
    FRONTEND_REDIRECT_URL: str
    FRONTEND_HOST: str
    MODE: str
    BACKEND_DOMAIN: str
    CLIENT_PROTOCOL: str


@dataclass
class Secrets:
    SECRET_KEY: str


@dataclass
class GoogleData:
    CLIENT_ID: str
    CLIENT_SECRET: str


@dataclass
class YandexData:
    CLIENT_ID: str
    CLIENT_SECRET: str


@dataclass
class GitHubData:
    CLIENT_ID: str
    CLIENT_SECRET: str


@dataclass
class YookassaData:
    CLIENT_ID: str
    CLIENT_SECRET: str


@dataclass
class Config:
    database: DataBase
    redis: RedisConf
    authJWT: AuthJWT
    email_sender: EmailSender
    variablesData: VariablesData
    secrets: Secrets
    googleData: GoogleData
    yandexData: YandexData
    githubData: GitHubData
    yookassaData: YookassaData


def load_config(path: str | None = None) -> Config:
    env: Env = Env()
    env.read_env(path)

    return Config(
        database=DataBase(
            DB_HOST=env("DB_HOST"),
            DB_PORT=env("DB_PORT"),
            DB_USER=env("DB_USER"),
            DB_PASS=env("DB_PASS"),
            DB_NAME=env("DB_NAME")
        ),
        redis=RedisConf(
            REDIS_HOST=env("REDIS_HOST"),
            REDIS_PORT=env("REDIS_PORT"),
            REDIS_DB=env("REDIS_DB"),
            REDIS_PASSWORD=env("REDIS_PASSWORD")
        ),
        authJWT=AuthJWT(
            private_key_path=AuthJWT.private_key_path,
            public_key_path=AuthJWT.public_key_path,
            algorithm=AuthJWT.algorithm
        ),
        email_sender=EmailSender(
            EMAIL_NAME=env("EMAIL_NAME"),
            EMAIL_PASS=env("EMAIL_PASS"),
            MIN_CODE=int(env("MIN_CODE")),
            MAX_CODE=int(env("MAX_CODE")),
            ADMIN_EMAIL=env("ADMIN_EMAIL")
        ),
        variablesData=VariablesData(
            BACKEND_HOST=env("BACKEND_HOST"),
            VPS_IP=env("VPS_IP"),
            FRONTEND_REDIRECT_URL=env("FRONTEND_REDIRECT_URL"),
            FRONTEND_HOST=env("FRONTEND_HOST"),
            MODE=env("MODE"),
            BACKEND_DOMAIN=env("BACKEND_DOMAIN"),
            CLIENT_PROTOCOL=env("CLIENT_PROTOCOL")
        ),
        secrets=Secrets(
            SECRET_KEY=env("SECRET_KEY")
        ),
        googleData=GoogleData(
            CLIENT_ID=env("GOOGLE_CLIENT_ID"),
            CLIENT_SECRET=env("GOOGLE_CLIENT_SECRET")
        ),
        yandexData=YandexData(
            CLIENT_ID=env("YANDEX_CLIENT_ID"),
            CLIENT_SECRET=env("YANDEX_CLIENT_SECRET")
        ),
        githubData=GitHubData(
            CLIENT_ID=env("GITHUB_CLIENT_ID"),
            CLIENT_SECRET=env("GITHUB_CLIENT_SECRET")
        ),
        yookassaData=YookassaData(
            CLIENT_ID=env("YOOKASSA_CLIENT_ID"),
            CLIENT_SECRET=env("YOOKASSA_CLIENT_SECRET")
        )
    )

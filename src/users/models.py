import datetime

from enum import Enum
from typing import Dict, Any, List
import uuid

from sqlalchemy import UUID, func, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from config_data.config import load_config, Config
from src.database import Base

settings: Config = load_config(".env")
google_config = settings.googleData
yandex_config = settings.yandexData
github_config = settings.githubData


class OAuthProvider(Enum):
    GOOGLE = {
        "name": "google",
        "scope": "openid email profile",
        "CLIENT_ID": google_config.CLIENT_ID,
        "CLIENT_SECRET": google_config.CLIENT_SECRET,
        "TOKEN_URL": "https://oauth2.googleapis.com/token",
        "AUTH_URL": "https://accounts.google.com/o/oauth2/v2/auth",
        "USER_URL": "https://people.googleapis.com/v1/people/me?personFields=emailAddresses,names"
    }

    YANDEX = {
        "name": "yandex",
        "scope": "login:email login:info",
        "CLIENT_ID": yandex_config.CLIENT_ID,
        "CLIENT_SECRET": yandex_config.CLIENT_SECRET,
        "TOKEN_URL": "https://oauth.yandex.ru/token",
        "AUTH_URL": "https://oauth.yandex.ru/authorize",
        "USER_URL": "https://login.yandex.ru/info"
    }

    GITHUB = {
        "name": "github",
        "scope": "user:email",
        "CLIENT_ID": github_config.CLIENT_ID,
        "CLIENT_SECRET": github_config.CLIENT_SECRET,
        "TOKEN_URL": "https://github.com/login/oauth/access_token",
        "AUTH_URL": "https://github.com/login/oauth/authorize",
        "USER_URL": "https://api.github.com/user"
    }


class Plans(Enum):
    default = "default"
    premium = "premium"
    business = "business"


plan_settings = {
    "default": {
        "max_length": 2000,
        "count_limit": 10,
        "price": 0,
        "description": "Default AI-Chat plan",
        "priority": 1,
    },
    "premium": {
        "max_length": 10000,
        "count_limit": 50,
        "price": 999,
        "description": "Buy premium AI-Chat plan",
        "priority": 2,
    },
    "business": {
        "max_length": 20000,
        "count_limit": 100,
        "price": 2999,
        "description": "Buy business AI-Chat plan",
        "priority": 3
    }
}


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(unique=True)
    plan: Mapped[Plans] = mapped_column(default=Plans.default)
    message_length_limit: Mapped[int] = mapped_column(default=plan_settings["default"]["max_length"])
    message_count_limit: Mapped[int] = mapped_column(default=plan_settings["default"]["count_limit"])
    user_tokens_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    is_admin: Mapped[bool] = mapped_column(default=False)
    is_verified: Mapped[bool] = mapped_column(default=False)
    is_active: Mapped[bool] = mapped_column(default=True)
    password_hash: Mapped[bytes] = mapped_column()
    created_at: Mapped[datetime.datetime] = mapped_column(default=func.now())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "email": self.email,
            "is_admin": self.is_admin,
            "plan": self.plan.value,
            "message_length_limit": self.message_length_limit,
            "message_count_limit": self.message_count_limit,
            "is_verified": self.is_verified,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat(),
        }


class VerifyCode(Base):
    __tablename__ = "verify_codes"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(50), unique=True)
    code: Mapped[int] = mapped_column()

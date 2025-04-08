import uuid
import datetime

from enum import Enum
from typing import Dict, Any

from sqlalchemy import UUID, func, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from config_data.config import load_config, Config
from src.database import Base

settings: Config = load_config(".env")
google_config = settings.googleData
yandex_config = settings.yandexData
github_config = settings.githubData
vk_config = settings.vkData


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

    VK = {
        "name": "vk",
        "scope": "user:email",
        "CLIENT_ID": vk_config.CLIENT_ID,
        "CLIENT_SECRET": vk_config.CLIENT_SECRET,
        "TOKEN_URL": "https://oauth.vk.com/access_token",
        "AUTH_URL": "https://oauth.vk.com/authorize",
        "USER_URL": "https://api.vk.com/method/users.get"
    }


class Plans(Enum):
    default = "default"
    premium = "premium"
    business = "business"


plan_settings = {
    "default": {
        "max_length": 2000,
        "count_limit": 10,
        "chats_limit": 5,
        "price": 0,
        "description": "Default AI-Chat plan",
        "priority": 1,
        "available_providers": [
            "default",
            "deepseek"
        ]
    },
    "premium": {
        "max_length": 10000,
        "count_limit": 50,
        "price": 999,
        "chats_limit": 20,
        "description": "Buy premium AI-Chat plan",
        "priority": 2,
        "available_providers": [
            "default",
            "deepseek",
            "gpt_4o_mini"
        ]
    },
    "business": {
        "max_length": 20000,
        "count_limit": 100,
        "chats_limit": 50,
        "price": 2999,
        "description": "Buy business AI-Chat plan",
        "priority": 3,
        "available_providers": [
            "default",
            "deepseek",
            "gpt_4o_mini",
            "gpt_4o",
            "gpt_4"
        ]
    }
}


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(unique=True)
    plan: Mapped[Plans] = mapped_column(default=Plans.default)
    plan_purchase_date: Mapped[datetime.date] = mapped_column(default=func.now())
    message_length_limit: Mapped[int] = mapped_column(default=plan_settings["default"]["max_length"])
    available_message_count: Mapped[int] = mapped_column(default=plan_settings["default"]["count_limit"])
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
            "plan_purchase_date": self.plan_purchase_date.isoformat(),
            "available_message_count": self.available_message_count,
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


class Feedback(Base):
    __tablename__ = "feedbacks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    user_email: Mapped[str] = mapped_column(ForeignKey("users.email", ondelete="CASCADE"))
    message: Mapped[str] = mapped_column(String(10000), nullable=False)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "name": self.name,
            "user_email": self.user_email,
            "message": self.message
        }

import uuid

from typing import Optional, List
from sqlalchemy import insert, select, delete, update

from config_data.config import Config, load_config
from utils import jwt_settings
from src.database import async_session

from src.users.models import User, VerifyCode
from src.users.schemas import UserCreate

settings: Config = load_config(".env")


class UserRepository:

    async def create_verify_code(self, email: str, code: int) -> None:
        async with async_session() as session:
            stmt = insert(VerifyCode).values(email=email, code=code)
            await session.execute(stmt)
            await session.commit()

    async def update_verify_code(self, email: str, code: int) -> None:
        async with async_session() as session:
            stmt = update(VerifyCode).where(VerifyCode.email == email).values(code=code)
            await session.execute(stmt)
            await session.commit()

    async def get_verify_code_by_email(self, email: str) -> VerifyCode:
        async with async_session() as session:
            query = select(VerifyCode).where(VerifyCode.email == email)
            result = await session.execute(query)
            verify_code = result.scalars().first()

            return verify_code

    async def delete_verify_code_by_id(self, code_id: int) -> None:
        async with async_session() as session:
            stmt = delete(VerifyCode).where(VerifyCode.id == code_id)
            await session.execute(stmt)
            await session.commit()

    async def create_user(self, new_user: UserCreate) -> User:
        password = new_user.password
        user_dc = new_user.dict(exclude={"password"})
        user_dc["password_hash"] = auth_settings.hash_password(password)
        user_dc["id"] = uuid.uuid4()

        async with async_session() as session:
            stmt = insert(User).values(**user_dc)
            await session.execute(stmt)
            await session.commit()

            query = select(User).where(User.id == user_dc["id"])
            result = await session.execute(query)
            user = result.scalars().first()

        return user

    async def edit_password(self, user: User, password: str) -> None:
        async with async_session() as session:
            new_hashed_password = auth_settings.hash_password(password)
            stmt = update(User).where(User.id == user.id).values(password_hash=new_hashed_password)
            await session.execute(stmt)
            await session.commit()

    async def get_user_by_email(self, email: str) -> Optional[User]:
        async with async_session() as session:
            query = select(User).where(User.email == email)
            result = await session.execute(query)
            user = result.scalars().first()
        return user

    async def get_all_users(self) -> List[User]:
        async with async_session() as session:
            query = select(User)
            result = await session.execute(query)
            users = result.scalars().all()

            return users

    async def change_admin_status(self, user: User) -> User:
        async with async_session() as session:
            stmt = update(User).where(User.id == user.id).values(is_admin=False if user.is_admin else True)
            await session.execute(stmt)
            await session.commit()

            user: User = await self.get_user_by_id(user.id)
            return user

    async def change_verified_status(self, user: User) -> User:
        async with async_session() as session:
            stmt = update(User).where(User.id == user.id).values(is_verified=False if user.is_verified else True)
            await session.execute(stmt)
            await session.commit()

            user: User = await self.get_user_by_id(user.id)
            return user

    async def change_active_status(self, user: User) -> User:
        async with async_session() as session:
            stmt = update(User).where(User.id == user.id).values(is_active=False if user.is_active else True)
            await session.execute(stmt)
            await session.commit()

            user: User = await self.get_user_by_id(user.id)
            return user

    async def get_user_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        async with async_session() as session:
            query = select(User).where(User.id == user_id)
            result = await session.execute(query)
            user = result.scalars().first()

        return user

    async def delete_user(self, user: User) -> None:
        async with async_session() as session:
            stmt = delete(User).where(User.id == user.id)
            await session.execute(stmt)
            await session.commit()

    async def set_admin_status(self, user: User) -> User:
        async with async_session() as session:
            stmt = update(User).where(User.id == user.id).values(is_admin=True)
            await session.execute(stmt)
            await session.commit()

            user: User = await self.get_user_by_id(user.id)
            return user

    async def delete_user_by_id(self, user_id: uuid.UUID) -> None:
        async with async_session() as session:
            stmt = delete(User).where(User.id == user_id)
            await session.execute(stmt)
            await session.commit()

    async def remove_user_admin_status(self, user_id: uuid.UUID) -> None:
        async with async_session() as session:
            stmt = update(User).where(User.id == user_id).values(is_admin=False)
            await session.execute(stmt)
            await session.commit()

    async def remove_admin_status_for_all(self) -> None:
        async with async_session() as session:
            stmt = update(User).values(is_admin=False)
            await session.execute(stmt)
            await session.commit()

    async def delete_all_users(self) -> None:
        async with async_session() as session:
            stmt = delete(User)
            await session.execute(stmt)
            await session.commit()

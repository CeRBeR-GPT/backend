import datetime
import uuid

from typing import Optional, List
from sqlalchemy import insert, select, delete, update, column, func, and_

from config_data.config import Config, load_config
from utils import jwt_settings
from src.database import async_session

from src.users.models import User, VerifyCode, Plans, plan_settings, Feedback, CodeType
from src.users.schemas import UserCreate, FeedbackCreate
from src.ai_chat.models import Message

settings: Config = load_config(".env")


class UserRepository:

    async def create_verify_code(self, email: str, code: int, code_type: CodeType) -> None:
        async with async_session() as session:
            stmt = insert(VerifyCode).values(email=email, code=code, type=code_type)
            await session.execute(stmt)
            await session.commit()

    async def get_feedback_by_id(self, feedback_id: uuid.UUID):
        async with async_session() as session:
            query = select(Feedback).where(Feedback.id == feedback_id)
            result = await session.execute(query)
            feedback = result.scalars().first()

            return feedback

    async def create_feedback(self, feedback: FeedbackCreate, email: str) -> Feedback:
        feedback_id = uuid.uuid4()
        async with async_session() as session:
            stmt = insert(Feedback).values(
                id=feedback_id, name=feedback.name, message=feedback.message, user_email=email
            )
            await session.execute(stmt)
            await session.commit()

        return await self.get_feedback_by_id(feedback_id)

    async def update_verify_code(self, email: str, code: int, code_type: CodeType) -> None:
        async with async_session() as session:
            stmt = update(VerifyCode).where(VerifyCode.email == email).values(code=code, type=code_type)
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
        user_dc["password_hash"] = jwt_settings.hash_password(password)
        user_dc["id"] = uuid.uuid4()

        async with async_session() as session:
            stmt = insert(User).values(**user_dc)
            await session.execute(stmt)
            await session.commit()

            query = select(User).where(User.id == user_dc["id"])
            result = await session.execute(query)
            user = result.scalars().first()

        return user

    async def edit_password(self, user: User, password: str) -> User:
        async with async_session() as session:
            stmt = update(User).where(User.id == user.id).values(
                user_tokens_id=uuid.uuid4(),
                password_hash=jwt_settings.hash_password(password)
            )
            await session.execute(stmt)
            await session.commit()

        return await self.get_user_by_email(user.email)

    async def get_user_by_email(self, email: str) -> Optional[User]:
        async with async_session() as session:
            query = select(User).where(User.email == email)
            result = await session.execute(query)
            user = result.scalars().first()
        return user

    async def update_available_messages_count(self, user: User, difference: int) -> User:
        async with async_session() as session:
            stmt = update(User).where(User.id == user.id).values(
                available_message_count=func.greatest(User.available_message_count + difference, 0)
            )
            await session.execute(stmt)
            await session.commit()

        return await self.get_user_by_id(user.id)

    async def reset_available_messages(self) -> None:
        async with async_session() as session:
            stmt = update(User).values(available_message_count=column('message_count_limit'))
            await session.execute(stmt)
            await session.commit()

    async def reset_users_plan_to_default(self) -> None:
        current_date = datetime.date.today()

        default_plan_about = plan_settings[Plans.default.value]
        new_message_length_limit = default_plan_about["max_length"]
        new_message_count_limit = default_plan_about["count_limit"]

        async with async_session() as session:
            stmt = update(User).where(User.plan_expire_date < current_date).values(
                plan=Plans.default,
                plan_purchase_date=datetime.date.today(),
                plan_expire_date=datetime.date.today() + datetime.timedelta(days=28),
                available_message_count=new_message_count_limit,
                message_length_limit=new_message_length_limit,
                message_count_limit=new_message_count_limit
            )
            await session.execute(stmt)
            await session.commit()

    async def delete_old_default_users_messages(self) -> None:
        current_date = datetime.date.today()
        timedelta = datetime.timedelta(days=7)

        default_users_ids = set()
        for user in await self.get_all_default_users():
            default_users_ids.add(user.id)

        async with async_session() as session:
            stmt = delete(Message).where(and_(
                Message.user_id.in_(default_users_ids),
                Message.created_at + timedelta < current_date
            ))
            await session.execute(stmt)
            await session.commit()

    async def update_user_plan(self, user_id: uuid.UUID, plan: Plans, plan_expire_date: datetime.date) -> User:
        new_plan_about = plan_settings[plan.value]
        new_message_length_limit = new_plan_about["max_length"]
        new_message_count_limit = new_plan_about["count_limit"]

        async with async_session() as session:
            stmt = update(User).where(User.id == user_id).values(
                plan=plan,
                plan_purchase_date=datetime.date.today(),
                plan_expire_date=plan_expire_date,
                available_message_count=new_message_count_limit,
                message_length_limit=new_message_length_limit,
                message_count_limit=new_message_count_limit
            )
            await session.execute(stmt)
            await session.commit()

        return await self.get_user_by_id(user_id)

    async def change_verified_status(self, user: User) -> User:
        async with async_session() as session:
            stmt = update(User).where(User.id == user.id).values(is_verified=False if user.is_verified else True)
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

    async def get_all_default_users(self) -> List[User]:
        async with async_session() as session:
            query = select(User).where(User.plan == Plans.default)
            result = await session.execute(query)
            users = result.scalars().all()

            return users

    async def get_all_users(self) -> List[User]:
        async with async_session() as session:
            query = select(User)
            result = await session.execute(query)
            users = result.scalars().all()

            return users

    async def delete_user(self, user: User) -> None:
        async with async_session() as session:
            stmt = delete(User).where(User.id == user.id)
            await session.execute(stmt)
            await session.commit()

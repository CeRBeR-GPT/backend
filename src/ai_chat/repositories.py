import uuid
from typing import List

from sqlalchemy import insert, select, update, delete, and_

from src.ai_chat.models import Chat, Message, MessageBelong
from src.database import async_session


class AIChatRepository:
    async def get_chat_by_id(self, chat_id: uuid.UUID) -> Chat:
        async with async_session() as session:
            query = select(Chat).where(Chat.id == chat_id)
            result = await session.execute(query)
            chat = result.scalars().first()

        return chat

    async def create_new_chat(self, name: str, user_id: uuid.UUID) -> Chat:
        chat_id = uuid.uuid4()
        async with async_session() as session:
            stmt = insert(Chat).values(id=chat_id, name=name, user_id=user_id)
            await session.execute(stmt)
            await session.commit()

        return await self.get_chat_by_id(chat_id)

    async def edit_chat_name(self, new_name: str, chat_id: uuid.UUID) -> Chat:
        async with async_session() as session:
            stmt = update(Chat).where(Chat.id == chat_id).values(name=new_name)
            await session.execute(stmt)
            await session.commit()

        return await self.get_chat_by_id(chat_id)

    async def delete_chat(self, chat_id: uuid.UUID) -> None:
        async with async_session() as session:
            stmt = delete(Chat).where(Chat.id == chat_id)
            await session.execute(stmt)
            await session.commit()

    async def get_message_by_id(self, message_id: uuid.UUID) -> Message:
        async with async_session() as session:
            query = select(Message).where(Message.id == message_id)
            result = await session.execute(query)
            message = result.scalars().first()

        return message

    async def get_all_messages_by_chat(self, chat_id: uuid.UUID) -> List[Message]:
        async with async_session() as session:
            query = select(Message).where(Message.chat_id == chat_id)
            result = await session.execute(query)
            message = result.mapp

        return message

    async def get_user_message_by_id(self, message_id: uuid.UUID) -> Message:
        async with async_session() as session:
            query = select(Message).where(
                and_(Message.id == message_id, Message.message_belong == MessageBelong.user_message)
            )
            result = await session.execute(query)
            message = result.scalars().first()

        return message

    async def get_assistant_message_by_id(self, message_id: uuid.UUID) -> Message:
        async with async_session() as session:
            query = select(Message).where(
                and_(Message.id == message_id, Message.message_belong == MessageBelong.assistant_message)
            )
            result = await session.execute(query)
            message = result.scalars().first()

        return message

    async def create_new_message(
            self, text: str, chat_id: uuid.UUID, user_id: uuid.UUID, message_belong: MessageBelong
    ) -> Message:
        message_id = uuid.uuid4()
        async with async_session() as session:
            stmt = insert(Message).values(
                id=message_id, text=text, chat_id=chat_id, user_id=user_id, message_belong=message_belong
            )
            await session.execute(stmt)
            await session.commit()

        return await self.get_user_message_by_id(message_id)

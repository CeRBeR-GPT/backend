import uuid

from fastapi import WebSocket
from typing import List, Dict

from src.ai_chat.exceptions import ChatNotFoundException, MessageNotFoundException
from src.ai_chat.models import Chat, Message, MessageBelong
from src.ai_chat.repositories import AIChatRepository
from src.users.models import User


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)


class AIChatService:
    repository = AIChatRepository()

    async def get_chat_history(self, user: User, chat_id: uuid.UUID) -> List[Dict]:
        chat = await self.get_chat_by_id(user, chat_id)
        dict_chat = chat.to_dict()
        history_response = []

        for message in dict_chat["messages"]:
            if message["message_belong"] == "user":
                history_response.append({"role": "user", "content": message["text"]})
            else:
                history_response.append({"role": "assistant", "content": message["text"]})

        return history_response

    async def get_chat_by_id(self, user: User, chat_id: uuid.UUID) -> Chat:
        chat = await self.repository.get_chat_by_id(chat_id)

        if chat is None or chat.user_id != user.id:
            raise ChatNotFoundException()

        return chat

    async def create_new_chat(self, user: User, name: str) -> Chat:
        return await self.repository.create_new_chat(name, user.id)

    async def edit_chat_name(self, user: User, chat_id: uuid.UUID, new_name: str) -> Chat:
        chat = await self.get_chat_by_id(user, chat_id)
        return await self.repository.edit_chat_name(new_name, chat.id)

    async def delete_chat(self, user: User, chat_id: uuid.UUID) -> None:
        chat = await self.get_chat_by_id(user, chat_id)
        return await self.repository.delete_chat(chat.id)

    async def get_message_by_id(self, user: User, message_id: uuid.UUID) -> Message:
        message = await self.repository.get_message_by_id(message_id)
        if message is None or message.user_id != user.id:
            raise MessageNotFoundException()

        return message

    async def create_new_message(
            self, user: User, text: str, chat_id: uuid.UUID, message_belong: MessageBelong
    ) -> Message:
        return await self.repository.create_new_message(text, chat_id, user.id, message_belong)

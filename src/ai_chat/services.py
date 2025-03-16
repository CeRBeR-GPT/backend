import uuid

from fastapi import WebSocket, WebSocketDisconnect
from typing import List, Dict

from src.ai_chat.exceptions import ChatNotFoundException, MessageNotFoundException
from src.ai_chat.models import Chat, Message, MessageBelong
from src.ai_chat.repositories import AIChatRepository
from src.users.models import User
from src.users.repositories import UserRepository
from src.users.services import UserService

from utils.ai_settings import generate_ai_response


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    @staticmethod
    async def send_personal_message(message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)


manager = ConnectionManager()


class AIChatService:
    repository = AIChatRepository()

    async def run_websocket_worker(self, websocket: WebSocket, chat_id: uuid.UUID, token: str):
        current_user = await UserService().validate_user(token=token)
        history = await self.get_chat_history(current_user, chat_id)
        await manager.connect(websocket)

        try:
            while True:

                user_message = await websocket.receive_text()
                current_user = await UserRepository().update_available_messages_count(
                    current_user, current_user.available_message_count - 1
                )

                if current_user.available_message_count <= 0:
                    await manager.send_personal_message(
                        "Превышен суточный лимит доступных сообщений! Вы всегда можете обновить план в профиле!",
                        websocket
                    )
                    continue

                await AIChatService().create_new_message(
                    current_user, user_message, chat_id, MessageBelong.user_message
                )
                history.append({"role": "user", "content": user_message})

                print("Generating AI response...")
                ai_response = generate_ai_response(user_message, history)
                print("Successful get response!")
                await AIChatService().create_new_message(
                    current_user, ai_response, chat_id, MessageBelong.assistant_message
                )
                history.append({"role": "assistant", "content": ai_response})
                print("Add response to database")

                await manager.send_personal_message(ai_response, websocket)

        except WebSocketDisconnect:
            manager.disconnect(websocket)
            print(f"Websocket client disconnected")

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

    async def delete_all_chat_messages(self, user: User, chat_id: uuid.UUID) -> Chat:
        chat = await self.get_chat_by_id(user, chat_id)
        return await self.repository.delete_all_chat_messages(chat.id)

    async def get_all_user_chats(self, user: User) -> List[Chat]:
        return await self.repository.get_all_user_chats(user.id)

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

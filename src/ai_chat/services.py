import asyncio
import uuid

from fastapi import WebSocket, WebSocketDisconnect
from typing import List, Dict

from starlette.websockets import WebSocketState

from src.ai_chat.exceptions import ChatNotFoundException, MessageNotFoundException, NotAvailableProviderException
from src.ai_chat.models import Chat, Message, MessageBelong
from src.ai_chat.repositories import AIChatRepository
from src.transactions.schemas import AvailableProviders
from src.users.models import User, plan_settings
from src.users.repositories import UserRepository
from src.users.services import UserService

from utils.ai_settings import generate_ai_response


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        async with self.lock:
            self.active_connections.append(websocket)
            print(f"Client connected: {websocket.client}")

    async def disconnect(self, websocket: WebSocket):
        async with self.lock:
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)
                print(f"Client disconnected: {websocket.client}")

    @staticmethod
    async def send_personal_message(message: str, websocket: WebSocket):
        try:
            if websocket.client_state == WebSocketState.CONNECTED:
                await websocket.send_text(message)
            else:
                print(
                    f"! Attempted to send message to disconnected client: {websocket.client}")

        except WebSocketDisconnect:
            print(f"Client disconnected during send: {websocket.client}")


manager = ConnectionManager()


class AIChatService:
    repository = AIChatRepository()

    async def run_websocket_worker(
            self, websocket: WebSocket, chat_id: uuid.UUID, token: str,
            provider: AvailableProviders = AvailableProviders.DEFAULT
    ):
        current_user = await UserService().validate_user(token=token)
        history = await self.get_chat_history(current_user, chat_id)
        await manager.connect(websocket)

        try:
            while True:
                user_message = await websocket.receive_text()
                print(
                    f"Received message from {websocket.client}: {user_message}")

                if current_user.available_message_count <= 0:
                    await manager.send_personal_message(
                        "Превышен суточный лимит доступных сообщений! Вы всегда можете обновить план в профиле!",
                        websocket
                    )
                    continue

                if provider.value not in plan_settings[current_user.plan.value]["available_providers"]:
                    raise NotAvailableProviderException()

                if len(user_message) > current_user.message_length_limit:
                    await manager.send_personal_message(
                        f"Длина данного сообщения превышает лимит символов "
                        f"({current_user.message_length_limit}) по Вашему тарифу",
                        websocket
                    )
                    continue

                current_user = await UserRepository().update_available_messages_count(current_user, -1)

                await AIChatService().create_new_message(
                    current_user, user_message, chat_id, MessageBelong.user_message
                )

                try:
                    ai_response = await asyncio.to_thread(generate_ai_response, user_message, history, provider.value)
                except RuntimeError:
                    await UserRepository().update_available_messages_count(current_user, 1)
                    await manager.send_personal_message(
                        "Модель перегружена! Попробуйте повторить запрос (с Вашего счёта он не был списан)",
                        websocket
                    )
                    continue

                await AIChatService().create_new_message(
                    current_user, ai_response, chat_id, MessageBelong.assistant_message
                )
                await manager.send_personal_message(ai_response, websocket)

        except WebSocketDisconnect:
            print(f"Websocket client disconnected: {websocket.client}")
            await manager.disconnect(websocket)

        except NotAvailableProviderException:
            print("Provider type error!")
            await manager.disconnect(websocket)
            raise NotAvailableProviderException()

        except Exception as e:
            print(f"!!! Error in websocket handler: {e}")
            await manager.send_personal_message(
                "На сервере произошла ошибка! Попробуйте повторить запрос (с Вашего счёта он не был списан)",
                websocket
            )
            await manager.disconnect(websocket)

    async def get_chat_history(self, user: User, chat_id: uuid.UUID) -> List[Dict]:
        chat = await self.get_chat_by_id(user, chat_id)
        dict_chat = chat.to_dict()
        history_response = []

        for message in dict_chat["messages"]:
            if message["message_belong"] == "user":
                history_response.append(
                    {"role": "user", "content": message["text"]})
            else:
                history_response.append(
                    {"role": "assistant", "content": message["text"]})

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

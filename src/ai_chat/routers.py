import uuid

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from typing import Annotated

from src.ai_chat.models import MessageBelong
from src.ai_chat.schemas import AIChatResponse
from src.ai_chat.services import ConnectionManager, AIChatService

from src.users.models import User
from src.users.schemas import SuccessfulResponse
from src.users.services import UserService

from utils.ai_settings import generate_ai_response

router = APIRouter(tags=["chat"], prefix="/chat")
manager = ConnectionManager()


@router.post("/new", response_model=AIChatResponse)
async def create_new_chat(
        current_user: Annotated[User, Depends(UserService().get_current_user)],
        name: str
) -> AIChatResponse:
    new_chat = await AIChatService().create_new_chat(current_user, name)
    return AIChatResponse(**new_chat.to_dict())


@router.get("/{chat_id}", response_model=AIChatResponse)
async def get_chat_by_id(
        current_user: Annotated[User, Depends(UserService().get_current_user)],
        chat_id: uuid.UUID,
) -> AIChatResponse:
    chat = await AIChatService().get_chat_by_id(current_user, chat_id)
    for message in chat.messages:
        message = message.to_dict()
        print(message)
    return AIChatResponse(**chat.to_dict())


@router.put("/{chat_id}", response_model=AIChatResponse)
async def edit_chat_name(
        current_user: Annotated[User, Depends(UserService().get_current_user)],
        chat_id: uuid.UUID,
        new_name: str
) -> AIChatResponse:
    updated_chat = await AIChatService().edit_chat_name(current_user, chat_id, new_name)
    return AIChatResponse(**updated_chat.to_dict())


@router.delete("/{chat_id}", response_model=SuccessfulResponse)
async def delete_chat(
        current_user: Annotated[User, Depends(UserService().get_current_user)],
        chat_id: uuid.UUID
) -> SuccessfulResponse:
    await AIChatService().delete_chat(current_user, chat_id)
    return SuccessfulResponse()


@router.websocket("/ws/{chat_id}")
async def websocket_endpoint(
        current_user: Annotated[User, Depends(UserService().get_current_user)],
        websocket: WebSocket,
        chat_id: uuid.UUID
):
    await manager.connect(websocket)
    history = await AIChatService().get_chat_history(current_user, chat_id)

    try:
        while True:
            user_message = await websocket.receive_text()

            await AIChatService().create_new_message(
                current_user, user_message, chat_id, MessageBelong.user_message
            )
            history.append({"role": "user", "content": user_message})

            ai_response = generate_ai_response(user_message, history)
            await AIChatService().create_new_message(
                current_user, ai_response, chat_id, MessageBelong.assistant_message
            )
            history.append({"role": "assistant", "content": ai_response})
            await manager.send_personal_message(ai_response, websocket)

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        print(f"Client disconnected")

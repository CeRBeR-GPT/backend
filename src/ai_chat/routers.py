import uuid

from fastapi import APIRouter, Depends, WebSocket
from typing import Annotated, List

from src.transactions.schemas import AvailableProviders
from src.ai_chat.schemas import AIChatResponse
from src.ai_chat.services import AIChatService

from src.users.models import User
from src.users.schemas import SuccessfulResponse
from src.users.services import UserService

router = APIRouter(tags=["chat"], prefix="/chat")


@router.post("/new", response_model=AIChatResponse)
async def create_new_chat(
        current_user: Annotated[User, Depends(UserService().get_current_user)],
        name: str
) -> AIChatResponse:
    new_chat = await AIChatService().create_new_chat(current_user, name)
    return AIChatResponse(**new_chat.to_dict())


@router.get("/all", response_model=List[AIChatResponse])
async def get_all_user_chats(
        current_user: Annotated[User, Depends(UserService().get_current_user)]
) -> List[AIChatResponse]:
    chats = await AIChatService().get_all_user_chats(current_user)
    return list(map(lambda x: AIChatResponse(**x.to_dict()), chats))


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


@router.delete("/{chat_id}/clear", response_model=AIChatResponse)
async def clear_chat(
        current_user: Annotated[User, Depends(UserService().get_current_user)],
        chat_id: uuid.UUID,
) -> AIChatResponse:
    updated_chat = await AIChatService().delete_all_chat_messages(current_user, chat_id)
    return AIChatResponse(**updated_chat.to_dict())


@router.delete("/{chat_id}", response_model=SuccessfulResponse)
async def delete_chat(
        current_user: Annotated[User, Depends(UserService().get_current_user)],
        chat_id: uuid.UUID
) -> SuccessfulResponse:
    await AIChatService().delete_chat(current_user, chat_id)
    return SuccessfulResponse()


@router.websocket("/ws/{chat_id}")
async def websocket_worker(
        websocket: WebSocket,
        chat_id: uuid.UUID,
        token: str,
        # provider: AvailableProviders

):
    await AIChatService().run_websocket_worker(websocket, chat_id, token, AvailableProviders.DEFAULT)

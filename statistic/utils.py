import uuid

from statistic.schemas import UserDocument


async def get_or_create_user(user_id: uuid.UUID) -> UserDocument:
    user = await UserDocument.find_one(UserDocument.user_id == user_id)
    if not user:
        user = UserDocument(user_id=user_id)
        await user.save()

    return user

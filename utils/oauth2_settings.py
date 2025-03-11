import httpx
from typing import Dict

from src.users.exceptions import FetchingGitHubUserException, OAuthTokenNotFoundException
from src.users.models import OAuthProvider


async def get_google_oauth_email(data: Dict) -> str:
    try:
        async with httpx.AsyncClient() as client:
            token_response = await client.post(OAuthProvider.GOOGLE.value["TOKEN_URL"], data=data)
            token_response.raise_for_status()
            tokens = token_response.json()
    except httpx.HTTPStatusError as e:
        raise OAuthTokenNotFoundException("Google")

    async with httpx.AsyncClient() as client:
        people_response = await client.get(
            OAuthProvider.GOOGLE.value["USER_URL"],
            headers={"Authorization": f"Bearer {tokens.get('access_token', '')}"}
        )
        people_response.raise_for_status()
        user_info = people_response.json()

    return user_info["emailAddresses"][0]["value"]


async def get_yandex_oauth_email(data: Dict) -> str:
    try:
        async with httpx.AsyncClient() as client:
            token_response = await client.post(OAuthProvider.YANDEX.value["TOKEN_URL"], data=data)
            token_response.raise_for_status()
            tokens = token_response.json()
    except httpx.HTTPStatusError as e:
        raise OAuthTokenNotFoundException("Yandex")

    async with httpx.AsyncClient() as client:
        user_info_response = await client.get(
            OAuthProvider.YANDEX.value["USER_URL"],
            headers={"Authorization": f"OAuth {tokens.get('access_token', '')}"},
        )
        user_info_response.raise_for_status()
        user_info = user_info_response.json()

    return user_info["default_email"]


async def get_github_oauth_email(data: Dict) -> str:
    headers = {
        "Accept": "application/json",
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(OAuthProvider.GITHUB.value["TOKEN_URL"], params=data, headers=headers)
            response.raise_for_status()
            tokens = response.json()
        except httpx.HTTPStatusError as e:
            raise OAuthTokenNotFoundException("GitHub")

    headers = {
        "Authorization": f"Bearer {tokens.get('access_token', '')}",
        "Accept": "application/json",
    }
    async with httpx.AsyncClient() as client:
        try:
            user_response = await client.get(OAuthProvider.GITHUB.value["USER_URL"], headers=headers)
            user_response.raise_for_status()

            email_response = await client.get("https://api.github.com/user/emails", headers=headers)
            email_response.raise_for_status()
            emails = email_response.json()

        except httpx.HTTPStatusError as e:
            raise FetchingGitHubUserException()

    primary_email = next((email["email"] for email in emails if email["primary"]), None)

    return primary_email

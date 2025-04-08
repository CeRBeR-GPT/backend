import httpx
import logging
from typing import Dict

from src.users.exceptions import FetchingGitHubUserException, OAuthTokenNotFoundException
from src.users.models import OAuthProvider

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def get_google_oauth_email(data: Dict) -> str:
    logger.info("Start get email from github...")

    try:
        async with httpx.AsyncClient() as client:
            token_response = await client.post(OAuthProvider.GOOGLE.value["TOKEN_URL"], data=data)
            token_response.raise_for_status()
            tokens = token_response.json()
    except httpx.HTTPStatusError as e:
        logger.error("Error: Cannot get OAuth token!")
        raise OAuthTokenNotFoundException("Google")

    logger.info("Successful get OAuth token")

    async with httpx.AsyncClient() as client:
        people_response = await client.get(
            OAuthProvider.GOOGLE.value["USER_URL"],
            headers={"Authorization": f"Bearer {tokens.get('access_token', '')}"}
        )
        people_response.raise_for_status()
        user_info = people_response.json()

    logger.info(f'Successful get OAuth user data. Email: {user_info["emailAddresses"][0]["value"]}')

    return user_info["emailAddresses"][0]["value"]


async def get_yandex_oauth_email(data: Dict) -> str:
    logger.info("Start get email from yandex...")

    try:
        async with httpx.AsyncClient() as client:
            token_response = await client.post(OAuthProvider.YANDEX.value["TOKEN_URL"], data=data)
            token_response.raise_for_status()
            tokens = token_response.json()
    except httpx.HTTPStatusError as e:
        logger.error("Error: Cannot get OAuth token!")
        raise OAuthTokenNotFoundException("Yandex")

    logger.info("Successful get OAuth token")

    async with httpx.AsyncClient() as client:
        user_info_response = await client.get(
            OAuthProvider.YANDEX.value["USER_URL"],
            headers={"Authorization": f"OAuth {tokens.get('access_token', '')}"},
        )
        user_info_response.raise_for_status()
        user_info = user_info_response.json()

    logger.info(f'Successful get OAuth user data. Email: {user_info["default_email"]}')

    return user_info["default_email"]


async def get_github_oauth_email(data: Dict) -> str:
    logger.info("Start get email from google...")

    headers = {
        "Accept": "application/json",
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(OAuthProvider.GITHUB.value["TOKEN_URL"], params=data, headers=headers)
            response.raise_for_status()
            tokens = response.json()
    except httpx.HTTPStatusError as e:
        logger.error("Error: Cannot get OAuth token!")
        raise OAuthTokenNotFoundException("GitHub")

    logger.info("Successful get OAuth token")

    headers = {
        "Authorization": f"Bearer {tokens.get('access_token', '')}",
        "Accept": "application/json",
    }

    try:
        async with httpx.AsyncClient() as client:
            user_response = await client.get(OAuthProvider.GITHUB.value["USER_URL"], headers=headers)
            user_response.raise_for_status()

            email_response = await client.get("https://api.github.com/user/emails", headers=headers)
            email_response.raise_for_status()
            emails = email_response.json()
    except httpx.HTTPStatusError as e:
        logging.error("Error: Can't fetching user data from github")
        raise FetchingGitHubUserException()

    primary_email = next((email["email"] for email in emails if email["primary"]), None)

    logger.info(f'Successful get OAuth user data. Email: {primary_email}')

    return primary_email

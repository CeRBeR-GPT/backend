import g4f
from typing import List, Dict

g4f.debug.logging = False

from config_data.config import Config, load_config

settings: Config = load_config()


def generate_ai_response(user_message: str, history: List[Dict]) -> str:
    try:
        history.append({"role": "user", "content": user_message})

        response = g4f.ChatCompletion.create(
            model=g4f.models.default,
            messages=history,
        )

        attempts = 0
        while settings.variablesData.VPS_IP in response and attempts <= 3:
            response = g4f.ChatCompletion.create(
                model=g4f.models.default,
                messages=history,
            )
            attempts += 1

        if settings.variablesData.VPS_IP in response:
            raise RuntimeError("Ошибка генерации ответа!")

        history.append({"role": "assistant", "content": response})

        return response

    except Exception:
        raise RuntimeError("Ошибка генерации ответа!")


if __name__ == "__main__":
    messages = []

    while True:
        query = input("Введите ваше сообщение: ")
        print(generate_ai_response(query, messages))
        print()
        print(messages)
        print()

import g4f

from typing import List, Dict
from config_data.config import Config, load_config

g4f.debug.logging = False
settings: Config = load_config()

ai_models = {
    "default": g4f.models.default,
    "deepseek": g4f.models.deepseek_r1,
    "gpt_4o_mini": g4f.models.gpt_4o_mini,
    "gpt_4o": g4f.models.gpt_4o,
    "gpt_4": g4f.models.gpt_4
}


def generate_ai_response(user_message: str, history: List[Dict], provider_name: str) -> str:
    try:
        history.append({"role": "user", "content": user_message})

        provider = ai_models.get(provider_name, g4f.models.default)
        print(provider_name, "AI using default provider")

        response = g4f.ChatCompletion.create(
            model=provider,
            messages=history,
        )

        attempts = 0
        while settings.variablesData.VPS_IP in response and attempts < 5:
            response = g4f.ChatCompletion.create(
                model=provider,
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
        print(generate_ai_response(query, messages, "deepseek"))
        print()
        print(messages)
        print()

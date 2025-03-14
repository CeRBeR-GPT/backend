import g4f
from typing import List, Dict

g4f.debug.logging = False  # Включите отладочное логирование G4F (для более подробной информации об ошибках)


def generate_response(user_message: str, history: List[Dict]) -> str:
    try:
        history.append({"role": "user", "content": user_message})

        response = g4f.ChatCompletion.create(
            model=g4f.models.default,
            messages=history,
        )

        history.append({"role": "assistant", "content": response})

        return response

    except Exception as e:
        return f"Произошла ошибка при генерации ответа. Пожалуйста, попробуйте позже.  Детали: {e}"


if __name__ == "__main__":
    messages = []

    while True:
        query = input("Введите ваше сообщение: ")
        print(generate_response(query, messages))
        print()
        print(messages)
        print()

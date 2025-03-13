import g4f
import traceback

# Настройка логирования

# Настройка G4F (можно добавить параметры прокси, если нужно)
g4f.debug.logging = False  # Включите отладочное логирование G4F (для более подробной информации об ошибках)

# Словарь для хранения истории диалогов (ключ - идентификатор пользователя/сессии)
conversation_history = {}


def generate_response(user_id: str, user_message: str) -> str:
    """
    Генерирует ответ на сообщение пользователя, используя G4F.

    Args:
        user_id: Уникальный идентификатор пользователя (например, ID сессии).
        user_message: Сообщение пользователя.

    Returns:
        Ответ от AI в виде строки, или сообщение об ошибке.
    """
    try:
        # 1. Получение истории диалога для пользователя
        history = conversation_history.get(user_id, [])

        # 2. Добавление нового сообщения пользователя в историю
        history.append({"role": "user", "content": user_message})

        # 3. Создание запроса к G4F (используем history)
        response = g4f.ChatCompletion.create(
            model=g4f.models.default,  # Используйте g4f.models.gpt_4, если у вас есть доступ
            messages=history,
        )

        # 4. Получение ответа от AI
        ai_response = response

        # 5. Добавление ответа AI в историю (обязательно!)
        history.append({"role": "assistant", "content": ai_response})

        # 6. Обновление истории диалога для пользователя
        conversation_history[user_id] = history

        return ai_response

    except Exception as e:
        return f"Произошла ошибка при генерации ответа. Пожалуйста, попробуйте позже.  Детали: {e}"


def clear_conversation_history(user_id: str):
    """
    Очищает историю диалога для указанного пользователя.

    Args:
        user_id: Уникальный идентификатор пользователя.
    """
    if user_id in conversation_history:
        del conversation_history[user_id]


def get_conversation_history(user_id: str) -> list:
    """
    Возвращает историю диалога для указанного пользователя.

    Args:
        user_id: Уникальный идентификатор пользователя.

    Returns:
        Список сообщений в истории, или пустой список, если история не найдена.
    """
    return conversation_history.get(user_id, [])


def main():
    """
    Основная функция для тестирования.
    """
    user1_id = "user123"  # Пример ID пользователя
    user2_id = "another_user"

    # Пример диалога для user1
    print("--- Начало диалога для user1 ---")
    response1_1 = generate_response(user1_id, "Привет, меня зовут Игорь!")
    print(f"User: Привет, меня зовут Игорь!")
    print(f"AI: {response1_1}")

    response1_2 = generate_response(user1_id, "Помнишь, как меня зовут?")
    print(f"User: Помнишь, как меня зовут?")
    print(f"AI: {response1_2}")

    # # Пример диалога для user2
    # print("\n--- Начало диалога для user2 ---")
    # response2_1 = generate_response(user2_id, "Здравствуй, я new user!")
    # print(f"User: Здравствуй, я new user!")
    # print(f"AI: {response2_1}")
    #
    # response2_2 = generate_response(user2_id, "Что такое FastAPI?")
    # print(f"User: Что такое FastAPI?")
    # print(f"AI: {response2_2}")
    #
    # # Продолжение диалога для user1
    # print("\n--- Продолжение диалога для user1 ---")
    # response1_3 = generate_response(user1_id, "А что ты знаешь о FastAPI?")
    # print(f"User: А что ты знаешь о FastAPI?")
    # print(f"AI: {response1_3}")
    #
    # # Проверка истории диалогов
    # print("\n--- Проверка истории диалогов ---")
    # print(f"История для user1: {get_conversation_history(user1_id)}")
    # print(f"История для user2: {get_conversation_history(user2_id)}")
    #
    # # Очистка истории для user1
    # clear_conversation_history(user1_id)
    # print("\n--- После очистки истории для user1 ---")
    # print(f"История для user1: {get_conversation_history(user1_id)}")


if __name__ == "__main__":
    main()

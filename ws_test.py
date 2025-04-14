import asyncio
import websockets


async def chat_client():
    token = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoiYWNjZXNzIiwic3ViIjoic3RyaW5nIiwidXVpZCI6ImE5YmY1NDYyLWMwYTEtNDdmYy05OTgyLTZlZDc4MGIxNjgzNSIsImV4cCI6MTc0NDYyMjYwOSwiaWF0IjoxNzQ0NjIxNDA5fQ.A08WS3x681r9NCAD3WC7-cNP_EMKnDS-eQB88Wt1zh2TvjX5XJKleg3puyRYuRVmDbXEPLiThQnNBQskp5DpZFWgQ4kt1nYnqvPgyvimRJELkOr1HBketKBErqSeq_lo_f-aaQSoVUpFXPegs7Nv25cD-u1-1s_09ud9q9qqNRrXIRcoi3cBXhsph_22gM5e9lbTmZFpeP-lwznD_-yHZOVbp-uvm9G0Zx8PpEsfQ-DS36RkVkP6zs897Na8m1FK66F87G9MuR_Bd5JMAesSXvXMSa8jyaGusSz7FQJFZ95j6WC54dslQhz54tNZXYbuJcDAzZ80Y7VlRi_xy1t_FA"
    chat_id = "80c79797-d145-4c02-92e8-35b64d5e3eb3"
    uri = f"wss://localhost:8000/chat/ws/{chat_id}?token={token}&provider=default"

    async with websockets.connect(uri) as websocket:
        print("Connected to WebSocket server. Type 'exit' to quit.")

        while True:
            # Ввод сообщения с клавиатуры
            user_message = input("You: ")
            if user_message.lower() == "exit":
                print("Exiting chat...")
                break

            # Отправка сообщения на сервер
            await websocket.send(user_message)

            # Получение ответа от ассистента
            ai_response = await websocket.recv()
            print(f"Assistant: {ai_response}")


# Запуск клиента
async def main():
    await chat_client()


if __name__ == "__main__":
    asyncio.run(main())

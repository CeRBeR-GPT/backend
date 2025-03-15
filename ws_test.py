import asyncio
import websockets


async def chat_client():
    uri = "ws://localhost:8000/chat/ws/80c79797-d145-4c02-92e8-35b64d5e3eb3"
    headers = {
        "Authorization": f"Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoiYWNjZXNzIiwic3ViIjoic3RyaW5nIiwidXVpZCI6ImE5YmY1NDYyLWMwYTEtNDdmYy05OTgyLTZlZDc4MGIxNjgzNSIsImV4cCI6MTc0MjExNjE3OSwiaWF0IjoxNzQyMDI5Nzc5fQ.HeqqQ7W61Wr47aTxKz35h4El1VVGrpIzh67JB-wUcwjDE2nOuRVn3WwfAdGJbS_Mr4IuY7-lnTR0ls6_Tr6mSgHP2MRDh10dRKA4b0e6qC83U5DU5e7-aVNcPkqHWP7IndCfGXW2EYcVJNOp_ENEkz3ql7Ov2XLJwAppzOjjhblUYQGAp_Az4p5aERicuiiriB6VwHoyvbDQeHrUn5lEZDVZ4mO3uhc-YWJoHXfTMmFtDoarUpl-PzgvrsHr1k_6sQ01EMswAVYdDRcl2IMp5ds6lVHjufWnhTiXSjBbwp-HZ-UPtdV8gKC4c2PFMw3yLQ1tIemmA8ndHpRyqxyc5g"
    }

    async with websockets.connect(uri, extra_headers=headers) as websocket:
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

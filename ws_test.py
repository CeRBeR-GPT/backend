import asyncio
import websockets


async def chat_client():
    token = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoiYWNjZXNzIiwic3ViIjoic3RyaW5nIiwidXVpZCI6ImE5YmY1NDYyLWMwYTEtNDdmYy05OTgyLTZlZDc4MGIxNjgzNSIsImV4cCI6MTc0MjEyMTE0NSwiaWF0IjoxNzQyMDM0NzQ1fQ.QNQTatBvWXD03pkxnConcWubbiU1x93hidIlUc2zPisCxQRN20J4L7vLDQ_VYTiT588oC3h69X0OqzpN8X-Jj0We9ngbg1SAeypyLi6S2SdNBlnxqAzpVFC55XmC0-nubjjqUYiJwFkye-vDeASt-xOQWJvArvQm27PQZLHXNCFA5J-n3-cd_OYH4Xqm3I4hnGO4jdXJjx-RyA9UbD1r8dc772TUD9QAZ-n1UhXcI28gh_IMsc2s_sIr6B_XrS6URBz1eZR-KqxuA57TcDxREmYNDDxD0YxU8Arkqrl0-uqTdcUVreZ_UCODFv22nhCZYT26Ct3c4sAhiEj8dy0KVw"
    chat_id = "80c79797-d145-4c02-92e8-35b64d5e3eb3"
    uri = f"ws://localhost:8000/chat/ws/{chat_id}?token={token}"

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

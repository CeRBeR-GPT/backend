from fastapi import HTTPException, status


class ChatNotFoundException(HTTPException):
    status_code = status.HTTP_404_NOT_FOUND
    detail = "Chat not found"

    def __init__(self):
        super().__init__(status_code=self.status_code, detail=self.detail)


class MessageNotFoundException(HTTPException):
    status_code = status.HTTP_404_NOT_FOUND
    detail = "Message not found"

    def __init__(self):
        super().__init__(status_code=self.status_code, detail=self.detail)

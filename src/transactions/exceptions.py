from fastapi import HTTPException, status


class TransactionNotFoundException(HTTPException):
    status_code = status.HTTP_404_NOT_FOUND
    detail = "Transaction not found"

    def __init__(self):
        super().__init__(status_code=self.status_code, detail=self.detail)


class FreePlanException(HTTPException):
    status_code = status.HTTP_400_BAD_REQUEST
    detail = "You can't buy free plan"

    def __init__(self):
        super().__init__(status_code=self.status_code, detail=self.detail)


class WeakerPlanException(HTTPException):
    status_code = status.HTTP_400_BAD_REQUEST
    detail = "You already have a more advanced plan"

    def __init__(self):
        super().__init__(status_code=self.status_code, detail=self.detail)

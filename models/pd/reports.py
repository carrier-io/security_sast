from pydantic import BaseModel


class StatusField(BaseModel):
    status: str = 'Pending...'
    percentage: int = 0
    description: str = 'Check if there are enough workers to perform the test'
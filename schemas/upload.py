from pydantic import BaseModel


class UploadResponse(BaseModel):
    filename: str
    stored_name: str
    size: int
    message: str

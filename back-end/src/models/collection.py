from pydantic import BaseModel, Field


class CollectionCreateRequest(BaseModel):
    name: str = Field(..., min_length=1)
    vector_size: int = 1536


class CollectionListResponse(BaseModel):
    collections: list[str]


class UploadResponse(BaseModel):
    collection: str
    chunks: int

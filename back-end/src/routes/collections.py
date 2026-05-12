import tempfile
from functools import lru_cache
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from src.models.collection import (
    CollectionCreateRequest,
    CollectionListResponse,
    UploadResponse,
)
from src.services.openai_service import OpenAIService
from src.services.qdrant_service import QdrantService

router = APIRouter(prefix="/collections", tags=["collections"])


@lru_cache
def get_qdrant_service() -> QdrantService:
    return QdrantService(openai_service=OpenAIService())


@router.get("", response_model=CollectionListResponse)
def list_collections(
    qdrant: QdrantService = Depends(get_qdrant_service),
) -> CollectionListResponse:
    return CollectionListResponse(collections=qdrant.list_collections())


@router.post("", response_model=CollectionListResponse, status_code=201)
def create_collection(
    req: CollectionCreateRequest,
    qdrant: QdrantService = Depends(get_qdrant_service),
) -> CollectionListResponse:
    if qdrant.collection_exists(req.name):
        raise HTTPException(status_code=409, detail="Coleção já existe.")
    qdrant.create_collection(req.name, vector_size=req.vector_size)
    return CollectionListResponse(collections=qdrant.list_collections())


@router.post("/{name}/documents", response_model=UploadResponse)
async def upload_document(
    name: str,
    file: UploadFile = File(...),
    qdrant: QdrantService = Depends(get_qdrant_service),
) -> UploadResponse:
    if not qdrant.collection_exists(name):
        raise HTTPException(status_code=404, detail="Coleção não encontrada.")

    suffix = Path(file.filename or "").suffix
    contents = await file.read()
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(contents)
        tmp_path = tmp.name
    try:
        chunks = qdrant.upload_file(name, tmp_path)
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=400,
            detail="Arquivo não é texto utf-8. Suportado: .txt, .md, .pdf.",
        )
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    return UploadResponse(collection=name, chunks=chunks)

import os
import uuid
from pathlib import Path

from pypdf import PdfReader
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from src.services.openai_service import OpenAIService

DEFAULT_VECTOR_SIZE = 1536  # text-embedding-3-small
DEFAULT_DISTANCE = Distance.COSINE
DEFAULT_CHUNK_SIZE = 1000
DEFAULT_CHUNK_OVERLAP = 100
DEFAULT_CLIENT_TIMEOUT = 60


class QdrantService:
    def __init__(
        self,
        endpoint: str | None = None,
        api_key: str | None = None,
        openai_service: OpenAIService | None = None,
    ):
        url = endpoint or os.getenv("QDRANT_ENDPOINT")
        key = api_key or os.getenv("QDRANT_API_KEY")
        if not url:
            raise RuntimeError(
                "QDRANT_ENDPOINT não definida. Configure no .env do back-end."
            )
        self.client = QdrantClient(url=url, api_key=key, timeout=DEFAULT_CLIENT_TIMEOUT)
        self.openai_service = openai_service

    def list_collections(self) -> list[str]:
        return [c.name for c in self.client.get_collections().collections]

    def collection_exists(self, name: str) -> bool:
        return self.client.collection_exists(collection_name=name)

    def create_collection(
        self,
        name: str,
        vector_size: int = DEFAULT_VECTOR_SIZE,
        distance: Distance = DEFAULT_DISTANCE,
        recreate: bool = False,
    ) -> None:
        if self.collection_exists(name):
            if not recreate:
                return
            self.delete_collection(name)
        self.client.create_collection(
            collection_name=name,
            vectors_config=VectorParams(size=vector_size, distance=distance),
        )

    def delete_collection(self, name: str) -> None:
        self.client.delete_collection(collection_name=name)

    def upsert_points(
        self,
        collection_name: str,
        vectors: list[list[float]],
        payloads: list[dict] | None = None,
        ids: list[str] | None = None,
    ) -> None:
        payloads = payloads or [{} for _ in vectors]
        ids = ids or [str(uuid.uuid4()) for _ in vectors]
        points = [
            PointStruct(id=i, vector=v, payload=p)
            for i, v, p in zip(ids, vectors, payloads)
        ]
        self.client.upsert(collection_name=collection_name, points=points)

    def upload_texts(
        self,
        collection_name: str,
        texts: list[str],
        metadata: list[dict] | None = None,
    ) -> int:
        self._require_openai()
        vectors = [self.openai_service.get_embedding(t) for t in texts]
        payloads: list[dict] = []
        for i, text in enumerate(texts):
            payload: dict = {"text": text}
            if metadata and i < len(metadata):
                payload.update(metadata[i])
            payloads.append(payload)
        self.upsert_points(collection_name, vectors, payloads)
        return len(texts)

    def upload_file(
        self,
        collection_name: str,
        file_path: str,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
    ) -> int:
        path = Path(file_path)
        if path.suffix.lower() == ".pdf":
            chunks, metadata = self._extract_pdf(path, chunk_size, chunk_overlap)
        else:
            text = path.read_text(encoding="utf-8")
            chunks = self._chunk_text(text, chunk_size, chunk_overlap)
            metadata = [
                {"source": path.name, "chunk_index": i}
                for i in range(len(chunks))
            ]
        if not chunks:
            return 0
        return self.upload_texts(collection_name, chunks, metadata)

    def _extract_pdf(
        self, path: Path, chunk_size: int, chunk_overlap: int
    ) -> tuple[list[str], list[dict]]:
        reader = PdfReader(str(path))
        chunks: list[str] = []
        metadata: list[dict] = []
        for page_num, page in enumerate(reader.pages, start=1):
            page_text = page.extract_text() or ""
            if not page_text.strip():
                continue
            page_chunks = self._chunk_text(page_text, chunk_size, chunk_overlap)
            for i, chunk in enumerate(page_chunks):
                chunks.append(chunk)
                metadata.append(
                    {
                        "source": path.name,
                        "page": page_num,
                        "chunk_index": i,
                    }
                )
        return chunks, metadata

    def search(
        self,
        collection_name: str,
        query: str,
        limit: int = 5,
    ) -> list[dict]:
        self._require_openai()
        vector = self.openai_service.get_embedding(query)
        result = self.client.query_points(
            collection_name=collection_name,
            query=vector,
            limit=limit,
        )
        return [
            {"id": p.id, "score": p.score, "payload": p.payload}
            for p in result.points
        ]

    def _require_openai(self) -> None:
        if self.openai_service is None:
            raise RuntimeError(
                "OpenAIService é necessário para gerar embeddings. "
                "Passe openai_service no construtor."
            )

    @staticmethod
    def _chunk_text(text: str, chunk_size: int, overlap: int) -> list[str]:
        if chunk_size <= overlap:
            raise ValueError("chunk_size precisa ser maior que overlap")
        chunks: list[str] = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunks.append(text[start:end])
            start = end - overlap
        return [c for c in chunks if c.strip()]

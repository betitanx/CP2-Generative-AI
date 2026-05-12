from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

from src.routes.chat import router as chat_router
from src.routes.collections import router as collections_router

app = FastAPI(title="ProjetoAI Chatbot API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router)
app.include_router(collections_router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}

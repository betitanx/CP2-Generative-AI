# Back-end — ProjetoAI Chatbot API

API em FastAPI que expõe um endpoint de chat. No momento todas as respostas são mocadas.

## Setup

```bash
cd back-end
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Rodar

```bash
uvicorn src.main:app --reload --port 8000
```

## Endpoints

- `GET /health` — checagem de saúde
- `POST /chat` — body: `{"message": "..."}` → `{"response": "..."}`

## Estrutura

```
back-end/
├── src/
│   ├── main.py           # entrypoint FastAPI
│   ├── models/chat.py    # schemas Pydantic
│   ├── routes/chat.py    # rotas /chat
│   └── services/chat_service.py  # lógica (mock por enquanto)
└── requirements.txt
```

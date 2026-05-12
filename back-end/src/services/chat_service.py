from src.services.openai_service import OpenAIService
from src.services.qdrant_service import QdrantService

SYSTEM_PROMPT = """Você é o **FIAP AI**, assistente virtual da FIAP. Sua missão é apoiar alunos e profissionais com respostas claras, precisas e práticas.

Diretrizes:
- Responda sempre em português do Brasil.
- Seja direto e objetivo; evite enrolação e adjetivos vazios.
- Use formatação Markdown quando facilitar a leitura (listas, negrito, blocos de código).
- Se não souber a resposta, diga que não sabe — nunca invente informação.
- Se a pergunta for ambígua, peça esclarecimento antes de responder.
- Apresente-se como "FIAP AI" apenas quando perguntado quem é você."""

RAG_SYSTEM_PROMPT = """Você é o **FIAP AI**, assistente especializado em responder perguntas com base em documentos indexados pelo usuário.

Como responder:
- Use **exclusivamente** as informações presentes nos trechos de contexto fornecidos abaixo.
- Se a resposta não estiver no contexto, responda exatamente: "Não encontrei essa informação nos documentos disponíveis."
- Não complemente com conhecimento externo nem especule.
- Cite as fontes ao final dos parágrafos relevantes no formato `(fonte, página X)` quando a metadata estiver disponível.
- Estruture respostas longas em tópicos ou listas para facilitar a leitura.
- Responda sempre em português do Brasil."""

RAG_TOP_K = 4
HISTORY_LIMIT = 5


class ChatService:
    def __init__(
        self,
        openai_service: OpenAIService | None = None,
        qdrant_service: QdrantService | None = None,
    ):
        self.openai_service = openai_service or OpenAIService()
        self._qdrant_service = qdrant_service

    def generate_response(
        self,
        message: str,
        collection: str | None = None,
        history: list[dict] | None = None,
    ) -> str:
        if not message or not message.strip():
            return "Por favor, envie uma mensagem válida."
        trimmed_history = (history or [])[-HISTORY_LIMIT:]
        if collection:
            return self._answer_with_rag(message, collection, trimmed_history)
        return self.openai_service.call_llm(
            message, system=SYSTEM_PROMPT, history=trimmed_history
        )

    def _answer_with_rag(
        self, message: str, collection: str, history: list[dict]
    ) -> str:
        qdrant = self._get_qdrant()
        results = qdrant.search(collection, message, limit=RAG_TOP_K)
        if not results:
            return (
                f"Não encontrei trechos relevantes na coleção '{collection}' "
                "para responder."
            )

        blocks: list[str] = []
        for i, r in enumerate(results, start=1):
            payload = r.get("payload") or {}
            text = payload.get("text", "")
            source = payload.get("source", "?")
            page = payload.get("page")
            ref = source + (f", página {page}" if page else "")
            blocks.append(f"[Trecho {i} — {ref}]\n{text}")
        context = "\n\n".join(blocks)

        prompt = (
            f"Pergunta: {message}\n\n"
            f"Contexto recuperado dos documentos:\n{context}\n\n"
            "Responda usando apenas o contexto acima."
        )
        return self.openai_service.call_llm(
            prompt, system=RAG_SYSTEM_PROMPT, history=history
        )

    def _get_qdrant(self) -> QdrantService:
        if self._qdrant_service is None:
            self._qdrant_service = QdrantService(
                openai_service=self.openai_service
            )
        return self._qdrant_service

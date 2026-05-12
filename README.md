# CP2 Generative AI - RAG Seguro com Governanca de IA

Projeto integrado de IA generativa e Governanca de IA. A entrega principal e um notebook Python que implementa um pipeline RAG com FAISS, simula dados sensiveis ficticios, demonstra ataques de prompt injection e compara o comportamento do sistema antes e depois de uma camada de protecao.

O repositorio tambem inclui o app complementar `ChatbotRAG`, com backend FastAPI e frontend Streamlit, preservado como base do projeto anterior.

## Entrega principal

- `RAG_Seguro_Prompt_Injection.ipynb`: notebook completo da entrega.
- `requirements.txt`: dependencias para executar o notebook.
- `back-end/`: API complementar em FastAPI.
- `front-end/`: interface complementar em Streamlit.

Todos os dados sensiveis usados no notebook sao ficticios e existem apenas para demonstracao academica.

## Requisitos

- Python 3.10+
- Chave da OpenAI configurada em `OPENAI_API_KEY`

Crie um arquivo `.env` na raiz, sem versiona-lo:

```bash
OPENAI_API_KEY=sua_chave_aqui
```

## Executar o notebook

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
jupyter notebook RAG_Seguro_Prompt_Injection.ipynb
```

Execute as celulas em ordem. O notebook interrompe a execucao com uma mensagem clara se `OPENAI_API_KEY` nao estiver configurada.

## O que o notebook demonstra

- Criacao de um documento sensivel ficticio com PII, credenciais, dados financeiros e segredos comerciais.
- Chunking do documento.
- Embeddings com OpenAI.
- Indexacao vetorial em FAISS.
- Recuperacao top-k.
- Geracao de respostas com LLM.
- Cenario RAG sem protecao.
- Cinco ataques distintos de prompt injection.
- Guardrails de input, contexto e output.
- Comparacao em tabela entre respostas vulneraveis e protegidas.
- Discussao de governanca com LGPD, OWASP LLM Top 10 e NIST AI RMF.

## App complementar: back-end

```bash
cd back-end
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn src.main:app --reload --port 8000
```

Endpoints principais:

- `GET /health`
- `POST /chat`
- `GET /collections`
- `POST /collections`
- `POST /collections/{name}/documents`

O app complementar usa Qdrant para colecoes vetoriais. Isso nao substitui o requisito academico do notebook, que usa FAISS.

## App complementar: front-end

Com o backend rodando em `http://localhost:8000`:

```bash
cd front-end
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run src/app.py
```

Para usar outro backend:

```bash
BACKEND_URL=http://meu-host:8000 streamlit run src/app.py
```

## Seguranca

Nao suba arquivos `.env`, chaves de API, bancos vetoriais locais, caches ou ambientes virtuais. O `.gitignore` deste repositorio ja cobre esses casos comuns.

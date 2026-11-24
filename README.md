# LocalBot: a mini ProManage

ProManage helps multi-location brands (banks, pharmacies, cafes) manage how
customers find them online. Two of its AI features are:
- a chatbot that answers customer questions about a store (Merlin AI), and
- AI replies to customer reviews, with a human checking the risky ones (Marvel AI).

LocalBot is a very small version of both, using a made-up cafe chain
("Brew & Co", 3 stores). It uses RAG for the chatbot: it looks up the facts for
the chosen store, then puts only those facts in the prompt.

Tested here: 12 automated tests pass, and I ran the web page end to end in
keyword mode with the model off. NOT tested here: the real embedding model and
Ollama (this sandbox cannot download them). Run them on your laptop.

## Run it (Windows PowerShell)
    python -m venv .venv
    .venv\Scripts\Activate.ps1
    pip install -r requirements.txt
    python -m pytest -q

Then start it in one of three modes:

1. Simplest (no downloads, no model):
       $env:SEARCH = "keyword"; $env:LLM = "none"
       python -m uvicorn app.main:app --reload
2. Semantic search, no model (downloads an 80 MB embedding model once):
       $env:SEARCH = "semantic"; $env:LLM = "none"
       python -m uvicorn app.main:app --reload
3. Full version: also install Ollama, run `ollama pull llama3.2:3b`, then
       $env:SEARCH = "semantic"; $env:LLM = "ollama"
       python -m uvicorn app.main:app --reload

## Deploy on Render with OpenRouter
1. Push this project to GitHub, then create a Render Web Service from that repository.
2. Render can use `render.yaml` as a Blueprint; provide `OPENROUTER_API_KEY` when
   prompted. It defaults to a free OpenRouter model. Keep the key in Render's
   environment settings, never in the repository or browser code.
3. Deploy and open the Render URL.

Open http://localhost:8000 . Choose a store, ask "Is there parking?", then paste
a review and press "Draft reply".

## Files, in the order you should read them
1. data/locations.json      the facts (made up)
2. app/knowledge.py         facts -> small text passages
3. app/retrievers.py        keyword search, then meaning search (embeddings)
4. app/chat.py              the prompt, and how retrieval + prompt make RAG
5. app/llm.py               the language model (Ollama) or no model
6. app/reviews.py           review replies and the human-approval rule
7. app/main.py              the web API (FastAPI)
8. static/index.html        the web page
9. tests/test_localbot.py   what each part must do

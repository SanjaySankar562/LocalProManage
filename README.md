# LocalProManage

LocalProManage is a small demo of AI tools for a multi-location business. It
includes a customer chatbot that answers from store-specific facts and a
review-reply assistant that drafts responses and flags negative reviews for
human approval.

The sample business, Brew & Co, and its three locations are fictional. The
chatbot retrieves relevant facts before answering (RAG), so it is designed to
answer only from the selected store's information.

## Install locally

You need Python and Git. In PowerShell:

```powershell
git clone https://github.com/SanjaySankar562/LocalProManage.git
cd LocalProManage
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

On macOS or Linux, activate the virtual environment with:

```sh
source .venv/bin/activate
```

## Choose how the chatbot runs

Set `SEARCH` and `LLM` in the same terminal before starting the app. For the
simplest local run, with no AI model or API key:

```powershell
$env:SEARCH = "keyword"
$env:LLM = "none"
python -m uvicorn app.main:app --reload
```

Then open http://localhost:8000. `LLM=none` uses a basic fact-based fallback;
it does not call an AI service. `SEARCH=keyword` also avoids downloading the
local embedding model.

### Local AI with Ollama

Install and start [Ollama](https://ollama.com/), then download the default model:

```powershell
ollama pull llama3.2:3b
$env:SEARCH = "semantic"
$env:LLM = "ollama"
python -m uvicorn app.main:app --reload
```

Ollama runs the language model on your computer, so no API key is needed.
Semantic search downloads its embedding model the first time it runs. You can
choose another Ollama model with `OLLAMA_MODEL`.

### Cloud AI with an OpenRouter API key

OpenRouter is the cloud AI provider currently supported by this project. Create
an API key in your OpenRouter account, then set it in PowerShell:

```powershell
$env:SEARCH = "semantic"
$env:LLM = "openrouter"
$env:OPENROUTER_API_KEY = "your-openrouter-api-key"
$env:OPENROUTER_MODEL = "openrouter/free"
python -m uvicorn app.main:app --reload
```

You can replace `openrouter/free` with another model ID supported by OpenRouter.
The key is read from the environment; never put it in source code or commit it
to GitHub. Other providers' API keys (such as OpenAI or Anthropic) are not
interchangeable with an OpenRouter key and are not currently supported.

`SEARCH` can be `keyword` or `semantic`. Semantic search uses a local embedding
model; choosing OpenRouter only changes the language model that writes the
answer.

## Run tests

```powershell
python -m pytest -q
```

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

### Cloud AI with an OpenAI-compatible API

The app supports providers that implement the OpenAI-compatible Chat
Completions API. Set the key, model ID, and (for providers other than OpenAI)
the provider's API base URL:

```powershell
$env:SEARCH = "semantic"
$env:LLM = "openai-compatible"
$env:LLM_API_KEY = "your-provider-api-key"
$env:LLM_API_MODEL = "your-model-id"
$env:LLM_API_BASE_URL = "https://api.openai.com/v1"
python -m uvicorn app.main:app --reload
```

For OpenAI, the base URL defaults to `https://api.openai.com/v1`. For another
compatible provider, replace it with that provider's documented base URL. The
model ID must be available to your account. A key alone is not enough: the
provider must support `POST /chat/completions` with Bearer authentication.

OpenRouter remains supported with its own settings:

```powershell
$env:LLM = "openrouter"
$env:OPENROUTER_API_KEY = "your-openrouter-api-key"
$env:OPENROUTER_MODEL = "openrouter/free"
python -m uvicorn app.main:app --reload
```

Keys are read from environment variables; never put them in source code or
commit them to GitHub. Providers' non-compatible native APIs are not supported
by the generic mode.

`SEARCH` can be `keyword` or `semantic`. Semantic search uses a local embedding
model; choosing a cloud provider only changes the language model that writes
the answer.

## Run tests

```powershell
python -m pytest -q
```

"""Step 5: choose a local Ollama model, OpenRouter, or no model."""
import os

import requests


class OllamaLLM:
    """Send prompts to a local Ollama model through its HTTP API."""
    is_real = True

    def __init__(self, model: str | None = None, host: str | None = None):
        self.model = model or os.getenv("OLLAMA_MODEL", "llama3.2:3b")
        self.host = host or os.getenv("OLLAMA_HOST", "http://localhost:11434")

    def generate(self, prompt: str) -> str:
        # Temperature stays low so generated answers vary less from the supplied facts.
        try:
            r = requests.post(
                f"{self.host}/api/generate",
                json={"model": self.model, "prompt": prompt, "stream": False,
                      "options": {"temperature": 0.1}},
                timeout=300,
            )
            r.raise_for_status()
        except requests.exceptions.ConnectionError as e:
            raise RuntimeError(
                "Cannot reach Ollama. Start it and run `ollama pull "
                f"{self.model}`, or set LLM=none."
            ) from e
        return r.json()["response"].strip()


class OpenAICompatibleLLM:
    """Send prompts to an OpenAI-compatible chat completions API."""
    is_real = True

    def __init__(self):
        self.api_key = os.getenv("LLM_API_KEY")
        self.base_url = os.getenv("LLM_API_BASE_URL", "https://api.openai.com/v1").rstrip("/")
        self.model = os.getenv("LLM_API_MODEL")
        if not self.api_key or not self.model:
            raise RuntimeError("Set LLM_API_KEY and LLM_API_MODEL to use an API provider.")

    def generate(self, prompt: str) -> str:
        r = requests.post(
            f"{self.base_url}/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.1,
            },
            timeout=120,
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"].strip()


class OpenRouterLLM(OpenAICompatibleLLM):
    """Send prompts to OpenRouter using its existing environment variables."""

    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.base_url = "https://openrouter.ai/api/v1"
        self.model = os.getenv("OPENROUTER_MODEL") or "google/gemma-4-31b-it:free"
        if not self.api_key:
            raise RuntimeError("Set OPENROUTER_API_KEY to use OpenRouter.")


class NoLLM:
    """No model: answer with the best matching fact so the demo still works."""

    is_real = False

    def generate(self, prompt: str) -> str:
        facts = prompt.split("Facts:\n", 1)[-1].split("\n\nCustomer question:", 1)[0]
        first = facts.strip().splitlines()[0].lstrip("- ").strip() if facts.strip() else ""
        return first or "I am not sure. Please call the store."


def get_llm():
    mode = os.getenv("LLM", "").lower()
    if not mode:
        mode = "openrouter" if os.getenv("OPENROUTER_API_KEY") else "ollama"
    if mode == "none":
        return NoLLM()
    if mode == "openrouter":
        return OpenRouterLLM()
    if mode == "openai-compatible":
        return OpenAICompatibleLLM()
    return OllamaLLM()

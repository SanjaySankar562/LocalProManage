class DefaultEmbedder:
    """Free local embeddings (small MiniLM model that ships with Chroma).

    The first call downloads about 80 MB once. After that it works offline.
    """

    def __init__(self) -> None:
        self._fn = None

    def embed(self, texts: list[str]) -> list[list[float]]:
        # Lazy-load the downloaded model so keyword-only mode stays model-free.
        if self._fn is None:
            from chromadb.utils.embedding_functions import DefaultEmbeddingFunction

            self._fn = DefaultEmbeddingFunction()
        return [list(map(float, v)) for v in self._fn(texts)]

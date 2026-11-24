"""Steps 2 and 3: two ways to find the passages that match a question.

KeywordRetriever  - counts shared words. Simple, no AI, easy to understand.
SemanticRetriever - compares meaning using embeddings and a vector database.

Both have the same method, search(question, location, k), so the rest of the
program does not care which one it is using.
"""
import re
import uuid

STOPWORDS = {
    "a", "an", "the", "do", "does", "you", "your", "i", "can", "is", "are", "to",
    "of", "on", "in", "at", "for", "what", "when", "how", "have", "we", "my", "it",
    "there", "and", "or", "me", "us", "any", "this", "that", "with",
}


def tokens(text: str) -> set[str]:
    """Normalize text into meaningful words for the no-download keyword search."""
    words = re.findall(r"[a-z0-9]+", text.lower())
    out = set()
    for w in words:
        if w in STOPWORDS:
            continue
        # very crude stemming so "opening" matches "open" and "cafes" matches "cafe"
        for suffix in ("ing", "es", "s"):
            if w.endswith(suffix) and len(w) - len(suffix) >= 3:
                w = w[: -len(suffix)]
                break
        out.add(w)
    return out


class KeywordRetriever:
    """Rank passages by shared words, filtered to one store when requested."""
    def __init__(self, passages: list[dict]):
        self.passages = passages

    def search(self, question: str, location: str | None = None, k: int = 3) -> list[dict]:
        q = tokens(question)
        scored = []
        for p in self.passages:
            if location and p["location"] != location:
                continue  # filter: only look at the chosen store
            score = len(q & tokens(p["text"]))
            if score > 0:
                scored.append((score, p))
        scored.sort(key=lambda pair: pair[0], reverse=True)
        return [dict(p, score=float(s)) for s, p in scored[:k]]


class SemanticRetriever:
    """Index passages by meaning and query them with cosine similarity."""
    def __init__(self, passages: list[dict], embedder, client=None):
        import chromadb

        self.embedder = embedder
        self.client = client or chromadb.EphemeralClient()
        # a unique name avoids clashes if the app builds the index twice
        self.collection = self.client.get_or_create_collection(
            name=f"passages_{uuid.uuid4().hex}", metadata={"hnsw:space": "cosine"}
        )
        self.collection.upsert(
            ids=[p["id"] for p in passages],
            documents=[p["text"] for p in passages],
            metadatas=[{"location": p["location"]} for p in passages],
            embeddings=embedder.embed([p["text"] for p in passages]),
        )

    def search(self, question: str, location: str | None = None, k: int = 3) -> list[dict]:
        where = {"location": location} if location else None
        res = self.collection.query(
            query_embeddings=self.embedder.embed([question]),
            n_results=k,
            where=where,
        )
        hits = []
        for pid, text, meta, dist in zip(
            res["ids"][0], res["documents"][0], res["metadatas"][0], res["distances"][0]
        ):
            hits.append(
                {"id": pid, "text": text, "location": meta["location"], "score": 1 - float(dist)}
            )
        return hits

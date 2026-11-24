"""Step 4: RAG = retrieve facts, then put them in the prompt."""

PROMPT = """You are the customer support assistant for Brew & Co, a cafe chain.
Answer using ONLY the facts below. If the facts do not contain the answer, say you
are not sure and suggest calling the store. Keep the answer to 2 or 3 sentences.

Facts:
{facts}

Customer question: {question}
Answer:"""

NOT_SURE = "I'm not sure about that. Please call the store and the team will help."


def build_prompt(question: str, hits: list[dict]) -> str:
    """Convert retrieved passages into a prompt that limits answers to known facts."""
    facts = "\n".join(f"- {h['text']}" for h in hits)
    return PROMPT.format(facts=facts, question=question)


def answer_question(question: str, location: str | None, retriever, llm, k: int = 3) -> dict:
    """Search first, then use the model only when facts were found."""
    hits = retriever.search(question, location, k)
    if not hits:
        return {"answer": NOT_SURE, "sources": []}
    answer = llm.generate(build_prompt(question, hits))
    return {"answer": answer, "sources": hits}

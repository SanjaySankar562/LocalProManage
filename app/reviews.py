"""Step 6: draft a reply to a customer review, and flag the risky ones for a human."""

NEGATIVE_WORDS = {"bad", "rude", "dirty", "slow", "cold", "terrible", "worst", "stale", "overpriced"}
POSITIVE_WORDS = {"great", "love", "loved", "friendly", "excellent", "amazing", "delicious", "best"}

REPLY_PROMPT = """You write replies to Google reviews for Brew & Co {name}.
Tone: warm, polite and short (2 to 3 sentences). Use simple words.
Rules: never promise refunds or discounts. Do not invent facts.
Consider both the star rating and written review; they may disagree.
{extra}
Review ({rating} stars): "{review}"
Reply:"""


def classify_sentiment(review: str, rating: int | None = None) -> str:
    """Combine review wording and stars, prioritizing either negative signal."""
    words = set(review.lower().split())
    if (rating is not None and rating <= 2) or words & NEGATIVE_WORDS:
        return "negative"
    if (rating is not None and rating >= 4) or words & POSITIVE_WORDS:
        return "positive"
    return "neutral"


def template_reply(sentiment: str, location: dict) -> str:
    """Produce a safe local reply when no real language model is enabled."""
    name = location["name"]
    if sentiment == "positive":
        return f"Thank you for the lovely review! We are so glad you enjoyed {name}. See you again soon. - Team {name}"
    if sentiment == "negative":
        return (f"We are sorry your visit to {name} did not go well. Please call us on "
                f"{location['phone']} so we can look into it. - Team {name}")
    return f"Thank you for your feedback about {name}. We would love to hear how we can improve. - Team {name}"


def draft_reply(review: str, rating: int | None, location: dict, llm) -> dict:
    """Draft a reply and require approval for negative sentiment."""
    sentiment = classify_sentiment(review, rating)
    if getattr(llm, "is_real", False):
        extra = ""
        if sentiment == "negative":
            extra = f"Apologise, and invite them to call {location['phone']}."
        prompt = REPLY_PROMPT.format(name=location["name"], extra=extra,
                                     rating=rating if rating is not None else "?", review=review)
        reply = llm.generate(prompt)
    else:
        reply = template_reply(sentiment, location)
    # Human in the loop: a person must approve replies to unhappy customers.
    return {"sentiment": sentiment, "reply": reply, "needs_human_approval": sentiment == "negative"}

"""Step 1: turn the location data into small text passages.

RAG works on pieces of text ("passages"). We build one passage per fact so a
search can return exactly the fact that answers the question.
"""
import json
from pathlib import Path


def load_locations(path: str = "data/locations.json") -> list[dict]:
    """Load the small store dataset from disk."""
    return json.loads(Path(path).read_text(encoding="utf-8"))


def build_passages(locations: list[dict]) -> list[dict]:
    """Split each store into independent facts for keyword or semantic retrieval."""
    passages = []
    for loc in locations:
        facts = [
            f"{loc['name']} opening hours: {loc['hours']}.",
            f"{loc['name']} address: {loc['address']}. Phone: {loc['phone']}.",
            f"{loc['name']} services and facilities: {', '.join(loc['services'])}.",
        ]
        for item in loc["faq"]:
            facts.append(f"{loc['name']} - {item['q']} {item['a']}")
        for n, text in enumerate(facts):
            passages.append(
                {"id": f"{loc['id']}-{n}", "location": loc["id"], "text": text}
            )
    return passages

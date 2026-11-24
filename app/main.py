"""FastAPI entry point: validates requests, wires features, and serves the web page."""
import os

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .chat import answer_question
from .embedder import DefaultEmbedder
from .knowledge import build_passages, load_locations
from .llm import get_llm
from .retrievers import KeywordRetriever, SemanticRetriever
from .reviews import draft_reply

app = FastAPI(title="LocalBot: a mini ProManage")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Locations stay in memory because this is a small, read-only demo.
LOCATIONS = load_locations()
BY_ID = {loc["id"]: loc for loc in LOCATIONS}
_state: dict = {}


def retriever():
    """Build the selected search backend once; later calls reuse the same index."""
    if "r" not in _state:
        passages = build_passages(LOCATIONS)
        if os.getenv("SEARCH", "semantic").lower() == "keyword":
            _state["r"] = KeywordRetriever(passages)
        else:
            _state["r"] = SemanticRetriever(passages, DefaultEmbedder())
    return _state["r"]


def llm():
    """Create one model adapter once so Ollama configuration is shared."""
    if "llm" not in _state:
        _state["llm"] = get_llm()
    return _state["llm"]


class ChatRequest(BaseModel):
    """Request shape for a store-specific customer question."""
    question: str = Field(min_length=3)
    location: str | None = None


class ReviewRequest(BaseModel):
    """Request shape for a review, optional rating, and required store."""
    review: str = Field(min_length=1)
    rating: int | None = Field(default=None, ge=1, le=5)
    location: str


def check_location(location_id: str | None):
    """Reject unknown store IDs instead of silently searching or replying for another store."""
    if location_id is not None and location_id not in BY_ID:
        raise HTTPException(status_code=404, detail=f"Unknown location: {location_id}")


@app.get("/")
def home():
    return FileResponse("static/index.html")


@app.get("/locations")
def locations():
    return [{"id": l["id"], "name": l["name"], "city": l["city"]} for l in LOCATIONS]


@app.post("/chat")
def chat(req: ChatRequest):
    check_location(req.location)
    return answer_question(req.question, req.location, retriever(), llm())


@app.post("/review-reply")
def review_reply(req: ReviewRequest):
    check_location(req.location)
    return draft_reply(req.review, req.rating, BY_ID[req.location], llm())

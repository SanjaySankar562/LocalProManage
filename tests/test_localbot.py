"""End-to-end and unit checks for retrieval, prompts, replies, and API validation."""

import chromadb
from fastapi.testclient import TestClient
from unittest.mock import patch

from app import main
from app.chat import NOT_SURE, answer_question, build_prompt
from app.knowledge import build_passages, load_locations
from app.llm import NoLLM, OllamaLLM, OpenAICompatibleLLM, OpenRouterLLM, get_llm
from app.retrievers import KeywordRetriever, SemanticRetriever, tokens
from app.reviews import classify_sentiment, draft_reply
from tests.fakes import FakeEmbedder, FakeLLM

LOCS = load_locations()
PASSAGES = build_passages(LOCS)
KW = KeywordRetriever(PASSAGES)


def test_passages_cover_every_location():
    assert {p["location"] for p in PASSAGES} == {"adyar", "indiranagar", "banjara"}
    assert all(p["text"] for p in PASSAGES)


def test_tokens_stem_and_drop_stopwords():
    assert "open" in tokens("Opening hours") and "the" not in tokens("the cafe")


def test_keyword_filters_by_location():
    hits = KW.search("Is there parking?", "indiranagar")
    assert hits and all(h["location"] == "indiranagar" for h in hits)
    assert "no parking" in hits[0]["text"]


def test_different_stores_give_different_answers():
    adyar = KW.search("birthday party booking", "adyar")[0]["text"]
    indira = KW.search("birthday party booking", "indiranagar")[0]["text"]
    assert "25 people" in adyar and "does not take party bookings" in indira


def test_keyword_misses_a_question_that_needs_meaning():
    # "work on my laptop" shares no words with "free wifi": the weakness of keywords
    assert KW.search("Can I work on my laptop?", "adyar") == []


def test_semantic_retriever_returns_scored_hits_for_one_store():
    r = SemanticRetriever(PASSAGES, FakeEmbedder(), client=chromadb.EphemeralClient())
    hits = r.search("opening hours", "banjara", k=2)
    assert len(hits) == 2 and all(h["location"] == "banjara" for h in hits)
    assert "closed on Monday" in hits[0]["text"]


def test_prompt_contains_facts_and_question():
    p = build_prompt("Is it open Sunday?", [{"text": "Sunday 9am to 9pm"}])
    assert "ONLY the facts" in p and "Sunday 9am to 9pm" in p and "Is it open Sunday?" in p


def test_answer_with_llm_and_without_hits():
    llm = FakeLLM()
    out = answer_question("Is there parking?", "adyar", KW, llm)
    assert out["answer"] == "fake answer" and "parking for 10 bikes" in llm.last_prompt
    llm2 = FakeLLM()
    out2 = answer_question("zzzz qqqq", "adyar", KW, llm2)
    assert out2["answer"] == NOT_SURE and llm2.last_prompt is None


def test_no_llm_mode_returns_best_fact():
    out = answer_question("Is there parking?", "adyar", KW, NoLLM())
    assert "parking" in out["answer"].lower()


def test_openrouter_uses_server_side_key():
    with patch.dict("os.environ", {
        "LLM": "openrouter",
        "OPENROUTER_API_KEY": "test-key",
        "OPENROUTER_MODEL": "test/model",
    }):
        llm = get_llm()
    with patch("app.llm.requests.post") as post:
        post.return_value.json.return_value = {
            "choices": [{"message": {"content": "AI answer"}}]
        }
        assert llm.generate("test prompt") == "AI answer"
    args, kwargs = post.call_args
    assert args[0] == "https://openrouter.ai/api/v1/chat/completions"
    assert kwargs["headers"]["Authorization"] == "Bearer test-key"
    assert kwargs["json"]["model"] == "test/model"


def test_openai_compatible_uses_configured_endpoint():
    with patch.dict("os.environ", {
        "LLM": "openai-compatible",
        "LLM_API_KEY": "test-key",
        "LLM_API_BASE_URL": "https://api.example.test/v1/",
        "LLM_API_MODEL": "test/model",
    }, clear=True):
        llm = get_llm()
    assert isinstance(llm, OpenAICompatibleLLM)
    with patch("app.llm.requests.post") as post:
        post.return_value.json.return_value = {
            "choices": [{"message": {"content": "AI answer"}}]
        }
        assert llm.generate("test prompt") == "AI answer"
    args, kwargs = post.call_args
    assert args[0] == "https://api.example.test/v1/chat/completions"
    assert kwargs["headers"]["Authorization"] == "Bearer test-key"
    assert kwargs["json"]["model"] == "test/model"


def test_openrouter_defaults_when_key_is_configured():
    with patch.dict("os.environ", {}, clear=True):
        assert isinstance(get_llm(), OllamaLLM)
    with patch.dict("os.environ", {"OPENROUTER_API_KEY": "test-key"}, clear=True):
        llm = get_llm()
    assert isinstance(llm, OpenRouterLLM)
    assert llm.model == "google/gemma-4-31b-it:free"


def test_sentiment_rules():
    assert classify_sentiment("fine", 5) == "positive"
    assert classify_sentiment("fine", 3) == "neutral"
    assert classify_sentiment("fine", 1) == "negative"
    assert classify_sentiment("rude staff and slow service") == "negative"
    assert classify_sentiment("bad store not clean", 5) == "negative"
    assert classify_sentiment("great coffee", 1) == "negative"


def test_negative_reviews_need_human_approval():
    loc = LOCS[0]
    bad = draft_reply("Terrible, rude staff", 1, loc, NoLLM())
    bad_with_five_stars = draft_reply("Bad store, not clean", 5, loc, NoLLM())
    good = draft_reply("Loved it", 5, loc, NoLLM())
    assert bad["needs_human_approval"] and loc["phone"] in bad["reply"]
    assert bad_with_five_stars["needs_human_approval"]
    assert not good["needs_human_approval"]


def test_api_end_to_end():
    # One test exercises location loading, chat, review approval, and validation.
    main._state["r"] = KW
    main._state["llm"] = NoLLM()
    c = TestClient(main.app)
    assert len(c.get("/locations").json()) == 3
    r = c.post("/chat", json={"question": "Do you have free wifi?", "location": "banjara"})
    assert r.status_code == 200 and "wifi" in r.json()["answer"].lower()
    r = c.post("/review-reply", json={"review": "Cold coffee", "rating": 1, "location": "adyar"})
    assert r.json()["needs_human_approval"] is True
    assert c.post("/chat", json={"question": "hello there", "location": "nowhere"}).status_code == 404
    assert c.post("/chat", json={"question": "hi"}).status_code == 422
    assert c.get("/").status_code == 200
    assert "/static/app.js" in c.get("/").text
    assert "/static/styles.css" in c.get("/").text
    assert c.get("/static/app.js").status_code == 200
    assert c.get("/static/styles.css").status_code == 200

import hashlib
import math
import re


class FakeEmbedder:
    """Counts words into 128 buckets. No download, fully predictable."""

    def embed(self, texts):
        out = []
        for t in texts:
            v = [0.0] * 128
            for w in re.findall(r"[a-z0-9]+", t.lower()):
                v[int(hashlib.md5(w.encode()).hexdigest(), 16) % 128] += 1.0
            n = math.sqrt(sum(x * x for x in v)) or 1.0
            out.append([x / n for x in v])
        return out


class FakeLLM:
    is_real = True

    def __init__(self):
        self.last_prompt = None

    def generate(self, prompt):
        self.last_prompt = prompt
        return "fake answer"
"""Deterministic substitutes that keep tests independent of a network or downloaded model."""


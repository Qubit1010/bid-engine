"""Hybrid retrieval over the capability library: cosine similarity + keyword overlap.

At 50 records an in-memory index is the right call - no vector DB needed.
"""
import re

import numpy as np

from core import llm
from db import database
from rag import embeddings

STOPWORDS = {
    "the", "a", "an", "of", "to", "and", "or", "for", "in", "on", "with", "by",
    "must", "shall", "should", "be", "is", "are", "have", "has", "provide",
    "bidder", "bidders", "firm", "company", "all", "any", "least", "at",
}


def _tokens(text: str) -> set[str]:
    return {t for t in re.findall(r"[a-z0-9]+", text.lower())
            if len(t) > 2 and t not in STOPWORDS}


def keyword_score(query: str, doc: str) -> float:
    q, d = _tokens(query), _tokens(doc)
    if not q:
        return 0.0
    return len(q & d) / len(q)


class CapabilityRetriever:
    def __init__(self) -> None:
        self.vectors, self.cap_ids = embeddings.load_index()
        caps = {c["cap_id"]: c for c in database.get_capabilities()}
        self.caps = [caps[cid] for cid in self.cap_ids]
        self.texts = [embeddings.cap_to_text(c) for c in self.caps]

    def retrieve(self, query: str, top_k: int = 3) -> list[dict]:
        """Returns top-k capabilities with hybrid scores in [0, 1]."""
        qvec, space = llm.embed([query])
        if space not in self.vectors:  # query embedded offline but index lacks hash? rebuild-safe
            space = "hash"
            qvec = np.vstack([llm.hash_embed(query)])
        index = self.vectors[space]
        qv = qvec[0]
        cos = index @ qv / (np.linalg.norm(index, axis=1) * (np.linalg.norm(qv) or 1.0))
        kw = np.array([keyword_score(query, t) for t in self.texts])
        hybrid = 0.7 * cos + 0.3 * kw

        order = np.argsort(hybrid)[::-1][:top_k]
        results = []
        for i in order:
            cap = dict(self.caps[i])
            cap["score"] = round(float(hybrid[i]), 4)
            cap["cosine"] = round(float(cos[i]), 4)
            cap["keyword"] = round(float(kw[i]), 4)
            cap["space"] = space
            results.append(cap)
        return results


_retriever: CapabilityRetriever | None = None


def get_retriever(refresh: bool = False) -> CapabilityRetriever:
    global _retriever
    if _retriever is None or refresh:
        _retriever = CapabilityRetriever()
    return _retriever

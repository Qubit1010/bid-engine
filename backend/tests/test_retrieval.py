"""Retrieval sanity: known queries must surface the right capability records."""
from rag.retriever import get_retriever


def test_solar_query_hits_solar_caps():
    hits = get_retriever().retrieve("design and install grid-tied solar PV systems", top_k=5)
    domains = {h["domain"] for h in hits}
    assert "Solar Energy" in domains


def test_results_sorted_by_score():
    hits = get_retriever().retrieve("road construction and rehabilitation works", top_k=5)
    scores = [h["score"] for h in hits]
    assert scores == sorted(scores, reverse=True)


def test_topk_respected():
    assert len(get_retriever().retrieve("anything at all really", top_k=3)) == 3


def test_evidence_shape():
    hit = get_retriever().retrieve("hospital IT deployment", top_k=1)[0]
    for key in ("cap_id", "domain", "summary", "score", "cosine", "keyword"):
        assert key in hit

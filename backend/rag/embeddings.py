"""Capability-library embedding index. Built once at seed time, cached on disk
in BOTH embedding spaces (openai + hash) so retrieval works fully offline."""
import json

import numpy as np

from core import config, llm
from db import database

INDEX_PATH = config.MODELS_DIR / "capability_index.npz"
META_PATH = config.MODELS_DIR / "capability_index_meta.json"


def cap_to_text(cap: dict) -> str:
    return (
        f"{cap['domain']}. {cap['summary']}. "
        f"Certification: {cap['certification']}. Client type: {cap['client_type']}. "
        f"Contract value {cap['contract_value']}, duration {cap['duration_months']} months, "
        f"completed {cap['year_completed']}."
    )


def build_capability_index() -> str:
    caps = database.get_capabilities()
    if not caps:
        raise RuntimeError("No capabilities in DB - run db/seed.py first")
    texts = [cap_to_text(c) for c in caps]

    openai_vecs, space = llm.embed(texts)
    hash_vecs = np.vstack([llm.hash_embed(t) for t in texts])

    arrays = {"hash": hash_vecs}
    if space == "openai":
        arrays["openai"] = openai_vecs
    np.savez(INDEX_PATH, **arrays)
    META_PATH.write_text(json.dumps({
        "cap_ids": [c["cap_id"] for c in caps],
        "spaces": list(arrays.keys()),
    }))
    return space


def load_index() -> tuple[dict[str, np.ndarray], list[str]]:
    if not INDEX_PATH.exists():
        build_capability_index()
    data = np.load(INDEX_PATH)
    meta = json.loads(META_PATH.read_text())
    return {k: data[k] for k in data.files}, meta["cap_ids"]

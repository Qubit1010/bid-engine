"""Dual-provider LLM client: Claude primary, OpenAI fallback, disk cache.

Every call is cached on disk keyed by a hash of the prompt, so a warmed demo
replays fully offline and never re-burns tokens.
"""
import hashlib
import json
import re
from pathlib import Path
from typing import Any

import numpy as np

from core import config

_anthropic_client = None
_openai_client = None


def _anthropic():
    global _anthropic_client
    if _anthropic_client is None:
        import anthropic
        _anthropic_client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
    return _anthropic_client


def _openai():
    global _openai_client
    if _openai_client is None:
        from openai import OpenAI
        _openai_client = OpenAI(api_key=config.OPENAI_API_KEY)
    return _openai_client


def _cache_path(bucket: str, key: str) -> Path:
    d = config.CACHE_DIR / bucket
    d.mkdir(parents=True, exist_ok=True)
    return d / f"{key}.json"


def _hash(*parts: str) -> str:
    h = hashlib.sha256()
    for p in parts:
        h.update(p.encode("utf-8", errors="replace"))
    return h.hexdigest()[:32]


def parse_json_response(text: str) -> Any:
    """Robustly pull a JSON object/array out of an LLM response."""
    text = text.strip()
    fence = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
    if fence:
        text = fence.group(1).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # fall back to the first balanced {...} or [...] block
    for opener, closer in (("{", "}"), ("[", "]")):
        start = text.find(opener)
        if start == -1:
            continue
        depth = 0
        for i in range(start, len(text)):
            if text[i] == opener:
                depth += 1
            elif text[i] == closer:
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(text[start : i + 1])
                    except json.JSONDecodeError:
                        break
    raise ValueError(f"No parseable JSON in LLM response: {text[:200]}")


def _openai_chat(system: str, user: str, max_tokens: int, json_mode: bool) -> str:
    kwargs: dict[str, Any] = {
        "model": config.OPENAI_MODEL,
        "max_completion_tokens": max_tokens,
        "messages": [
            {"role": "system", "content": system + ("\nRespond with a single JSON object." if json_mode else "")},
            {"role": "user", "content": user},
        ],
    }
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}
    if config.OPENAI_MODEL.startswith("gpt-5"):
        kwargs["reasoning_effort"] = "low"
    resp = _openai().chat.completions.create(**kwargs)
    return resp.choices[0].message.content


def complete_json(system: str, user: str, max_tokens: int = 8192,
                  bucket: str = "llm") -> Any:
    """JSON-mode completion with OpenAI -> Claude fallback and disk cache."""
    key = _hash(system, user)
    path = _cache_path(bucket, key)
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))["data"]

    data, provider = None, None
    errors = []
    try:
        data = parse_json_response(_openai_chat(system, user, max_tokens, json_mode=True))
        provider = "openai"
    except Exception as e:  # noqa: BLE001 - any provider failure triggers fallback
        errors.append(f"openai: {e}")
        try:
            resp = _anthropic().messages.create(
                model=config.CLAUDE_MODEL,
                max_tokens=min(max_tokens, 8192),
                system=system,
                messages=[{"role": "user", "content": user}],
            )
            data = parse_json_response(resp.content[0].text)
            provider = "anthropic"
        except Exception as e2:  # noqa: BLE001
            errors.append(f"anthropic: {e2}")
            raise RuntimeError("All LLM providers failed: " + " | ".join(errors)) from e2

    path.write_text(json.dumps({"provider": provider, "data": data}), encoding="utf-8")
    return data


def complete_text(system: str, user: str, max_tokens: int = 8192,
                  bucket: str = "llm-text") -> str:
    key = _hash(system, user)
    path = _cache_path(bucket, key)
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))["data"]

    errors = []
    try:
        text, provider = _openai_chat(system, user, max_tokens, json_mode=False), "openai"
    except Exception as e:  # noqa: BLE001
        errors.append(f"openai: {e}")
        try:
            resp = _anthropic().messages.create(
                model=config.CLAUDE_MODEL,
                max_tokens=min(max_tokens, 8192),
                system=system,
                messages=[{"role": "user", "content": user}],
            )
            text, provider = resp.content[0].text, "anthropic"
        except Exception as e2:  # noqa: BLE001
            errors.append(f"anthropic: {e2}")
            raise RuntimeError("All LLM providers failed: " + " | ".join(errors)) from e2

    path.write_text(json.dumps({"provider": provider, "data": text}), encoding="utf-8")
    return text


# ---------------------------------------------------------------------------
# Embeddings
# ---------------------------------------------------------------------------

EMBED_DIM = 1536  # text-embedding-3-small
HASH_DIM = 512


def hash_embed(text: str, dim: int = HASH_DIM) -> np.ndarray:
    """Deterministic offline-safe embedding via the hashing trick (unigrams+bigrams)."""
    vec = np.zeros(dim, dtype=np.float32)
    tokens = re.findall(r"[a-z0-9]+", text.lower())
    grams = tokens + [f"{a}_{b}" for a, b in zip(tokens, tokens[1:])]
    for g in grams:
        idx = int(hashlib.md5(g.encode()).hexdigest(), 16)
        vec[idx % dim] += 1.0 if (idx >> 16) % 2 else -1.0
    norm = np.linalg.norm(vec)
    return vec / norm if norm > 0 else vec


def embed(texts: list[str]) -> tuple[np.ndarray, str]:
    """Embed texts. Returns (matrix, space) where space is 'openai' or 'hash'.

    Per-text disk cache means warmed demo queries replay offline in openai space.
    """
    cached: dict[int, np.ndarray] = {}
    missing: list[tuple[int, str]] = []
    for i, t in enumerate(texts):
        p = _cache_path("embeddings", _hash(config.EMBEDDING_MODEL, t))
        if p.exists():
            cached[i] = np.array(json.loads(p.read_text())["v"], dtype=np.float32)
        else:
            missing.append((i, t))

    if missing:
        try:
            resp = _openai().embeddings.create(
                model=config.EMBEDDING_MODEL, input=[t for _, t in missing]
            )
            for (i, t), item in zip(missing, resp.data):
                v = np.array(item.embedding, dtype=np.float32)
                cached[i] = v
                _cache_path("embeddings", _hash(config.EMBEDDING_MODEL, t)).write_text(
                    json.dumps({"v": v.tolist()})
                )
        except Exception:  # noqa: BLE001 - offline fallback
            return np.vstack([hash_embed(t) for t in texts]), "hash"

    return np.vstack([cached[i] for i in range(len(texts))]), "openai"

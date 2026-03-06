import json
import threading
from pathlib import Path

import httpx
import numpy as np

from promptshield.config import ShieldConfig

_index: np.ndarray | None = None
_metadata: list[dict] = []
_lock = threading.Lock()


async def _embed(texts: list[str], config: ShieldConfig) -> np.ndarray:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{config.provider.base_url}/embeddings",
            headers={"Authorization": f"Bearer {config.provider.api_key}"},
            json={"model": config.provider.embedding_model, "input": texts},
        )
        response.raise_for_status()
        data = response.json()
        embeddings = [item["embedding"] for item in data["data"]]
        return np.array(embeddings, dtype=np.float32)


async def _build_index(config: ShieldConfig) -> tuple[np.ndarray, list[dict]]:
    path = Path(__file__).parent.parent / "data" / "attack_patterns.json"
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    examples = data.get("embedding_examples", [])
    if not examples:
        return np.array([]), []

    texts = [ex["text"] for ex in examples]
    metadata_list = [{"threat_type": ex["category"], "id": ex["id"]} for ex in examples]

    vecs = await _embed(texts, config)

    # L2-normalize
    norms = np.linalg.norm(vecs, axis=1, keepdims=True)
    norms[norms == 0] = 1
    vecs /= norms

    return vecs, metadata_list


async def _get_index(config: ShieldConfig) -> tuple[np.ndarray, list[dict]]:
    global _index, _metadata
    if _index is None:
        with _lock:
            if _index is None:
                _index, _metadata = await _build_index(config)
    return _index, _metadata


async def scan_vector(prompt: str, config: ShieldConfig) -> tuple[str, float, str]:
    index, metadata = await _get_index(config)

    if len(index) == 0:
        return "safe", 0.0, "none"

    query_vec = (await _embed([prompt], config))[0]

    # L2-normalize query
    query_norm = np.linalg.norm(query_vec)
    if query_norm > 0:
        query_vec /= query_norm

    scores = index @ query_vec

    # top-1
    best_idx = int(np.argmax(scores))
    best_score = float(scores[best_idx])

    if best_score > config.detection.confidence_threshold:
        threat_type = metadata[best_idx]["threat_type"]
        return "blocked", best_score, threat_type

    return "safe", best_score, "none"

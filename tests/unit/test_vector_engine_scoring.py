from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from promptshield.config import ShieldConfig
from promptshield.detection.vector_engine import scan_vector


@pytest.fixture
def config():
    cfg = ShieldConfig()
    cfg.provider.api_key = "test_key"
    cfg.provider.base_url = "http://test-url"
    cfg.provider.embedding_model = "test-model"
    cfg.detection.confidence_threshold = 0.85
    return cfg


@pytest.mark.asyncio
async def test_scan_vector_uses_single_nearest_neighbor(config):
    # This test ensures we don't dilute the score with top-3
    async def mock_embed(texts, config):
        return np.array([[1.0, 0.0, 0.0]], dtype=np.float32)

    with (
        patch("promptshield.detection.vector_engine._embed", new=mock_embed),
        patch("promptshield.detection.vector_engine._get_index") as mock_get_index,
    ):
        # 1 perfect match, 2 terrible matches
        mock_index = np.array(
            [
                [1.0, 0.0, 0.0],
                [0.0, 1.0, 0.0],
                [0.0, 1.0, 0.0],
            ],
            dtype=np.float32,
        )
        mock_metadata = [
            {"threat_type": "jailbreak", "id": "1"},
            {"threat_type": "jailbreak", "id": "2"},
            {"threat_type": "jailbreak", "id": "3"},
        ]
        mock_get_index.return_value = (mock_index, mock_metadata)

        verdict, score, threat_type = await scan_vector("test prompt", config)

        # If it averages top-3, the score would be (1.0 + 0.0 + 0.0)/3 = 0.33
        # If it uses top-1, the score would be 1.0
        assert score == 1.0
        assert verdict == "blocked"


@pytest.mark.asyncio
async def test_scan_vector_blocked_on_best_score(config):
    async def mock_embed(texts, config):
        return np.array([[0.9, 0.43588989, 0.0]], dtype=np.float32)

    with (
        patch("promptshield.detection.vector_engine._embed", new=mock_embed),
        patch("promptshield.detection.vector_engine._get_index") as mock_get_index,
    ):
        mock_index = np.array([[1.0, 0.0, 0.0]], dtype=np.float32)
        mock_metadata = [{"threat_type": "injection", "id": "1"}]
        mock_get_index.return_value = (mock_index, mock_metadata)

        verdict, score, threat_type = await scan_vector("test prompt", config)
        assert verdict == "blocked"
        assert threat_type == "injection"


@pytest.mark.asyncio
async def test_scan_vector_safe_on_best_score(config):
    async def mock_embed(texts, config):
        return np.array([[0.5, 0.8660254, 0.0]], dtype=np.float32)

    with (
        patch("promptshield.detection.vector_engine._embed", new=mock_embed),
        patch("promptshield.detection.vector_engine._get_index") as mock_get_index,
    ):
        mock_index = np.array([[1.0, 0.0, 0.0]], dtype=np.float32)
        mock_metadata = [{"threat_type": "injection", "id": "1"}]
        mock_get_index.return_value = (mock_index, mock_metadata)

        verdict, score, threat_type = await scan_vector("test prompt", config)
        assert verdict == "pass"


@pytest.mark.asyncio
async def test_attack_scores_higher_than_safe_prompt(config):
    with (
        patch("promptshield.detection.vector_engine._get_index") as mock_get_index,
        patch("promptshield.detection.vector_engine._embed") as mock_embed,
    ):
        mock_index = np.array(
            [
                [1.0, 0.0, 0.0],
            ],
            dtype=np.float32,
        )
        mock_metadata = [{"threat_type": "jailbreak", "id": "1"}]
        mock_get_index.return_value = (mock_index, mock_metadata)

        async def mock_embed_attack(*args):
            return np.array([[1.0, 0.0, 0.0]], dtype=np.float32)

        mock_embed.side_effect = mock_embed_attack
        _, attack_score, _ = await scan_vector("attack", config)

        async def mock_embed_safe(*args):
            return np.array([[0.0, 1.0, 0.0]], dtype=np.float32)

        mock_embed.side_effect = mock_embed_safe
        _, safe_score, _ = await scan_vector("pass", config)

        assert attack_score > safe_score

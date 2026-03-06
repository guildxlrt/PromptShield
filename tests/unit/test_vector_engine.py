import pytest
import numpy as np
import httpx
import asyncio
import threading
from unittest.mock import patch, MagicMock
from promptshield.config import ShieldConfig
from promptshield.detection.vector_engine import _embed, _build_index, _get_index, scan_vector
import promptshield.detection.vector_engine as ve

@pytest.fixture
def config():
    cfg = ShieldConfig()
    cfg.provider.api_key = "test_key"
    cfg.provider.base_url = "http://test-url"
    cfg.provider.embedding_model = "test-model"
    cfg.detection.confidence_threshold = 0.8
    return cfg

@pytest.fixture(autouse=True)
def reset_globals():
    # Reset global state before each test
    ve._index = None
    ve._metadata = []
    if not hasattr(ve, '_index'):
        ve._index = None
    if not hasattr(ve, '_metadata'):
        ve._metadata = []
    if hasattr(ve, '_collection_cache'):
        ve._collection_cache = None

@pytest.mark.asyncio
async def test_embed_raises_on_http_error(config):
    with patch('httpx.AsyncClient.post') as mock_post:
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError("Error", request=MagicMock(), response=MagicMock())
        mock_post.return_value = mock_response
        
        with pytest.raises(httpx.HTTPStatusError):
            await _embed(["test text"], config)

@pytest.mark.asyncio
async def test_build_index_vectors_are_normalized(config):
    # Mock _embed to return unnormalized vectors
    async def mock_embed(texts, config):
        # return unnormalized vector [2.0, 0.0]
        return np.array([[2.0, 0.0]] * len(texts), dtype=np.float32)
        
    with patch('promptshield.detection.vector_engine._embed', new=mock_embed):
        index, metadata = await _build_index(config)
        assert len(index) > 0
        assert len(index) == len(metadata)
        norms = np.linalg.norm(index, axis=1)
        np.testing.assert_allclose(norms, 1.0, rtol=1e-5)

@pytest.mark.asyncio
async def test_scan_vector_blocked_above_threshold(config):
    async def mock_embed(texts, config):
        if texts == ["malicious prompt"]:
            return np.array([[1.0, 0.0, 0.0]], dtype=np.float32)
        else:
            # index
            return np.array([
                [1.0, 0.0, 0.0],
                [0.9, 0.1, 0.0],
                [0.8, 0.2, 0.0],
            ], dtype=np.float32)

    with patch('promptshield.detection.vector_engine._embed', new=mock_embed), \
         patch('promptshield.detection.vector_engine._get_index') as mock_get_index:
        
        # mock index is perfectly matching the malicious prompt
        mock_index = np.array([
            [1.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0]
        ], dtype=np.float32)
        mock_metadata = [
            {"threat_type": "jailbreak", "id": "1"},
            {"threat_type": "jailbreak", "id": "2"},
            {"threat_type": "jailbreak", "id": "3"},
            {"threat_type": "safe", "id": "4"},
        ]
        mock_get_index.return_value = (mock_index, mock_metadata)
        
        verdict, score, threat_type = await scan_vector("malicious prompt", config)
        assert verdict == "blocked"
        assert score > config.detection.confidence_threshold
        assert threat_type == "jailbreak"

@pytest.mark.asyncio
async def test_scan_vector_safe_below_threshold(config):
    with patch('promptshield.detection.vector_engine._get_index') as mock_get_index, \
         patch('promptshield.detection.vector_engine._embed') as mock_embed:
        
        mock_index = np.array([
            [0.0, 1.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 1.0, 0.0],
        ], dtype=np.float32)
        mock_metadata = [
            {"threat_type": "jailbreak", "id": "1"},
            {"threat_type": "jailbreak", "id": "2"},
            {"threat_type": "jailbreak", "id": "3"},
        ]
        mock_get_index.return_value = (mock_index, mock_metadata)
        
        async def mock_embed_func(texts, config):
            return np.array([[1.0, 0.0, 0.0]], dtype=np.float32)
        mock_embed.side_effect = mock_embed_func
        
        verdict, score, threat_type = await scan_vector("safe prompt", config)
        assert verdict == "safe"
        assert score < config.detection.confidence_threshold
        assert threat_type == "none"

@pytest.mark.asyncio
async def test_get_index_thread_safe_single_build(config):
    build_count = 0
    
    async def mock_build_index(cfg):
        nonlocal build_count
        build_count += 1
        return np.array([[1.0]], dtype=np.float32), [{"threat_type": "test", "id": "1"}]
        
    with patch('promptshield.detection.vector_engine._build_index', new=mock_build_index):
        async def worker():
            await _get_index(config)
            
        # Run multiple concurrent workers
        await asyncio.gather(*(worker() for _ in range(10)))
        
        assert build_count == 1
        assert ve._index is not None

@pytest.mark.asyncio
async def test_scan_vector_does_not_fail_open(config):
    with patch('promptshield.detection.vector_engine._get_index') as mock_get_index:
        mock_get_index.side_effect = Exception("API is down")
        
        with pytest.raises(Exception):
            await scan_vector("some prompt", config)

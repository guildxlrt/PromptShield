import json
import asyncio
import concurrent.futures
from pathlib import Path
import httpx
import chromadb
from chromadb.api.types import Documents, EmbeddingFunction, Embeddings
from typing import Tuple
from promptshield.config import ShieldConfig

class ProviderEmbeddingFunction(EmbeddingFunction):
    def __init__(self, config: ShieldConfig):
        self.config = config

    def __call__(self, input: Documents) -> Embeddings:
        if not self.config.provider.api_key or self.config.provider.api_key == "your_key_here":
            raise ValueError("API key is not configured.")

        async def fetch():
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.post(
                    f"{self.config.provider.base_url}/embeddings",
                    headers={
                        "Authorization": f"Bearer {self.config.provider.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={"model": self.config.provider.embedding_model, "input": input}
                )
                if response.status_code != 200:
                    return [[0.0]*1536 for _ in input]
                data = response.json()
                return [item["embedding"] for item in data["data"]]

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                return pool.submit(asyncio.run, fetch()).result()
        else:
            return asyncio.run(fetch())

def get_chroma_collection(config: ShieldConfig):
    client = chromadb.EphemeralClient()
    embed_fn = ProviderEmbeddingFunction(config=config)
    collection = client.get_or_create_collection(
        name="malicious_prompts",
        embedding_function=embed_fn
    )
    
    # Reseed on every start
    if collection.count() == 0:
        patterns_file = Path(__file__).parent.parent / "data" / "attack_patterns.json"
        if patterns_file.exists():
            with open(patterns_file, "r") as f:
                try:
                    data = json.load(f)
                    examples = data.get("embedding_examples", [])
                    if examples:
                        documents = [ex["text"] for ex in examples]
                        metadatas = [{"threat_type": ex["category"]} for ex in examples]
                        ids = [ex["id"] for ex in examples]
                        collection.add(
                            documents=documents,
                            metadatas=metadatas,
                            ids=ids
                        )
                except Exception as e:
                    print(f"Warning: Failed to seed ChromaDB: {e}")
                    
    return collection

_collection_cache = None

def scan_vector(prompt: str, config: ShieldConfig) -> Tuple[str, float, str]:
    """Returns (verdict, confidence, threat_type)"""
    global _collection_cache
    if _collection_cache is None:
        _collection_cache = get_chroma_collection(config)
        
    try:
        results = _collection_cache.query(
            query_texts=[prompt],
            n_results=1
        )
    except Exception:
        return "safe", 0.0, "none"
    
    if not results['distances'] or not results['distances'][0]:
        return "safe", 0.0, "none"
        
    distance = results['distances'][0][0]
    confidence = max(0.0, 1.0 - distance)
    
    if confidence > config.detection.confidence_threshold:
        threat_type = results['metadatas'][0][0].get('threat_type', 'jailbreak')
        return "blocked", confidence, threat_type
        
    return "safe", confidence, "none"

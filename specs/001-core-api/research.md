# ⚠️ SUPERSEDED – ARCHITECTURAL PIVOT (2025)

**This specification describes the original cloud-hosted SaaS plan.**  
**It was abandoned in favor of a local-first Python library (see spec-002).**  
**Most functional requirements listed here were never implemented.**

---

# Research: PromptShield API Core Endpoints

**Status**: SUPERSEDED (see spec-002 for current implementation)

**HISTORICAL NOTE**: This research predates the architectural pivot. The vector store decision documented below (ChromaDB) was subsequently replaced with a NumPy brute-force implementation in spec-003. The multi-tenant billing and authentication architecture was entirely abandoned.

## Phase 0: Outline & Research

### 1. Vector Database Integration (Local ChromaDB)
- **Decision**: Use `chromadb` with a custom embedding function calling OpenRouter's embedding endpoint (`openai/text-embedding-3-small`).
- **Rationale**: Free tier memory limits on Render/Railway make local models (like `sentence-transformers`) non-viable. Calling a remote embedding API keeps the memory footprint minimal while maintaining the < $50 monthly budget constraint.
- **Alternatives considered**: sentence-transformers (rejected due to memory limits), FAISS (too low-level), Pinecone (expensive).

### 2. LLM Fallback (OpenRouter API)
- **Decision**: Use `httpx` to make async calls to OpenRouter using a fast, cheap model (e.g., `meta-llama/llama-3-8b-instruct` or a similar <$0.10/1M token model) as a fallback when confidence is < 0.6.
- **Rationale**: OpenRouter allows dynamic model swapping without changing API integration code. Async calls ensure the FastAPI loop is not blocked during the < 2s response window.
- **Alternatives considered**: OpenAI direct (more expensive, vendor lock-in), local LLM execution (impossible on Free Tier Render/Railway due to memory limits).

### 3. Rate Limiting Strategy
- **Decision**: Implement a lightweight in-memory sliding window or token bucket rate limiter tied to the `api_key`. Since it's a single endpoint running on a free tier, an external Redis cache is unnecessary.
- **Rationale**: Keeps architecture simple and fits within budget. State can be kept in Python dictionaries (with an expiration sweep) or via a minimal SQLite-backed rate limiter if persistence is needed across restarts. We will use an in-memory dictionary with timestamp cleanup.
- **Alternatives considered**: Redis (requires external hosting, cost/complexity), PostgreSQL (too much overhead for rate limits).

# ⚠️ SPEC-001 IS SUPERSEDED

All files in this directory describe the **original cloud-hosted SaaS architecture** that was abandoned in early 2025.

## What Changed

| Aspect | Original Plan (spec-001) | Current Implementation (spec-002) |
|--------|--------------------------|-----------------------------------|
| **Architecture** | Multi-tenant cloud API | Self-hosted Python library |
| **Deployment** | FastAPI server on Render/Railway | Local machine, zero infrastructure |
| **Authentication** | API keys + SQLite user table | None (local-only) |
| **Billing** | Stripe integration | None |
| **Rate Limiting** | Token bucket per API key | None |
| **Database** | SQLite with HMAC-hashed emails | None |
| **User Signup** | `/auth/register` endpoint | None |
| **Vector Store** | ChromaDB (then NumPy in spec-003) | NumPy only |

## Which Files Are Relevant?

- ✅ **spec.md, data-model.md** — Read for historical context on the core detection pipeline design (Regex → Vector → LLM cascade)
- ✅ **plan.md** — Read to understand the original vision and why it pivoted
- ⚠️ **quickstart.md** — **OUTDATED** — See README.md in the project root for current usage
- ⚠️ **research.md** — **OUTDATED** — ChromaDB was replaced by NumPy in spec-003
- ⚠️ **tasks.md** — **OUTDATED** — Billing, auth, and rate limiting phases were abandoned

## What to Read Instead

For the **current, implemented architecture**, see:

1. **[specs/002-cli-tool/](../002-cli-tool/)** — The actual spec for the Python library, CLI, and local server
2. **[README.md](../../README.md)** — User-facing quickstart and feature overview
3. **[specs/003-vector-engine-refactor/](../003-vector-engine-refactor/)** — How ChromaDB was replaced with NumPy
4. **[specs/004-vector-engine-scoring/](../004-vector-engine-scoring/)** — Top-1 nearest neighbor scoring

## Why Did This Pivot?

**Original plan**: Build a cloud API with billing, user accounts, and rate limiting. High infrastructure cost, complex multi-tenant data isolation, operational overhead.

**New plan**: Build a self-hosted Python library. Zero infrastructure, zero cost, zero data sharing, zero operational complexity. Much better fit for a security tool.

The core detection pipeline (regex → embedding → LLM fallback) survived the pivot intact. Only the infrastructure, billing, and authentication layers were removed.

## Quick Reference: What Was Scrapped

- ❌ `/billing/checkout`, `/billing/webhook`, `/billing/status` — Stripe integration
- ❌ `/auth/register` — User signup endpoint
- ❌ SQLite `accounts` table — User database
- ❌ HMAC-SHA256 email hashing — User data privacy
- ❌ Token bucket rate limiter — Free tier (10 req/min, 1k scans/mo) and Paid tier (100 req/min, 50k scans/mo)
- ❌ `api_key` field in ScanRequest — Authentication
- ❌ Audit logging infrastructure — No persistent request log

## Quick Reference: What Survived

- ✅ Regex detection engine — Layer 1
- ✅ Vector similarity engine — Layer 2 (NumPy instead of ChromaDB)
- ✅ LLM fallback engine — Layer 3
- ✅ ScanResponse schema — verdict, threat_type, confidence, reason, sanitized_prompt, pipeline_layer, scan_id
- ✅ Latency SLOs — <500ms for regex/embedding, <2s for LLM fallback
- ✅ Multi-interface support — Python library + CLI + local HTTP server

---

**Bottom line**: If you're looking for information about billing, user accounts, or cloud deployment, this spec is historical. For everything else, start with spec-002.
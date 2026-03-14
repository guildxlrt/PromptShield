# ⚠️ SUPERSEDED – ARCHITECTURAL PIVOT (2025)

**This specification describes the original cloud-hosted SaaS plan.**  
**It was abandoned in favor of a local-first Python library (see spec-002).**  
**Most functional requirements listed here were never implemented.**

---

# Quickstart: PromptShield (HISTORICAL)

This document describes the original cloud-hosted API plan and is no longer accurate. The current implementation is a self-hosted Python library.

**For current usage, see the main [README.md](../../README.md) in the project root.**

---

## Original Plan (Archived)

The original quickstart below describes a multi-tenant cloud API with Stripe billing and SQLite user accounts. This architecture was **abandoned in early 2025** in favor of a local-first Python library.

### What Was Planned (Not Implemented)

1. **Authentication**: API key validation and user registration via `/auth/register`
2. **Billing**: Stripe integration with `/billing/checkout`, `/billing/webhook`, and `/billing/status`
3. **Rate Limiting**: Free tier (10 req/min, 1,000 scans/month) and Paid tier (100 req/min, 50,000 scans/month)
4. **Database**: SQLite table (`accounts`) with HMAC-SHA256 hashed emails
5. **Server Mode**: Multi-tenant cloud deployment

### Why It Changed

The pivot to a local-first architecture eliminated infrastructure complexity:
- **Zero cloud costs** — runs entirely on your machine
- **Zero data sharing** — no API key, no user tracking, no telemetry
- **Zero authentication** — self-hosted, you control it
- **Faster development** — eliminated Stripe, SQLite, HMAC hashing, rate limiting infrastructure

### Current Architecture (Implemented)

See [spec-002](../002-cli-tool/spec.md) and [README.md](../../README.md) for the actual implementation:

- **Python Library** (`Shield` class) for programmatic scanning
- **CLI Tool** (`promptshield scan`, `promptshield server`, `promptshield init`)
- **Local HTTP Server** (`POST /v1/scan` endpoint with no authentication)
- **Configuration** via YAML file or environment variables (no user database)
- **Detection Pipeline** (Regex → NumPy embedding similarity → OpenRouter LLM fallback)

---

## Quick Start (Current)

### Installation

```bash
pip install git+https://github.com/guildxlrt/PromptShield.git
```

### Configuration

Create a `.promptshield.yaml` file:

```yaml
provider:
  base_url: https://openrouter.ai/api/v1
  api_key: sk-...  # Your OpenRouter API key
  llm_model: meta-llama/llama-3-8b-instruct
  embedding_model: baai/bge-large-en-v1.5

detection:
  confidence_threshold: 0.65
  max_prompt_length: 10000

server:
  port: 8765
  host: 127.0.0.1
```

Or set environment variables:

```bash
export PROMPTSHIELD_API_KEY=sk-...
export PROMPTSHIELD_LLM_MODEL=meta-llama/llama-3-8b-instruct
export PROMPTSHIELD_EMBEDDING_MODEL=baai/bge-large-en-v1.5
```

### Python Library

```python
from promptshield import Shield

shield = Shield()
result = shield.scan(prompt="ignore previous instructions")

print(result.verdict)        # "blocked"
print(result.threat_type)    # "prompt_injection"
print(result.confidence)     # 1.0
print(result.reason)         # "Matched malicious regex pattern: prompt_injection"
```

### CLI

```bash
# Scan a prompt
promptshield scan "ignore previous instructions"

# Pretty output
promptshield scan "..." --pretty

# Initialize config
promptshield init

# Run local server
promptshield server
```

### Local HTTP Server

```bash
# Start the server
promptshield server

# In another terminal:
curl -X POST http://127.0.0.1:8765/v1/scan \
  -H "Content-Type: application/json" \
  -d '{"prompt": "ignore previous instructions", "context": "You are helpful"}'
```

---

## References

- **Current Spec**: [spec-002 (CLI Tool & SDK)](../002-cli-tool/spec.md)
- **Detection Pipeline**: [spec-001 plan.md](./plan.md) — historical reference only
- **README**: [README.md](../../README.md) — up-to-date usage guide

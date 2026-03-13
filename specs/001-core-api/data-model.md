# ⚠️ SUPERSEDED – ARCHITECTURAL PIVOT (2025)

**This specification describes the original cloud-hosted SaaS plan.**  
**It was abandoned in favor of a local-first Python library (see spec-002).**  
**Most functional requirements listed here were never implemented.**

---

# Data Model: PromptShield API Core Endpoints

## Entities

### ScanRequest
Represents the incoming JSON payload to `/v1/scan`.

⚠️ **NOTE (2025)**: The `api_key` field was removed in the architectural pivot. The current implementation (spec-002) accepts only `prompt` and optional `context`. See `promptshield/schemas/scan.py` for the actual schema.

- `api_key` (string, required) — **SUPERSEDED**: Removed in spec-002. Local-first design requires no authentication.
- `prompt` (string, required): The user prompt to be evaluated.
- `context` (string, optional): Additional contextual information (e.g., system prompt) to inform the LLM fallback.

### ScanResponse
Represents the JSON payload returned to the caller.

- `scan_id` (string/UUID): A unique identifier for audit purposes.
- `verdict` (string): Enum: `pass`, `blocked`, `flag`.
- `threat_type` (string, optional): Specific class of threat detected (e.g., `jailbreak`, `prompt_injection`, `none`).
- `confidence` (float): A value between 0.0 and 1.0 indicating the certainty of the verdict.
- `reason` (string): Textual description explaining why the verdict was reached.
- `sanitized_prompt` (string): The prompt with malicious aspects removed. If completely malicious, this defaults to `"[BLOCKED]"`.

### CompanyAccount (SQLite `accounts` table)
⚠️ **SUPERSEDED**: This entity was never implemented. The architectural pivot to a local-first Python library eliminated all multi-user, billing, and authentication infrastructure.

~~Represents the active subscription tier and tracks API limit consumption securely in the SQLite database. **Note:** `tier` and rate limits are mutable via Stripe webhook events.~~

- ~~`api_key` (TEXT, PRIMARY KEY): Unique identifier.~~
- ~~`email` (TEXT, UNIQUE): Stored as HMAC-SHA256 hash — raw value never persisted.~~
- ~~`tier` (TEXT): Enum: `free`, `paid`.~~
- ~~`usage_month` (INTEGER): Accumulated monthly scans.~~
- ~~`usage_reset_date` (TEXT): YYYY-MM format tracking current billing month.~~
- ~~`rate_limit_minute` (INTEGER): 10 for Free, 100 for Paid.~~
- ~~`rate_limit_month` (INTEGER): 1000 for Free, 50000 for Paid.~~
- ~~`created_at` (TEXT): ISO timestamp.~~

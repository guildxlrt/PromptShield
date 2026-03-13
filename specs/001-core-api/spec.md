# ⚠️ SUPERSEDED – ARCHITECTURAL PIVOT (2025)

**This specification describes the original cloud-hosted SaaS plan.**
**It was abandoned in favor of a local-first Python library (see spec-002).**
**Most functional requirements listed here were never implemented.**

---

# Feature Specification: PromptShield API Core Endpoints

**Feature Branch**: `001-core-api`  
**Created**: 2026-03-01  
**Status**: SUPERSEDED (see spec-002 for current implementation)  
**Input**: User description: "PromptShield is a security checkpoint for LLM applications. Developers call it before sending user prompts to any LLM. It detects malicious inputs and returns a structured verdict."

**ARCHITECTURAL NOTE**: This spec originally proposed a multi-tenant cloud API with Stripe billing, SQLite user accounts, and HMAC-hashed email storage. In early 2025, the project pivoted to a self-hosted, single-machine Python library with zero infrastructure requirements. Spec-002 ("CLI Tool & SDK") documents the current, implemented architecture. Requirements FR-002, FR-009–FR-017 (billing, auth, rate limiting, email hashing) were abandoned. Only the core detection pipeline (FR-001, FR-003–FR-006) and its latency SLOs survive in spec-002.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Scan API Integration (Priority: P1)

Developers integrate the scan endpoint into their application backend to filter out malicious prompts before forwarding them to their LLM.

**Why this priority**: This is the core functionality. Without the ability to scan prompts and receive a verdict, the product does not exist.

**Independent Test**: Can be fully tested by sending a POST request to `/v1/scan` with a valid API key and an evaluation prompt, and receiving a valid JSON verdict.

**Acceptance Scenarios**:

1. **Given** a developer with a valid API key, **When** they send a pass prompt, **Then** the API returns a verdict of "pass" within 500ms.
2. **Given** a developer with a valid API key, **When** they send an obvious prompt injection attempt (e.g. "ignore previous instructions"), **Then** the API returns a verdict of "blocked" with a threat_type and reason within 500ms.
3. **Given** a developer with a valid API key, **When** they send an ambiguous prompt, **Then** the API routes it to the LLM analyzer and returns a verdict within 2 seconds.

---

### Edge Cases

- **Payload Size**: System MUST reject prompts exceeding 10,000 characters with a 422 Unprocessable Entity error.
- **Provider Timeout**: If OpenRouter API times out (5s limit), system MUST return a `flag` verdict with `confidence: 0.5` and `reason: "Detection provider timeout"`.
- **Vector Search Failure**: If ChromaDB returns zero results, the pipeline MUST proceed to the LLM fallback if regex analysis is inconclusive.
- **API Security**: The `sanitized_prompt` field MUST contain `"[BLOCKED]"` when a prompt is determined to be completely malicious.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST expose a `POST /v1/scan` endpoint.
- **FR-002**: System MUST accept a JSON payload with `api_key`, `prompt`, and optional `context`.
- **FR-003**: System MUST return a structured JSON response containing `verdict` (pass, blocked, flag), `threat_type`, `confidence`, `reason`, `sanitized_prompt`, and `scan_id`.
- **FR-004**: System MUST evaluate prompts against a regex/pattern matching engine first.
- **FR-005**: System MUST evaluate prompts against a semantic embedding similarity engine against known attack vectors.
- **FR-006**: System MUST evaluate prompts using an external LLM call if the previous steps yield a confidence below 0.6.
- **FR-007**: System MUST log every scan interaction with `scan_id`, timestamp, `verdict`, and `threat_type` for audit trails.
- **FR-008**: System MUST dogfood its own API to protect itself from malicious inputs.
- **FR-009**: System MUST enforce Free tier limits of 1,000 scans/month and 10 req/minute using a **Token Bucket** algorithm.
- **FR-010**: System MUST enforce Paid tier limits of 50,000 scans/month and 100 req/minute using a **Token Bucket** algorithm. Billing is strictly usage-tracking only for v1; no external payment provider integration.
- **FR-011**: System MUST manage regex and embedding attack vectors effectively. Patterns MUST be loaded from a local configuration file or ChromaDB on startup.
- **FR-012**: System MUST set `sanitized_prompt` to `"[BLOCKED]"` when a prompt is determined to be completely malicious.
- **FR-013**: System MUST expose a `POST /billing/checkout` endpoint to create a Stripe checkout session for a given `api_key`.
- **FR-014**: System MUST expose a `POST /billing/webhook` endpoint to receive Stripe webhook events, verify signatures, and upgrade the account to "paid" on `checkout.session.completed`.
- **FR-015**: System MUST expose a `GET /billing/status` endpoint to return the current subscription tier and usage information for an `api_key`.
- **FR-016**: System MUST expose a `POST /auth/register` endpoint to accept an email, validate it, insert a new user into the SQLite database, and instantly return a generated free tier API key.
- **FR-017**: System MUST hash all emails using HMAC-SHA256 with a secret pepper before persistence. Raw email MUST NOT be written to disk, logged, or returned in any API response.
- **FR-018**: The LLM detection engine (`scan_llm()`) MUST instruct the LLM to provide a mandatory `reason` field in its JSON response via the system prompt. The engine MUST extract the `reason` field from the LLM's JSON response and return it as the 4th element of a 4-tuple: `(verdict, confidence, threat_type, reason)`. The reason MUST be propagated through the detection pipeline to populate the `ScanResponse.reason` field. The system prompt MUST explicitly require that the reason field is never empty and must explain the verdict in a concise manner.
- **FR-019**: The LLM system prompt MUST instruct the LLM to respond with valid JSON using only double quotes (not single quotes). The system prompt MUST include an example JSON object with escaped double quotes to demonstrate the required format. This ensures that the LLM's JSON response can be successfully parsed by Python's `json.loads()` without errors.

### Key Entities

- **Scan Request**: Represents an incoming analysis job containing the raw prompt, optional context, and the calling company's API key.
- **Verdict Report**: The structured analysis result containing the threat assessment, confidence score, and remediation details.
- **Company Account**: Represents a registered entity, tracking their allocated API key, active subscription tier, and monthly scan consumption.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: API responds to standard regex/embedding evaluated prompts in under 500ms (**P95 latency**).
- **SC-002**: API responds to prompts requiring LLM evaluation in under 2000ms (**P95 latency**).
- **SC-003**: System detects known jailbreak attempts with a confidence of >0.9 using the local embedding pipeline.
- **SC-004**: System successfully enforces rate limits strictly blocking requests beyond 10 req/min (Free) and 100 req/min (Paid).
- **SC-005**: The `ScanResponse.reason` field is always populated with a non-empty string describing why the verdict was reached, either from the detection layer or the LLM.
- **SC-006**: 100% of LLM responses are successfully parsed by `json.loads()` without JSON decoding errors, confirming valid JSON formatting with double quotes.
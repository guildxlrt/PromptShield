# API Contract: PromptShield Core

## POST /auth/register
Generates a new free-tier API key instantly via a self-serve email registration flow.

**Request Header**:
`Content-Type: application/json`

**Request Body**:
```json
{
  "email": "string (Required: Valid email address)"
}
```

**Response Body (200 OK)**:
```json
{
  "api_key": "string (Generated API key starting with 'ps_free_')",
  "tier": "free",
  "message": "string"
}
```

**Error Responses**:
- `409 Conflict`: Email already registered.
- `422 Unprocessable Entity`: Invalid email format.

## POST /v1/scan
Endpoint to scan a user prompt for malicious intent.

**Request Header**:
`Content-Type: application/json`

**Request Body**:
```json
{
  "api_key": "string (Required: e.g. ps_live_123456789)",
  "prompt": "string (Required: The raw prompt text to scan)",
  "context": "string (Optional: Provide system instructions to help LLM evaluation)"
}
```

**Response Body (200 OK)**:
```json
{
  "scan_id": "string (UUID v4)",
  "verdict": "string (Enum: 'pass', 'blocked', 'flag')",
  "threat_type": "string (e.g. 'jailbreak', 'prompt_injection', or 'none')",
  "confidence": 0.95,
  "reason": "string (Explanation of the verdict)",
  "sanitized_prompt": "string (The prompt, or '[BLOCKED]' if fully malicious)"
}
```

**Error Responses**:
- `401 Unauthorized`: Invalid or missing `api_key`.
- `429 Too Many Requests`: Exceeded minute/monthly rate limits.
- `422 Unprocessable Entity`: Missing required `prompt` field.

## POST /billing/checkout
Creates a Stripe checkout session for a given API key to upgrade to the paid tier.

**Request Header**:
`Content-Type: application/json`

**Request Body**:
```json
{
  "api_key": "string",
  "tier": "paid"
}
```

**Response Body (200 OK)**:
```json
{
  "checkout_url": "string (Stripe checkout session URL)"
}
```

## POST /billing/webhook
Receives Stripe webhook events to upgrade user tiers upon successful payment.

**Request Header**:
`stripe-signature`: "string (Signature for verification)"

**Response Body (200 OK)**:
```json
{
  "status": "ok"
}
```

## GET /billing/status
Retrieves the current billing tier and usage limits for a given API key.

**Query Parameter**:
`api_key`: string (Required)

**Response Body (200 OK)**:
```json
{
  "tier": "string (e.g. 'free' or 'paid')",
  "usage_month": 0,
  "rate_limit_minute": 100,
  "rate_limit_month": 50000
}
```

# Quickstart: PromptShield API

## Setup

1. **Clone and Install**
   Install dependencies (preferably using a virtual environment):
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install fastapi uvicorn chromadb httpx pydantic pydantic-settings
   ```

2. **Configuration**
   Set up your environment variables (`.env` file):
   ```env
   OPENROUTER_API_KEY=your_openrouter_key
   LLM_MODEL=meta-llama/llama-3-8b-instruct
   EMAIL_PEPPER=your_secret_pepper_here
   ```

3. **Run the API**
   ```bash
   uvicorn src.api.main:app --reload
   ```

## Integration

Use PromptShield as a middleware before forwarding queries to your internal LLM.

```python
import httpx

async def safe_llm_query(api_key: str, user_prompt: str):
    # 1. Ask PromptShield for a verdict
    response = httpx.post(
        "http://localhost:8000/v1/scan",
        json={"api_key": api_key, "prompt": user_prompt}
    )
    result = response.json()
    
    # 2. Halt or proceed
    if result["verdict"] == "blocked":
        raise Exception(f"Prompt blocked: {result['reason']}")
    
    # 3. Proceed with sanitized prompt
    print(f"Executing: {result['sanitized_prompt']}")
```

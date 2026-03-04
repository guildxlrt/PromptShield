from fastapi import FastAPI, HTTPException
from promptshield import Shield, ShieldConfig, ScanRequest, ScanResponse

app = FastAPI(
    title="PromptShield Server", 
    version="2.0.0",
    description="Local security tool protecting LLM applications from prompt injection and jailbreak attempts."
)

config = ShieldConfig.load()
shield = Shield(config=config)

@app.post("/v1/scan", response_model=ScanResponse)
def scan_endpoint(request: ScanRequest):
    """
    Dogfooding: The server mode runs the exact same detection pipeline
    to scan the incoming prompt.
    """
    try:
        result = shield.scan(prompt=request.prompt, context=request.context)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health_check():
    return {"status": "ok"}

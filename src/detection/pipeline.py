from typing import Any, Dict, Optional

from src.config import ShieldConfig
from src.detection.llm_engine import scan_llm
from src.detection.regex_engine import scan_regex
from src.detection.vector_engine import scan_vector


async def run_pipeline(
    prompt: str, config: ShieldConfig, context: Optional[str] = None
) -> Dict[str, Any]:
    # 1. Regex Match (instant, free)
    verdict, confidence, threat = scan_regex(prompt)
    if verdict == "blocked":
        return {
            "verdict": "blocked",
            "confidence": 1.0,
            "threat_type": threat,
            "reason": f"Matched malicious regex pattern: {threat}",
            "sanitized_prompt": "[BLOCKED]",
            "pipeline_layer": "regex",
        }

    # 2. Vector Similarity (fast, local)
    verdict, confidence, threat = await scan_vector(prompt, config)
    if verdict == "blocked" and confidence > config.detection.confidence_threshold:
        return {
            "verdict": "blocked",
            "confidence": confidence,
            "threat_type": threat,
            "reason": f"Semantic similarity to known attack vector: {threat}",
            "sanitized_prompt": "[BLOCKED]",
            "pipeline_layer": "embedding",
        }

    # 3. LLM Fallback (expensive, slow) - if confidence is low (< threshold)
    if confidence < config.detection.confidence_threshold:
        verdict, llm_conf, threat, reason = await scan_llm(prompt, config, context)
        return {
            "verdict": verdict,
            "confidence": llm_conf,
            "threat_type": threat,
            "reason": reason
            if reason and reason.strip()
            else f"LLM evaluation result: {verdict}",
            "sanitized_prompt": "[BLOCKED]" if verdict == "blocked" else prompt,
            "pipeline_layer": "llm",
        }

    # Otherwise return pass
    return {
        "verdict": "pass",
        "confidence": confidence,
        "threat_type": "none",
        "reason": "No malicious patterns detected",
        "sanitized_prompt": prompt,
        "pipeline_layer": "embedding",
    }

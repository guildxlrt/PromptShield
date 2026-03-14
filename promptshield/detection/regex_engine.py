import json
import re
from pathlib import Path
from typing import Tuple

PATTERNS = []


def load_patterns():
    global PATTERNS
    if not PATTERNS:
        patterns_file = Path(__file__).parent.parent / "data" / "attack_patterns.json"
        if patterns_file.exists():
            try:
                with open(patterns_file, "r") as f:
                    data = json.load(f)
                    for item in data.get("regex_patterns", []):
                        flags = (
                            re.IGNORECASE if item.get("flags") == "IGNORECASE" else 0
                        )
                        PATTERNS.append(
                            (item.get("pattern"), item.get("category"), flags)
                        )
            except Exception as e:
                print(f"Warning: Failed to load regex patterns: {e}")


def scan_regex(prompt: str) -> Tuple[str, float, str]:
    """Returns (verdict, confidence, threat_type)"""
    load_patterns()
    for pattern, threat_type, flags in PATTERNS:
        if re.search(pattern, prompt, flags):
            return "blocked", 1.0, threat_type

    return "pass", 0.0, "none"

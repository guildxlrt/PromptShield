import os
import yaml
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import BaseModel, Field

class ProviderConfig(BaseModel):
    base_url: str = "https://openrouter.ai/api/v1"
    api_key: str = ""
    llm_model: str = "meta-llama/llama-3-8b-instruct"
    embedding_model: str = "openai/text-embedding-3-small"

class DetectionConfig(BaseModel):
    confidence_threshold: float = 0.6
    max_prompt_length: int = 10000

class ServerConfig(BaseModel):
    port: int = 8765
    host: str = "127.0.0.1"

class ShieldConfig(BaseSettings):
    provider: ProviderConfig = Field(default_factory=ProviderConfig)
    detection: DetectionConfig = Field(default_factory=DetectionConfig)
    server: ServerConfig = Field(default_factory=ServerConfig)

    @classmethod
    def load(cls) -> "ShieldConfig":
        config_path = Path(".promptshield.yaml")
        yaml_data = {}
        if config_path.exists():
            with open(config_path, "r") as f:
                yaml_data = yaml.safe_load(f) or {}

        config = cls(**yaml_data)

        # Environment variable overrides
        if "PROMPTSHIELD_API_KEY" in os.environ:
            config.provider.api_key = os.environ["PROMPTSHIELD_API_KEY"]
        if "PROMPTSHIELD_BASE_URL" in os.environ:
            config.provider.base_url = os.environ["PROMPTSHIELD_BASE_URL"]
        if "PROMPTSHIELD_LLM_MODEL" in os.environ:
            config.provider.llm_model = os.environ["PROMPTSHIELD_LLM_MODEL"]
        if "PROMPTSHIELD_EMBEDDING_MODEL" in os.environ:
            config.provider.embedding_model = os.environ["PROMPTSHIELD_EMBEDDING_MODEL"]

        return config


from __future__ import annotations

from pydantic import SecretStr
from pydantic_settings import BaseSettings,SettingsConfigDict

class Settings(BaseSettings):

    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", 
                                      env_file_encoding="utf-8",
                                      case_sensitive=False)

    # Database settings
    TENANT_ID: SecretStr
    CLIENT_ID: SecretStr
    CLIENT_SECRET: SecretStr
    DEV_WORKSPACE: str = "Dev"
    PROD_WORKSPACE: str = "Prod"
    POWER_BI_BASE_URL : str = "https://api.powerbi.com/v1.0/myorg"


    # API KEY
    OPENAI_API_KEY: SecretStr
    openai_llm_model: str = "gpt-4o"

    # Embedding settings
    EMBEDDING_PROVIDER: str = "openai"
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    EMBEDDING_DIMENSIONS: int = 1536

     # 📂 Temp
    TEMP_DIR: str = "/tmp/temp"

    # ⏱️ Polling
    IMPORT_TIMEOUT: int = 300
    POLL_INTERVAL: int = 5

     # API server
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_workers: int = 1
    BASE_URL: str = "https://powerbi-n7h5.onrender.com" #"http://localhost:8000"

_settings : Settings | None = None

def get_settings() -> Settings:

    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings

if __name__ == "__main__":
    settings = get_settings()
    print(settings.model_dump())
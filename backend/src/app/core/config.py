from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Clinical RAG Assistant"
    environment: str = "development"
    database_url: str = "postgresql+asyncpg://clinical_app:clinical_app_password@localhost:5432/clinical_rag"
    backend_cors_origins: str = "http://localhost:5173"

    jwt_secret_key: str = Field(default="change-this-in-production")
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    openai_api_key: str | None = None
    openai_chat_model: str = "gpt-4.1-mini"
    openai_embedding_model: str = "text-embedding-3-small"
    embedding_provider: str = "deterministic"
    llm_provider: str = "deterministic"

    rag_top_k: int = 8
    rag_min_score: float = 0.35
    max_upload_mb: int = 25

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.backend_cors_origins.split(",") if origin.strip()]


settings = Settings()

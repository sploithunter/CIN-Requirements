from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    # App
    app_name: str = "Conversational Requirements API"
    debug: bool = False

    # Database
    database_url: str

    # Redis
    redis_url: str = "redis://localhost:6379"

    # Auth
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7

    # OAuth
    google_client_id: str = ""
    google_client_secret: str = ""
    microsoft_client_id: str = ""
    microsoft_client_secret: str = ""
    oauth_redirect_uri: str = "http://localhost:3000/auth/callback"

    # Claude / AI
    anthropic_api_key: str
    claude_model: str = "claude-haiku-4-5-20251001"  # Haiku 4.5 - fast & cheap ($1/$5 per MTok)
    claude_model_heavy: str = "claude-sonnet-4-5-20250929"  # Sonnet 4.5 for complex tasks
    max_tokens_per_session: int = 100000

    # Optional: Other AI providers
    openai_api_key: str = ""
    gemini_api_key: str = ""

    # Storage (R2/S3)
    s3_endpoint_url: str
    s3_access_key: str
    s3_secret_key: str
    s3_bucket_name: str

    # Liveblocks
    liveblocks_secret_key: str

    model_config = SettingsConfigDict(env_file=".env")


@lru_cache
def get_settings() -> Settings:
    return Settings()

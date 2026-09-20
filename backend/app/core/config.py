from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql://iaa_user:changeme@localhost:5432/interview_assist_agent"
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "changeme"
    minio_secret_key: str = "changeme"
    minio_bucket: str = "iaa-files"
    anthropic_api_key: str = ""
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"
    llm_provider: str = "mock"
    jwt_secret: str = "changeme"
    jwt_expire_minutes: int = 30
    refresh_token_expire_days: int = 30
    env: str = "development"
    redis_url: str = "redis://localhost:6379/0"
    # Danh sách origin được phép gọi API - phân cách bằng dấu phẩy trong .env.
    # VD production: ALLOWED_ORIGINS=https://ngdinhthuy.duckdns.org
    allowed_origins: str = "http://localhost:5173"

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        """Loại bỏ khoảng trắng thừa khi admin nhập biến môi trường."""
        return v.strip()

    @property
    def cors_origins(self) -> list[str]:
        """Trả về list origin sạch để truyền cho CORSMiddleware."""
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]


settings = Settings()
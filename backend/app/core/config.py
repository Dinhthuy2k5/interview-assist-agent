from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql://iaa_user:changeme@localhost:5432/interview_assist_agent"
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "changeme"
    minio_secret_key: str = "changeme"
    minio_bucket: str = "iaa-files"
    anthropic_api_key: str = ""
    jwt_secret: str = "changeme"
    jwt_expire_minutes: int = 60
    env: str = "development"
    llm_provider: str = "mock"   # "mock" | "anthropic" | "groq"
    groq_api_key: str = ""


settings = Settings()
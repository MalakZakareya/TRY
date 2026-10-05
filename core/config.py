from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Agentic AI"
    DESCRIPTION: str = "Starter Agentic AI application with a file upload interface."
    VERSION: str = "0.1.0"

    HOST: str = "127.0.0.1"
    PORT: int = 8001
    DEBUG: bool = True
    CORS_ORIGINS: list[str] = ["*"]
    UPLOAD_DIR: str = "uploads"

    # OpenAI
    OPENAI_API_KEY: str = ""

    # Test Mode
    TEST_MODE: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )


settings = Settings()
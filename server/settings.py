from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "Hyperindex"
    DEBUG: bool = True
    DATABASE_URL: str = "sqlite:///./server/db/hyperindex.db"
    SECRET_KEY: str = "super-secret-key-change-me"  # Default if not in env
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 1 week

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()

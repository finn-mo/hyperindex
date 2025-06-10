from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables or .env file.

    Attributes:
        PROJECT_NAME (str): Name of the application.
        DEBUG (bool): Enables debug mode when True.
        DATABASE_URL (str): SQLAlchemy database URL for the application database.
        SECRET_KEY (str): Secret key used to sign JWTs. Hardcoded fallback is used for testing; override via .env.
        ALGORITHM (str): JWT signing algorithm (default: HS256).
        ACCESS_TOKEN_EXPIRE_MINUTES (int): Lifetime of access tokens in minutes (default: 1 week).

    Notes:
        Use a secure SECRET_KEY in production by setting it in the .env file.
        The hardcoded fallback should only be used during development or testing.
    """

    PROJECT_NAME: str = "Hyperindex"
    DEBUG: bool = True
    DATABASE_URL: str = "sqlite:///./server/db/hyperindex.db"
    SECRET_KEY: str = "super-secret-key-change-me"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 1 week

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )

settings = Settings()
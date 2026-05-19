from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    SERVER_LISTEN_IP: str = "0.0.0.0"
    SERVER_LISTEN_PORT: int = 8000
    SERVER_WORKERS: int = 1
    PRODUCTION: bool = False

    APP_NAME: str = "MyApp"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    CORS_ORIGINS: List[str] = ["*"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["*"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]

    DATABASE_URL: str = "mysql+aiomysql://user:pass@localhost:3306/mydb"

    LOG_LEVEL: str = "INFO"
    SYSLOG_HOST: str = "localhost"
    SYSLOG_PORT: int = 514

    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    SEED_ADMIN_EMAIL: str = "admin@example.com"
    SEED_ADMIN_USERNAME: str = "admin"
    SEED_ADMIN_FULLNAME: str = "System Administrator"
    SEED_ADMIN_PASSWORD: str = "Admin1234"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
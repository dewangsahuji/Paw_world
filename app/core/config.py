
from pydantic import BaseSettings, AnyUrl

class Settings(BaseSettings):
    app_env: str = "development"
    debug: bool = True
    database_url: str = "postgresql+asyncpg://app:password@postgres:5432/pawworld"
    redis_url: str = "redis://redis:6379/0"
    mongo_url: str = "mongodb://mongo:27017"
    elasticsearch_url: AnyUrl = "http://elastic:9200"
    secret_key: str = "changeme"

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()

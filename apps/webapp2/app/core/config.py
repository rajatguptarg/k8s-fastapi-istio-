from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "WebApp2"
    environment: str = "dev"
    debug: bool = True

    webapp1_base_url: str = "http://webapp1.default.svc.cluster.local"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    return Settings()

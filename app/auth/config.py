from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    jwt_private_key: str
    jwt_public_key: str
    jwt_algorithm: str
    access_token_expire_minutes: int
    refresh_token_expire_days: int

    postgres_user: str
    postgres_password: str
    postgres_db: str

    db_host: str
    db_port: int

    database_url: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()

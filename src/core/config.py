from pathlib import Path

from pydantic import AliasChoices, Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_FILE = f"{Path(__file__).resolve().parent.parent.parent}/.env"

DEFAULT_HOSTS = [
    "http://127.0.0.1:3000",
    "http://localhost:3000",
]

class CorsConfig(BaseSettings):
    allowed_hosts: str | list = []
    allowed_hosts_regex: str = r"^http://(localhost|127\.0\.0\.1):[1-9][0-9]{3}$" # TODO В прод помнять
    allowed_credentials: bool = True
    allowed_methods: str = "*"
    allowed_headers: str | list = ["*"]

    @field_validator("allowed_hosts", mode="before", check_fields=False)
    @classmethod
    def split_allowed_hosts(cls, value):
        if isinstance(value, str):
            lst = value.split(",")
            lst.extend(DEFAULT_HOSTS)
            return lst
        return value

    @property
    def get_list_allowed_methods(self) -> list[str]:
        return self.allowed_methods.split(",")

    @field_validator("allowed_headers", mode="before", check_fields=False)
    @classmethod
    def split_allowed_headers(cls, value):
        if isinstance(value, str):
            lst = value.split(",")
            return lst
        return value

class RabbitConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_prefix="RABBITMQ_",
        case_sensitive=False,
        extra="ignore",
    )

    host: str = "localhost"
    port: int = 5672
    username: str = Field(
        default="guest",
        validation_alias=AliasChoices("RABBITMQ_DEFAULT_USER", "RABBITMQ_USER"),
    )
    password: SecretStr = Field(
        default=SecretStr("guest"),
        validation_alias=AliasChoices("RABBITMQ_DEFAULT_PASS", "RABBITMQ_PASSWORD"),
    )

    @property
    def url(self) -> str:
        return f"amqp://{self.username}:{self.password.get_secret_value()}@{self.host}:{self.port}/"

class DatabaseConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_prefix="POSTGRES_",
        case_sensitive=False,
        extra="ignore",
    )

    driver: str = "postgresql"
    username: str = Field(default="postgres", validation_alias="POSTGRES_USER")
    password: SecretStr = Field(default=SecretStr("postgres"), validation_alias="POSTGRES_PASSWORD")
    host: str = "localhost"
    port: int = 5432
    name: str = Field(default="postgres", validation_alias="POSTGRES_DB")
    echo: bool = False
    echo_pool: bool = False
    pool_size: int = 30
    max_overflow: int = 10

    naming_convention: dict[str, str] = {
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_N_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s",
    }

    def url(self, async_url: bool = True) -> str:
        driver = "postgresql+asyncpg" if async_url else "postgresql"
        return f"{driver}://{self.username}:{self.password.get_secret_value()}@{self.host}:{self.port}/{self.name}"


class APPSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        case_sensitive=False,
        env_nested_delimiter="__",
        env_ignore_empty=True,
        extra="ignore",
    )
    debug: bool = False
    api_key: SecretStr = SecretStr("")
    cors: CorsConfig = CorsConfig()
    sentry_dsn: SecretStr = SecretStr("")
    rabbitmq: RabbitConfig = RabbitConfig()
    db: DatabaseConfig = DatabaseConfig()

config = APPSettings()

from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    google_application_credentials: str = ""
    bigquery_project_id: str = ""
    bigquery_dataset: str = ""
    bigquery_table_lancamentos: str = "lancamentos"
    firebase_project_id: str = ""

    # Dados bancários Itaú
    itau_cnpj_empresa: str = ""
    itau_agencia: str = ""
    itau_conta: str = ""
    itau_dac: str = ""
    itau_nome_empresa: str = ""

    secret_key: str = "dev-secret-key"
    mock_mode: bool = False
    dev_mode: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()

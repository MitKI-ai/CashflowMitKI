from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_env: str = "development"
    app_secret_key: str = "change-me"
    database_url: str = "sqlite:///data/subscriptions.db"
    app_port: int = 8080
    smtp_host: str = "smtp.example.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    app_base_url: str = "https://www.cashflow.mitki.ai"
    smtp_from: str = "noreply@cashflow.mitki.ai"
    admin_email: str = "admin@mitki.ai"
    admin_password: str = "admin123"
    default_locale: str = "de"
    app_version: str = "0.1.0"
    is_production: bool = False
    internal_api_key: str = "change-me-internal"
    prefect_api_url: str = "http://localhost:4200/api"
    nocodb_api_url: str = ""
    nocodb_api_token: str = ""
    jwt_secret_key: str = "change-me-jwt-secret"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60
    google_client_id: str = ""
    google_client_secret: str = ""
    microsoft_client_id: str = ""
    microsoft_client_secret: str = ""

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()

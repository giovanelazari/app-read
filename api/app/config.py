from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://kindle:kindle@db:5432/kindle_highlights"
    web_url: str = "http://localhost:5173"
    vapid_claim_email: str = "mailto:admin@example.com"
    vapid_dir: str = "/data/vapid"
    playwright_profile_dir: str = "/data/playwright/profile"
    timezone: str = "America/Sao_Paulo"
    scheduler_enabled: bool = True

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def database_url_sync(self) -> str:
        # Alembic needs a synchronous URL; we use psycopg (v3) which supports both.
        return self.database_url


settings = Settings()

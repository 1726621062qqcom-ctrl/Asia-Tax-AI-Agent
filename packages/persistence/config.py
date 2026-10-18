"""Runtime configuration.

Values come from environment variables (prefix FSIE_) or an optional local .env.
No secrets are committed; .env is git-ignored, .env.example is the template.
"""

from __future__ import annotations

from functools import lru_cache
import os
import re

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Default points at the local docker-compose PostgreSQL.
    database_url: str = "postgresql+psycopg://fsie:fsie@localhost:5432/fsie_l0"
    chat_enable_model: bool = False
    allowed_hosts: list[str] = ['localhost', '127.0.0.1', '[::1]', 'testserver']
    secure_cookies: bool = False

    def deployment_hosts(self) -> list[str]:
        hosts = list(self.allowed_hosts)
        # Render supplies the exact service hostname; do not allow all onrender.com hosts.
        hostname = os.environ.get('RENDER_EXTERNAL_HOSTNAME', '')
        if re.fullmatch(r'[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.onrender\.com', hostname):
            hosts.append(hostname)
        return hosts

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="FSIE_",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()

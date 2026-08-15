from typing import Optional
from backend.repository.db import DbState
from backend.repository import config as config_repo


class ConfigService:
    def __init__(self, db: DbState):
        self.db = db

    def get_config(self, key: str) -> Optional[str]:
        return config_repo.get_config(self.db, key)

    def save_config(self, key: str, value: str) -> None:
        config_repo.save_config(self.db, key, value)

from typing import Any, Optional
from backend.config import DisplayConfig


class DisplayConfigService:
    def __init__(self, db: Optional[Any] = None) -> None:
        self.db = db

    @staticmethod
    def load() -> DisplayConfig:
        return DisplayConfig.load()

    @staticmethod
    def save(config: DisplayConfig) -> None:
        config.save()

    def get_config(self) -> DisplayConfig:
        return self.load()

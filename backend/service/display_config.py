from backend.config import DisplayConfig


class DisplayConfigService:
    @staticmethod
    def load() -> DisplayConfig:
        return DisplayConfig.load()

    @staticmethod
    def save(config: DisplayConfig) -> None:
        config.save()

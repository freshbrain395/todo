from typing import List, Dict, Any
from backend.repository.db import DbState
from backend.repository import ai_config as ai_config_repo


class AiConfigService:
    def __init__(self, db: DbState):
        self.db = db

    def get_providers(self) -> List[Dict[str, Any]]:
        return ai_config_repo.load_providers(self.db)

    def save_providers(self, providers_json: str) -> None:
        ai_config_repo.save_providers(self.db, providers_json)

    def get_prompts(self) -> List[Dict[str, Any]]:
        return ai_config_repo.load_prompts(self.db)

    def save_prompts(self, prompts_json: str) -> None:
        ai_config_repo.save_prompts(self.db, prompts_json)

    def get_skills(self) -> List[Dict[str, Any]]:
        return ai_config_repo.load_skills(self.db)

    def save_skills(self, skills_json: str) -> None:
        ai_config_repo.save_skills(self.db, skills_json)

    def get_sessions(self) -> List[Dict[str, Any]]:
        return ai_config_repo.load_sessions(self.db)

    def save_sessions(self, sessions_json: str) -> None:
        ai_config_repo.save_sessions(self.db, sessions_json)

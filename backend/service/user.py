from typing import Dict, Any
from backend.repository.db import DbState
from backend.repository import user as user_repo


class UserService:
    def __init__(self, db: DbState):
        self.db = db

    def register(self, username: str, password: str) -> Dict[str, Any]:
        return user_repo.register_user(self.db, username, password)

    def login(self, username: str, password: str) -> Dict[str, Any]:
        return user_repo.login_user(self.db, username, password)

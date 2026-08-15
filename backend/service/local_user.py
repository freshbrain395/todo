from backend.repository.db import DbState
from backend.repository import local_user as local_user_repo


class LocalUserService:
    def __init__(self, db: DbState):
        self.db = db

    def get_local_users(self) -> str:
        return local_user_repo.get_local_users(self.db)

    def save_local_users(self, accounts_json: str) -> None:
        local_user_repo.save_local_users(self.db, accounts_json)

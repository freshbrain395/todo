use crate::repository::{local_user as repo, DbState};

pub fn get_local_users(db: &DbState) -> Result<String, String> {
    repo::get_local_users(db)
}

pub fn save_local_users(db: &DbState, accounts_json: &str) -> Result<bool, String> {
    repo::save_local_users(db, accounts_json).map(|_| true)
}

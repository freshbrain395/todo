use crate::repository::{user as user_repo, DbState, User};

pub fn register_user(db: &DbState, username: &str, password: &str) -> Result<User, String> {
    user_repo::register_user(db, username, password)
}

pub fn login_user(db: &DbState, username: &str, password: &str) -> Result<User, String> {
    user_repo::login_user(db, username, password)
}

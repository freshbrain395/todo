use tauri::State;
use crate::repository::{DbState, User};
use crate::service::user as user_service;

pub fn register_user_direct(
    username: String,
    password: String,
    db: &DbState,
) -> Result<User, String> {
    user_service::register_user(db, &username, &password)
}

#[tauri::command]
pub fn register_user(
    username: String,
    password: String,
    db: State<'_, DbState>,
) -> Result<User, String> {
    register_user_direct(username, password, &db)
}

pub fn login_user_direct(
    username: String,
    password: String,
    db: &DbState,
) -> Result<User, String> {
    user_service::login_user(db, &username, &password)
}

#[tauri::command]
pub fn login_user(
    username: String,
    password: String,
    db: State<'_, DbState>,
) -> Result<User, String> {
    login_user_direct(username, password, &db)
}

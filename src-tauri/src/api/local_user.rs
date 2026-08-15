use tauri::State;
use crate::repository::DbState;
use crate::service::local_user;

pub fn get_local_users_direct(db: &DbState) -> Result<String, String> {
    local_user::get_local_users(db)
}

#[tauri::command]
pub fn get_local_users(db: State<'_, DbState>) -> Result<String, String> {
    get_local_users_direct(&db)
}

pub fn save_local_users_direct(accounts_json: String, db: &DbState) -> Result<bool, String> {
    local_user::save_local_users(db, &accounts_json)
}

#[tauri::command]
pub fn save_local_users(accounts_json: String, db: State<'_, DbState>) -> Result<bool, String> {
    save_local_users_direct(accounts_json, &db)
}

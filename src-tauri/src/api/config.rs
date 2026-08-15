use tauri::State;
use crate::repository::DbState;
use crate::service::config as config_service;
use crate::service::display_config::{self, DisplayConfig};

pub fn get_clock_config_direct(db: &DbState) -> Result<Option<String>, String> {
    config_service::get_clock_config(db)
}

#[tauri::command]
pub fn get_clock_config(db: State<'_, DbState>) -> Result<Option<String>, String> {
    get_clock_config_direct(&db)
}

pub fn save_clock_config_direct(config_json: String, db: &DbState) -> Result<bool, String> {
    config_service::save_clock_config(db, &config_json)
}

#[tauri::command]
pub fn save_clock_config(config_json: String, db: State<'_, DbState>) -> Result<bool, String> {
    save_clock_config_direct(config_json, &db)
}

pub fn get_app_config_direct(key: String, db: &DbState) -> Result<Option<String>, String> {
    config_service::get_app_config(db, &key)
}

#[tauri::command]
pub fn get_app_config(key: String, db: State<'_, DbState>) -> Result<Option<String>, String> {
    get_app_config_direct(key, &db)
}

pub fn save_app_config_direct(key: String, value: String, db: &DbState) -> Result<bool, String> {
    config_service::save_app_config(db, &key, &value)
}

#[tauri::command]
pub fn save_app_config(key: String, value: String, db: State<'_, DbState>) -> Result<bool, String> {
    save_app_config_direct(key, value, &db)
}

pub fn get_display_config_direct() -> DisplayConfig {
    display_config::load_display_config()
}

#[tauri::command]
pub fn get_display_config() -> DisplayConfig {
    get_display_config_direct()
}

pub fn save_display_config_direct(config: DisplayConfig) -> Result<bool, String> {
    display_config::save_display_config(&config).map(|_| true)
}

#[tauri::command]
pub fn save_display_config(config: DisplayConfig) -> Result<bool, String> {
    save_display_config_direct(config)
}

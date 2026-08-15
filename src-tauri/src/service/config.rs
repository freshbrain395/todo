use crate::repository::{config as config_repo, DbState};

pub fn get_clock_config(db: &DbState) -> Result<Option<String>, String> {
    config_repo::get_config(db, "clock_config").map_err(|e| e.to_string())
}

pub fn save_clock_config(db: &DbState, config_json: &str) -> Result<bool, String> {
    config_repo::save_config(db, "clock_config", config_json)
        .map(|_| true)
        .map_err(|e| e.to_string())
}

pub fn get_app_config(db: &DbState, key: &str) -> Result<Option<String>, String> {
    config_repo::get_config(db, key).map_err(|e| e.to_string())
}

pub fn save_app_config(db: &DbState, key: &str, value: &str) -> Result<bool, String> {
    config_repo::save_config(db, key, value)
        .map(|_| true)
        .map_err(|e| e.to_string())
}

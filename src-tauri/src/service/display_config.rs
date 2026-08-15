use serde::{Deserialize, Serialize};
use std::fs;
use std::path::PathBuf;

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct DisplayConfig {
    pub user_name: String,
    pub user_prefix: String,
    pub ai_name: String,
    pub ai_prefix: String,
}

impl Default for DisplayConfig {
    fn default() -> Self {
        Self {
            user_name: "用户".to_string(),
            user_prefix: "todo-agent".to_string(),
            ai_name: "Todo Agent".to_string(),
            ai_prefix: "🤖".to_string(),
        }
    }
}

pub fn get_display_config_path() -> PathBuf {
    dirs::data_local_dir()
        .unwrap_or_else(|| PathBuf::from("."))
        .join("todo_agent")
        .join("cli_config.json")
}

pub fn load_display_config() -> DisplayConfig {
    let path = get_display_config_path();
    if path.exists() {
        if let Ok(content) = fs::read_to_string(&path) {
            if let Ok(config) = serde_json::from_str::<DisplayConfig>(&content) {
                return config;
            }
        }
    }
    let default_config = DisplayConfig::default();
    let _ = save_display_config(&default_config);
    default_config
}

pub fn save_display_config(config: &DisplayConfig) -> Result<(), String> {
    let path = get_display_config_path();
    if let Some(parent) = path.parent() {
        let _ = fs::create_dir_all(parent);
    }
    let json_str = serde_json::to_string_pretty(config).map_err(|e| e.to_string())?;
    fs::write(&path, json_str).map_err(|e| e.to_string())
}

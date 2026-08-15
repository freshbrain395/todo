use tauri::State;
use serde_json::Value;
use crate::repository::DbState;
use crate::service::ai_config;

pub fn get_ai_providers_direct(db: &DbState) -> Result<Vec<Value>, String> {
    ai_config::get_providers(db)
}

#[tauri::command]
pub fn get_ai_providers(db: State<'_, DbState>) -> Result<Vec<Value>, String> {
    get_ai_providers_direct(&db)
}

pub fn save_ai_providers_direct(providers_json: String, db: &DbState) -> Result<bool, String> {
    ai_config::save_providers(db, &providers_json)
}

#[tauri::command]
pub fn save_ai_providers(providers_json: String, db: State<'_, DbState>) -> Result<bool, String> {
    save_ai_providers_direct(providers_json, &db)
}

pub fn get_ai_prompts_direct(db: &DbState) -> Result<Vec<Value>, String> {
    ai_config::get_prompts(db)
}

#[tauri::command]
pub fn get_ai_prompts(db: State<'_, DbState>) -> Result<Vec<Value>, String> {
    get_ai_prompts_direct(&db)
}

pub fn save_ai_prompts_direct(prompts_json: String, db: &DbState) -> Result<bool, String> {
    ai_config::save_prompts(db, &prompts_json)
}

#[tauri::command]
pub fn save_ai_prompts(prompts_json: String, db: State<'_, DbState>) -> Result<bool, String> {
    save_ai_prompts_direct(prompts_json, &db)
}

pub fn get_ai_skills_direct(db: &DbState) -> Result<Vec<Value>, String> {
    ai_config::get_skills(db)
}

#[tauri::command]
pub fn get_ai_skills(db: State<'_, DbState>) -> Result<Vec<Value>, String> {
    get_ai_skills_direct(&db)
}

pub fn save_ai_skills_direct(skills_json: String, db: &DbState) -> Result<bool, String> {
    ai_config::save_skills(db, &skills_json)
}

#[tauri::command]
pub fn save_ai_skills(skills_json: String, db: State<'_, DbState>) -> Result<bool, String> {
    save_ai_skills_direct(skills_json, &db)
}

pub fn get_ai_sessions_direct(db: &DbState) -> Result<Vec<Value>, String> {
    ai_config::get_sessions(db)
}

#[tauri::command]
pub fn get_ai_sessions(db: State<'_, DbState>) -> Result<Vec<Value>, String> {
    get_ai_sessions_direct(&db)
}

pub fn save_ai_sessions_direct(sessions_json: String, db: &DbState) -> Result<bool, String> {
    ai_config::save_sessions(db, &sessions_json)
}

#[tauri::command]
pub fn save_ai_sessions(sessions_json: String, db: State<'_, DbState>) -> Result<bool, String> {
    save_ai_sessions_direct(sessions_json, &db)
}

pub fn get_tool_config_direct(db: &DbState) -> Result<Option<String>, String> {
    ai_config::get_tool_config(db)
}

#[tauri::command]
pub fn get_tool_config(db: State<'_, DbState>) -> Result<Option<String>, String> {
    get_tool_config_direct(&db)
}

pub fn save_tool_config_direct(config_json: String, db: &DbState) -> Result<bool, String> {
    ai_config::save_tool_config(db, &config_json)
}

#[tauri::command]
pub fn save_tool_config(config_json: String, db: State<'_, DbState>) -> Result<bool, String> {
    save_tool_config_direct(config_json, &db)
}

pub fn get_llm_config_direct(db: &DbState) -> Result<Option<String>, String> {
    ai_config::get_llm_config(db)
}

#[tauri::command]
pub fn get_llm_config(db: State<'_, DbState>) -> Result<Option<String>, String> {
    get_llm_config_direct(&db)
}

pub fn save_llm_config_direct(config_json: String, db: &DbState) -> Result<bool, String> {
    ai_config::save_llm_config(db, &config_json)
}

#[tauri::command]
pub fn save_llm_config(config_json: String, db: State<'_, DbState>) -> Result<bool, String> {
    save_llm_config_direct(config_json, &db)
}

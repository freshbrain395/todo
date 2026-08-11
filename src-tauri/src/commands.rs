use tauri::State;
use crate::db::{DbState, Todo};
use crate::llm::{parse_intent_and_execute, AiActionResult, LlmConfig};

#[tauri::command]
pub fn get_todos(
    filter: String,
    search: String,
    db: State<'_, DbState>,
) -> Result<Vec<Todo>, String> {
    db.get_todos(&filter, &search).map_err(|e| e.to_string())
}

#[tauri::command]
pub fn add_todo(
    title: String,
    priority: String,
    category: String,
    remind_at: Option<String>,
    db: State<'_, DbState>,
) -> Result<i64, String> {
    db.add_todo(&title, &priority, &category, remind_at.as_deref())
        .map_err(|e| e.to_string())
}

#[tauri::command]
pub fn update_todo_status(
    id: i64,
    completed: bool,
    db: State<'_, DbState>,
) -> Result<bool, String> {
    db.update_todo_status(id, completed).map_err(|e| e.to_string())
}

#[tauri::command]
pub fn update_todo(
    id: i64,
    title: String,
    priority: String,
    category: String,
    remind_at: Option<String>,
    db: State<'_, DbState>,
) -> Result<bool, String> {
    db.update_todo(id, &title, &priority, &category, remind_at.as_deref())
        .map_err(|e| e.to_string())
}

#[tauri::command]
pub fn delete_todo(id: i64, db: State<'_, DbState>) -> Result<bool, String> {
    db.delete_todo(id).map_err(|e| e.to_string())
}

#[tauri::command]
pub async fn fetch_models(base_url: String, api_key: String) -> Result<Vec<String>, String> {
    let clean_url = base_url.trim().trim_end_matches('/').to_string();
    let api_url = if clean_url.contains("11434") {
        if !clean_url.ends_with("/api") && !clean_url.ends_with("/v1") {
            format!("{}/api/tags", clean_url)
        } else if clean_url.ends_with("/api") {
            format!("{}/tags", clean_url)
        } else {
            format!("{}/models", clean_url)
        }
    } else {
        if !clean_url.ends_with("/v1") && !clean_url.contains("/models") {
            format!("{}/models", clean_url)
        } else if clean_url.ends_with("/v1") {
            format!("{}/models", clean_url)
        } else {
            clean_url
        }
    };

    let client = reqwest::Client::builder()
        .timeout(std::time::Duration::from_secs(10))
        .build()
        .map_err(|e| format!("HTTP客户端初始化失败: {}", e))?;

    let mut req = client.get(&api_url);
    if !api_key.trim().is_empty() {
        req = req.header("Authorization", format!("Bearer {}", api_key.trim()));
    }

    let resp = req.send().await.map_err(|e| format!("网络请求失败: {}", e))?;
    if !resp.status().is_success() {
        return Err(format!("HTTP 状态错误: {}", resp.status()));
    }

    let json_val: serde_json::Value = resp.json().await.map_err(|e| format!("JSON解析失败: {}", e))?;

    let mut model_names = Vec::new();
    if let Some(data_arr) = json_val.get("data").and_then(|v| v.as_array()) {
        for m in data_arr {
            if let Some(id) = m.get("id").and_then(|v| v.as_str()) {
                model_names.push(id.to_string());
            }
        }
    } else if let Some(models_arr) = json_val.get("models").and_then(|v| v.as_array()) {
        for m in models_arr {
            if let Some(name) = m.get("name").and_then(|v| v.as_str()) {
                model_names.push(name.to_string());
            }
        }
    }

    if model_names.is_empty() {
        return Err("解析成功但未发现任何可用模型".to_string());
    }

    Ok(model_names)
}

#[tauri::command]
pub async fn execute_ai_command(
    input: String,
    config: LlmConfig,
    db: State<'_, DbState>,
) -> Result<AiActionResult, String> {
    parse_intent_and_execute(&input, &config, &db).await
}

#[tauri::command]
pub fn get_clock_config(db: State<'_, DbState>) -> Result<Option<String>, String> {
    db.get_config("clock_config").map_err(|e| e.to_string())
}

#[tauri::command]
pub fn save_clock_config(config_json: String, db: State<'_, DbState>) -> Result<bool, String> {
    db.save_config("clock_config", &config_json)
        .map(|_| true)
        .map_err(|e| e.to_string())
}

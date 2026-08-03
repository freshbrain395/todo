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
pub async fn execute_ai_command(
    input: String,
    config: LlmConfig,
    db: State<'_, DbState>,
) -> Result<AiActionResult, String> {
    parse_intent_and_execute(&input, &config, &db).await
}

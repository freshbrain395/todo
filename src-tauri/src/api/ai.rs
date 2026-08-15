use tauri::State;
use crate::repository::DbState;
use crate::service::ai::{self as ai_service, AiActionResult, ChatMessage, LlmConfig};

#[tauri::command]
pub async fn fetch_models(base_url: String, api_key: String) -> Result<Vec<String>, String> {
    ai_service::fetch_models(base_url, api_key).await
}

pub async fn execute_ai_command_direct(
    input: String,
    config: LlmConfig,
    user_id: Option<i64>,
    history: Option<Vec<ChatMessage>>,
    system_prompt: Option<String>,
    db: &DbState,
) -> Result<AiActionResult, String> {
    let history_ref = history.as_deref();
    let system_ref = system_prompt.as_deref();
    ai_service::parse_intent_and_execute(&input, &config, db, user_id, system_ref, history_ref).await
}

#[tauri::command]
pub async fn execute_ai_command(
    input: String,
    config: LlmConfig,
    user_id: Option<i64>,
    history: Option<Vec<ChatMessage>>,
    system_prompt: Option<String>,
    db: State<'_, DbState>,
) -> Result<AiActionResult, String> {
    execute_ai_command_direct(input, config, user_id, history, system_prompt, &db).await
}

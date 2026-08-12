// Prevents additional console window on Windows in release, DO NOT REMOVE!!
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod db;
mod llm;
mod commands;

use db::DbState;
use std::fs;

fn main() {
    let app_dir = dirs::data_local_dir()
        .unwrap_or_else(|| std::path::PathBuf::from("."))
        .join("todo_agent");
    let _ = fs::create_dir_all(&app_dir);
    let db_path = app_dir.join("todos.db");

    let db_state = DbState::new(db_path).expect("Failed to initialize SQLite database");

    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_updater::Builder::new().build())
        .manage(db_state)
        .invoke_handler(tauri::generate_handler![
            commands::register_user,
            commands::login_user,
            commands::get_todos,
            commands::add_todo,
            commands::update_todo_status,
            commands::update_todo,
            commands::delete_todo,
            commands::fetch_models,
            commands::execute_ai_command,
            commands::get_clock_config,
            commands::save_clock_config
        ])

        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}

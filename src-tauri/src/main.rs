// Prevents additional console window on Windows in release, DO NOT REMOVE!!
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

pub mod api;
pub mod repository;
pub mod service;

pub mod db;
pub mod llm;
pub mod commands;
pub mod cli;

// 为了保持与原有结构的向下兼容性，也可以 re-export 常用结构体
pub use repository::db::DbState;
pub use repository::todo::Todo;
pub use repository::user::User;

use std::fs;
use clap::Parser;

#[tokio::main]
async fn main() {
    let app_dir = dirs::data_local_dir()
        .unwrap_or_else(|| std::path::PathBuf::from("."))
        .join("todo_agent");
    let _ = fs::create_dir_all(&app_dir);
    let db_path = app_dir.join("todos.db");

    let db_state = DbState::new(db_path).expect("Failed to initialize SQLite database");

    // 若有命令行参数传人（如 pnpm cli 或运行 CLI 子命令），进入 CLI 模式
    let args: Vec<String> = std::env::args().collect();
    if args.len() > 1 {
        if let Ok(cli_args) = cli::Cli::try_parse() {
            cli::handle_cli(cli_args, &db_state).await;
            return;
        }
    }


    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_updater::Builder::new().build())
        .manage(db_state)
        .invoke_handler(tauri::generate_handler![
            api::register_user,
            api::login_user,
            api::get_todos,
            api::add_todo,
            api::update_todo_status,
            api::update_todo,
            api::delete_todo,
            api::fetch_models,
            api::execute_ai_command,
            api::get_clock_config,
            api::save_clock_config,
            api::get_app_config,
            api::save_app_config,
            api::get_display_config,
            api::save_display_config,
            api::get_ai_providers,
            api::save_ai_providers,
            api::get_ai_prompts,
            api::save_ai_prompts,
            api::get_ai_skills,
            api::save_ai_skills,
            api::get_ai_sessions,
            api::save_ai_sessions,
            api::get_tool_config,
            api::save_tool_config,
            api::get_llm_config,
            api::save_llm_config,
            api::get_local_users,
            api::save_local_users
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}


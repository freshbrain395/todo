use tauri::State;
use crate::repository::{DbState, Todo};
use crate::service::todo as todo_service;

pub fn get_todos_direct(
    filter: String,
    search: String,
    user_id: Option<i64>,
    db: &DbState,
) -> Result<Vec<Todo>, String> {
    todo_service::get_todos(db, &filter, &search, user_id)
}

#[tauri::command]
pub fn get_todos(
    filter: String,
    search: String,
    user_id: Option<i64>,
    db: State<'_, DbState>,
) -> Result<Vec<Todo>, String> {
    get_todos_direct(filter, search, user_id, &db)
}

pub fn add_todo_direct(
    title: String,
    priority: String,
    category: String,
    remind_at: Option<String>,
    user_id: Option<i64>,
    db: &DbState,
) -> Result<i64, String> {
    todo_service::add_todo(db, &title, &priority, &category, remind_at.as_deref(), user_id)
}

#[tauri::command]
pub fn add_todo(
    title: String,
    priority: String,
    category: String,
    remind_at: Option<String>,
    user_id: Option<i64>,
    db: State<'_, DbState>,
) -> Result<i64, String> {
    add_todo_direct(title, priority, category, remind_at, user_id, &db)
}

pub fn update_todo_status_direct(
    id: i64,
    completed: bool,
    user_id: Option<i64>,
    db: &DbState,
) -> Result<bool, String> {
    todo_service::update_todo_status(db, id, completed, user_id)
}

#[tauri::command]
pub fn update_todo_status(
    id: i64,
    completed: bool,
    user_id: Option<i64>,
    db: State<'_, DbState>,
) -> Result<bool, String> {
    update_todo_status_direct(id, completed, user_id, &db)
}

pub fn update_todo_direct(
    id: i64,
    title: String,
    priority: String,
    category: String,
    remind_at: Option<String>,
    user_id: Option<i64>,
    db: &DbState,
) -> Result<bool, String> {
    todo_service::update_todo(db, id, &title, &priority, &category, remind_at.as_deref(), user_id)
}

#[tauri::command]
pub fn update_todo(
    id: i64,
    title: String,
    priority: String,
    category: String,
    remind_at: Option<String>,
    user_id: Option<i64>,
    db: State<'_, DbState>,
) -> Result<bool, String> {
    update_todo_direct(id, title, priority, category, remind_at, user_id, &db)
}

pub fn delete_todo_direct(id: i64, user_id: Option<i64>, db: &DbState) -> Result<bool, String> {
    todo_service::delete_todo(db, id, user_id)
}

#[tauri::command]
pub fn delete_todo(id: i64, user_id: Option<i64>, db: State<'_, DbState>) -> Result<bool, String> {
    delete_todo_direct(id, user_id, &db)
}

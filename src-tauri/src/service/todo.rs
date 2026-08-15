use crate::repository::{todo as todo_repo, DbState, Todo};

pub fn get_todos(db: &DbState, filter: &str, search: &str, user_id: Option<i64>) -> Result<Vec<Todo>, String> {
    todo_repo::get_todos(db, filter, search, user_id).map_err(|e| e.to_string())
}

pub fn add_todo(
    db: &DbState,
    title: &str,
    priority: &str,
    category: &str,
    remind_at: Option<&str>,
    user_id: Option<i64>,
) -> Result<i64, String> {
    todo_repo::add_todo(db, title, priority, category, remind_at, user_id).map_err(|e| e.to_string())
}

pub fn update_todo_status(db: &DbState, id: i64, completed: bool, user_id: Option<i64>) -> Result<bool, String> {
    todo_repo::update_todo_status(db, id, completed, user_id).map_err(|e| e.to_string())
}

pub fn update_todo(
    db: &DbState,
    id: i64,
    title: &str,
    priority: &str,
    category: &str,
    remind_at: Option<&str>,
    user_id: Option<i64>,
) -> Result<bool, String> {
    todo_repo::update_todo(db, id, title, priority, category, remind_at, user_id).map_err(|e| e.to_string())
}

pub fn delete_todo(db: &DbState, id: i64, user_id: Option<i64>) -> Result<bool, String> {
    todo_repo::delete_todo(db, id, user_id).map_err(|e| e.to_string())
}

pub use crate::repository::db::DbState;
pub use crate::repository::todo::Todo;
pub use crate::repository::user::User;

#[cfg(test)]
mod tests {
    use std::path::PathBuf;
    use crate::repository::{user as user_repo, todo as todo_repo, DbState};

    #[test]
    fn test_sqlite_crud_and_user_auth() {
        let db_state = DbState::new(PathBuf::from(":memory:")).expect("Failed to create in-memory db");

        // 1. Register & Login User
        let user = user_repo::register_user(&db_state, "testuser", "123456").expect("Register failed");
        assert_eq!(user.username, "testuser");

        let logged_user = user_repo::login_user(&db_state, "testuser", "123456").expect("Login failed");
        assert_eq!(logged_user.id, user.id);

        // 2. Add local todo & user todo
        let local_id = todo_repo::add_todo(&db_state, "本地任务", "high", "工作", None, None).expect("Add local failed");
        let user_id_todo = todo_repo::add_todo(&db_state, "用户专属任务", "high", "学习", None, Some(user.id)).expect("Add user todo failed");

        // 3. Verify Isolation
        let local_todos = todo_repo::get_todos(&db_state, "all", "", None).expect("Get local failed");
        assert_eq!(local_todos.len(), 1);
        assert_eq!(local_todos[0].id, local_id);

        let user_todos = todo_repo::get_todos(&db_state, "all", "", Some(user.id)).expect("Get user failed");
        assert_eq!(user_todos.len(), 1);
        assert_eq!(user_todos[0].id, user_id_todo);
    }
}

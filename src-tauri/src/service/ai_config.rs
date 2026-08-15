use std::fs;
use std::path::PathBuf;
use serde_json::{json, Value};
use crate::repository::{ai_config as repo, config as config_repo, DbState};

const TOOL_CONFIG_KEY: &str = "agent_enabled_tools";
const LLM_CONFIG_KEY: &str = "llm_config";

pub fn get_prompts_file_path() -> PathBuf {
    dirs::data_local_dir()
        .unwrap_or_else(|| PathBuf::from("."))
        .join("todo_agent")
        .join("prompts.json")
}

pub fn get_skills_dir_path() -> PathBuf {
    dirs::data_local_dir()
        .unwrap_or_else(|| PathBuf::from("."))
        .join("todo_agent")
        .join("skills")
}

fn default_prompts() -> Vec<Value> {
    vec![
        json!({ "id": "schedule", "category": "工作", "title": "高效工作日程划分", "text": "请帮我规划今天的工作日程，把重要且紧急的任务安排在上午最清醒的时候。", "jsonFormat": "", "enabled": true, "isActive": false }),
        json!({ "id": "breakdown", "category": "项目", "title": "复杂大项目细化", "text": "帮我把\"完成项目上线\"拆解为 5 个具体的、可落地的子待办事项。", "jsonFormat": "", "enabled": true, "isActive": false }),
        json!({ "id": "summary", "category": "总结", "title": "工作总结整理", "text": "请根据我已完成的待办事项，帮我撰写一份简明扼要的本周工作总结。", "jsonFormat": "", "enabled": true, "isActive": false }),
        json!({ "id": "quadrant", "category": "规划", "title": "待办四象限排序", "text": "分析我现有的待办列表，并给出最推荐优先处理的前 3 项任务建议。", "jsonFormat": "", "enabled": true, "isActive": false })
    ]
}

fn default_skills() -> Vec<Value> {
    vec![
        json!({ "id": "gtd", "category": "时间管理", "title": "GTD 四象限任务规划", "description": "按紧急/重要四象限分类任务并提供优先级建议", "systemPrompt": "请将用户提交的任务按紧急/重要四象限进行分类，并给出第一优先级的 3 个具体执行建议。", "enabled": true }),
        json!({ "id": "pomodoro", "category": "专注提升", "title": "番茄工作法轮巡规划", "description": "将大任务拆分为 25 分钟番茄钟与 5 分钟休息时段", "systemPrompt": "将大任务拆分为若干 25 分钟的番茄专注时段，并给出每个时段的安排建议。", "enabled": true }),
        json!({ "id": "weekly-report", "category": "工作总结", "title": "周报与工作总结整理", "description": "提炼本周已完成事项产出及风险分析", "systemPrompt": "分析已完成待办，提炼本周核心产出、未完成风险及下周计划。", "enabled": true }),
        json!({ "id": "smart-alarm", "category": "自然语言", "title": "自然语言时间解构与提醒", "description": "提取口头描述中的时间并转换为待办提醒", "systemPrompt": "提取用户输入中的时间点与事件主体，将模糊时间（如\"明早八点半\"）转换为具体时间，并生成提醒待办。", "enabled": true }),
        json!({ "id": "breakdown", "category": "项目拆解", "title": "目标分解与微习惯提炼", "description": "把大目标拆解为可操作的微习惯行动项", "systemPrompt": "拆解复杂目标为具体、可衡量、有清晰动作的子待办事项。", "enabled": true })
    ]
}

pub fn get_providers(db: &DbState) -> Result<Vec<Value>, String> {
    repo::load_providers(db)
}

pub fn save_providers(db: &DbState, providers_json: &str) -> Result<bool, String> {
    repo::save_providers(db, providers_json).map(|_| true)
}

// ============ Prompts File Storage ============

pub fn get_prompts(db: &DbState) -> Result<Vec<Value>, String> {
    let file_path = get_prompts_file_path();
    if file_path.exists() {
        if let Ok(content) = fs::read_to_string(&file_path) {
            if let Ok(val) = serde_json::from_str::<Vec<Value>>(&content) {
                if !val.is_empty() {
                    let _ = repo::save_prompts(db, &content);
                    return Ok(val);
                }
            }
        }
    }

    let prompts = repo::load_prompts(db).unwrap_or_else(|_| default_prompts());
    let list = if prompts.is_empty() { default_prompts() } else { prompts };
    if let Ok(json_str) = serde_json::to_string_pretty(&list) {
        if let Some(parent) = file_path.parent() {
            let _ = fs::create_dir_all(parent);
        }
        let _ = fs::write(&file_path, &json_str);
        let _ = repo::save_prompts(db, &json_str);
    }
    Ok(list)
}

pub fn save_prompts(db: &DbState, prompts_json: &str) -> Result<bool, String> {
    let file_path = get_prompts_file_path();
    if let Some(parent) = file_path.parent() {
        let _ = fs::create_dir_all(parent);
    }
    if let Ok(val) = serde_json::from_str::<Value>(prompts_json) {
        let pretty = serde_json::to_string_pretty(&val).unwrap_or_else(|_| prompts_json.to_string());
        let _ = fs::write(&file_path, &pretty);
        let _ = repo::save_prompts(db, &pretty);
    } else {
        let _ = fs::write(&file_path, prompts_json);
        let _ = repo::save_prompts(db, prompts_json);
    }
    Ok(true)
}

// ============ Skills Folder Storage ============

pub fn get_skills(db: &DbState) -> Result<Vec<Value>, String> {
    let dir_path = get_skills_dir_path();
    if dir_path.exists() && dir_path.is_dir() {
        if let Ok(entries) = fs::read_dir(&dir_path) {
            let mut file_skills = Vec::new();
            for entry in entries.flatten() {
                let path = entry.path();
                if path.is_file() && path.extension().and_then(|s| s.to_str()) == Some("json") {
                    if let Ok(content) = fs::read_to_string(&path) {
                        if let Ok(val) = serde_json::from_str::<Value>(&content) {
                            file_skills.push(val);
                        }
                    }
                }
            }
            if !file_skills.is_empty() {
                if let Ok(json_str) = serde_json::to_string(&file_skills) {
                    let _ = repo::save_skills(db, &json_str);
                }
                return Ok(file_skills);
            }
        }
    }

    let db_skills = repo::load_skills(db).unwrap_or_else(|_| default_skills());
    let list = if db_skills.is_empty() { default_skills() } else { db_skills };
    let _ = fs::create_dir_all(&dir_path);
    for skill in &list {
        let id = skill["id"].as_str().unwrap_or("skill");
        let skill_file = dir_path.join(format!("{}.json", id));
        if let Ok(pretty) = serde_json::to_string_pretty(skill) {
            let _ = fs::write(skill_file, pretty);
        }
    }
    if let Ok(json_str) = serde_json::to_string(&list) {
        let _ = repo::save_skills(db, &json_str);
    }
    Ok(list)
}

pub fn save_skills(db: &DbState, skills_json: &str) -> Result<bool, String> {
    let dir_path = get_skills_dir_path();
    let _ = fs::create_dir_all(&dir_path);

    let skills: Vec<Value> = serde_json::from_str(skills_json).unwrap_or_default();

    if let Ok(entries) = fs::read_dir(&dir_path) {
        for entry in entries.flatten() {
            let path = entry.path();
            if path.is_file() && path.extension().and_then(|s| s.to_str()) == Some("json") {
                let stem = path.file_stem().and_then(|s| s.to_str()).unwrap_or("");
                let exists_in_new = skills.iter().any(|s| s["id"].as_str().unwrap_or("") == stem);
                if !exists_in_new {
                    let _ = fs::remove_file(path);
                }
            }
        }
    }

    for s in &skills {
        let id = s["id"].as_str().unwrap_or("skill");
        let skill_file = dir_path.join(format!("{}.json", id));
        if let Ok(pretty) = serde_json::to_string_pretty(s) {
            let _ = fs::write(skill_file, pretty);
        }
    }

    let _ = repo::save_skills(db, skills_json);
    Ok(true)
}

pub fn get_sessions(db: &DbState) -> Result<Vec<Value>, String> {
    repo::load_sessions(db)
}

pub fn save_sessions(db: &DbState, sessions_json: &str) -> Result<bool, String> {
    repo::save_sessions(db, sessions_json).map(|_| true)
}

pub fn get_tool_config(db: &DbState) -> Result<Option<String>, String> {
    config_repo::get_config(db, TOOL_CONFIG_KEY).map_err(|e| e.to_string())
}

pub fn save_tool_config(db: &DbState, config_json: &str) -> Result<bool, String> {
    config_repo::save_config(db, TOOL_CONFIG_KEY, config_json)
        .map(|_| true)
        .map_err(|e| e.to_string())
}

pub fn get_llm_config(db: &DbState) -> Result<Option<String>, String> {
    config_repo::get_config(db, LLM_CONFIG_KEY).map_err(|e| e.to_string())
}

pub fn save_llm_config(db: &DbState, config_json: &str) -> Result<bool, String> {
    config_repo::save_config(db, LLM_CONFIG_KEY, config_json)
        .map(|_| true)
        .map_err(|e| e.to_string())
}

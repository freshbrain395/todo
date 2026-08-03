use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use reqwest::Client;
use std::time::Duration;

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct LlmConfig {
    pub provider: String,
    pub base_url: String,
    pub api_key: String,
    pub model: String,
    pub enable_thinking: bool,
}

impl Default for LlmConfig {
    fn default() -> Self {
        LlmConfig {
            provider: "siliconflow".to_string(),
            base_url: "https://api.siliconflow.cn/v1".to_string(),
            api_key: "".to_string(),
            model: "deepseek-ai/DeepSeek-V4-Flash".to_string(),
            enable_thinking: false,
        }
    }
}

#[derive(Debug, Serialize, Deserialize)]
pub struct AiActionResult {
    pub action: String,
    pub data: Value,
    pub message: String,
    pub should_refresh: bool,
}

pub async fn parse_intent_and_execute(
    user_input: &str,
    config: &LlmConfig,
    db: &super::db::DbState,
) -> Result<AiActionResult, String> {
    let client = Client::builder()
        .timeout(Duration::from_secs(30))
        .build()
        .map_err(|e| e.to_string())?;

    let system_prompt = r#"你是一个待办事项智能助手。根据用户的自然语言输入，解析其意图并返回固定格式的 JSON 对象（不要添加任何 markdown 代码块标记以外的文字）。
JSON 格式标准：
{
  "action": "add" | "complete" | "delete" | "query" | "chat",
  "data": {
    "title": "任务标题（如果 action 是 add）",
    "priority": "high" | "medium" | "low",
    "category": "工作" | "生活" | "学习" | "个人",
    "remind_at": "YYYY-MM-DD HH:MM:SS" (可选),
    "id": 123 (如果 action 是 complete 或 delete)
  },
  "raw_response": "给用户的回复文本"
}"#;

    let url = if config.provider == "siliconflow" {
        format!("{}/chat/completions", config.base_url.trim_end_matches('/'))
    } else {
        format!("{}/api/generate", config.base_url.trim_end_matches('/'))
    };

    let body = if config.provider == "siliconflow" {
        json!({
            "model": config.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input}
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.2
        })
    } else {
        json!({
            "model": config.model,
            "system": system_prompt,
            "prompt": user_input,
            "stream": false,
            "format": "json"
        })
    };

    let mut request = client.post(&url);
    if config.provider == "siliconflow" && !config.api_key.is_empty() {
        request = request.header("Authorization", format!("Bearer {}", config.api_key));
    }

    let response = request
        .json(&body)
        .send()
        .await
        .map_err(|e| format!("请求 AI 接口失败: {}", e))?;

    let res_json: Value = response
        .json()
        .await
        .map_err(|e| format!("解析 AI 响应 JSON 失败: {}", e))?;

    let content_text = if config.provider == "siliconflow" {
        res_json["choices"][0]["message"]["content"]
            .as_str()
            .unwrap_or("")
            .to_string()
    } else {
        res_json["response"].as_str().unwrap_or("").to_string()
    };

    // Clean JSON content if wrapped in markdown fenced code blocks
    let clean_json = content_text
        .trim()
        .trim_start_matches("```json")
        .trim_start_matches("```")
        .trim_end_matches("```")
        .trim();

    let parsed: Value = serde_json::from_str(clean_json).unwrap_or_else(|_| {
        json!({
            "action": "chat",
            "data": {},
            "raw_response": content_text
        })
    });

    let action = parsed["action"].as_str().unwrap_or("chat");
    let data = &parsed["data"];

    match action {
        "add" => {
            let title = data["title"].as_str().unwrap_or(user_input);
            let priority = data["priority"].as_str().unwrap_or("medium");
            let category = data["category"].as_str().unwrap_or("工作");
            let remind_at = data["remind_at"].as_str();

            let todo_id = db
                .add_todo(title, priority, category, remind_at)
                .map_err(|e| format!("写入数据库失败: {}", e))?;

            Ok(AiActionResult {
                action: "add".to_string(),
                data: json!({"id": todo_id, "title": title}),
                message: format!("✨ 已为您智能创建待办：[{}] (分类: {}, 优先级: {})", title, category, priority),
                should_refresh: true,
            })
        }
        "complete" => {
            let id = data["id"].as_i64().unwrap_or(0);
            if id > 0 {
                let _ = db.update_todo_status(id, true);
                Ok(AiActionResult {
                    action: "complete".to_string(),
                    data: json!({"id": id}),
                    message: format!("✅ 已为您完成待办事项 ID [{}]", id),
                    should_refresh: true,
                })
            } else {
                Ok(AiActionResult {
                    action: "chat".to_string(),
                    data: json!({}),
                    message: parsed["raw_response"].as_str().unwrap_or("未找到匹配的任务 ID").to_string(),
                    should_refresh: false,
                })
            }
        }
        "delete" => {
            let id = data["id"].as_i64().unwrap_or(0);
            if id > 0 {
                let _ = db.delete_todo(id);
                Ok(AiActionResult {
                    action: "delete".to_string(),
                    data: json!({"id": id}),
                    message: format!("🗑️ 已为您删除待办事项 ID [{}]", id),
                    should_refresh: true,
                })
            } else {
                Ok(AiActionResult {
                    action: "chat".to_string(),
                    data: json!({}),
                    message: parsed["raw_response"].as_str().unwrap_or("删除失败，未提供合法任务 ID").to_string(),
                    should_refresh: false,
                })
            }
        }
        _ => {
            let reply = parsed["raw_response"]
                .as_str()
                .unwrap_or("收到指令，但未能识别出明确的待办新增/修改操作。");
            Ok(AiActionResult {
                action: "chat".to_string(),
                data: json!({}),
                message: format!("🤖 AI 回复：{}", reply),
                should_refresh: false,
            })
        }
    }
}

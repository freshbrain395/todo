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
    user_id: Option<i64>,
) -> Result<AiActionResult, String> {
    let client = Client::builder()
        .timeout(Duration::from_secs(15))
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
  "raw_response": "给用户的亲切回复文本"
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

    // 尝试请求大模型，若失败或未配置 Key 则自动使用本地智能降级解析引擎
    let mut request = client.post(&url);
    if config.provider == "siliconflow" && !config.api_key.is_empty() {
        request = request.header("Authorization", format!("Bearer {}", config.api_key));
    }

    let parsed_result = match request.json(&body).send().await {
        Ok(response) => {
            if response.status().is_success() {
                match response.json::<Value>().await {
                    Ok(res_json) => {
                        let content_text = if config.provider == "siliconflow" {
                            res_json["choices"][0]["message"]["content"]
                                .as_str()
                                .unwrap_or("")
                                .to_string()
                        } else {
                            res_json["response"].as_str().unwrap_or("").to_string()
                        };
                        let clean_json = content_text
                            .trim()
                            .trim_start_matches("```json")
                            .trim_start_matches("```")
                            .trim_end_matches("```")
                            .trim();
                        serde_json::from_str::<Value>(clean_json).unwrap_or_else(|_| {
                            json!({
                                "action": "chat",
                                "data": {},
                                "raw_response": content_text
                            })
                        })
                    }
                    Err(e) => fallback_intent_parse(user_input, &format!("解析响应失败: {}", e)),
                }
            } else {
                let err_text = response.text().await.unwrap_or_default();
                fallback_intent_parse(user_input, &format!("API 返回错误: {}", err_text))
            }
        }
        Err(e) => fallback_intent_parse(user_input, &format!("网络请求失败或未配置Key: {}", e)),
    };

    let action = parsed_result["action"].as_str().unwrap_or("chat");
    let data = &parsed_result["data"];

    match action {
        "add" => {
            let title = data["title"].as_str().unwrap_or(user_input);
            let priority = data["priority"].as_str().unwrap_or("medium");
            let category = data["category"].as_str().unwrap_or("工作");
            let remind_at = data["remind_at"].as_str();

            let todo_id = db
                .add_todo(title, priority, category, remind_at, user_id)
                .map_err(|e| format!("写入数据库失败: {}", e))?;

            let reply = parsed_result["raw_response"]
                .as_str()
                .unwrap_or("已为您智能创建待办事项！");

            Ok(AiActionResult {
                action: "add".to_string(),
                data: json!({"id": todo_id, "title": title, "priority": priority, "category": category}),
                message: format!("🤖 {} \n\n✨ 任务详情：[{}] (分类: {}, 优先级: {})", reply, title, category, priority),
                should_refresh: true,
            })
        }
        "complete" => {
            let id = data["id"].as_i64().unwrap_or(0);
            if id > 0 {
                let _ = db.update_todo_status(id, true, user_id);
                Ok(AiActionResult {
                    action: "complete".to_string(),
                    data: json!({"id": id}),
                    message: format!("✅ 已成功标记任务 ID [{}] 为已完成！", id),
                    should_refresh: true,
                })
            } else {
                let reply = parsed_result["raw_response"].as_str().unwrap_or("收到指令，请提供具体的任务 ID 或明确说明要完成哪一项。");
                Ok(AiActionResult {
                    action: "chat".to_string(),
                    data: json!({}),
                    message: format!("🤖 {}", reply),
                    should_refresh: false,
                })
            }
        }
        "delete" => {
            let id = data["id"].as_i64().unwrap_or(0);
            if id > 0 {
                let _ = db.delete_todo(id, user_id);
                Ok(AiActionResult {
                    action: "delete".to_string(),
                    data: json!({"id": id}),
                    message: format!("🗑️ 已成功彻底删除任务 ID [{}]", id),
                    should_refresh: true,
                })
            } else {
                let reply = parsed_result["raw_response"].as_str().unwrap_or("未能删除，请说明要删除的具体任务 ID。");
                Ok(AiActionResult {
                    action: "chat".to_string(),
                    data: json!({}),
                    message: format!("🤖 {}", reply),
                    should_refresh: false,
                })
            }
        }

        _ => {
            let reply = parsed_result["raw_response"]
                .as_str()
                .unwrap_or("收到！我是您的 Todo Agent 助手，随时为您服务。");
            Ok(AiActionResult {
                action: "chat".to_string(),
                data: json!({}),
                message: format!("🤖 {}", reply),
                should_refresh: false,
            })
        }
    }
}

// 本地智能降级解析函数
fn fallback_intent_parse(user_input: &str, _reason: &str) -> Value {
    let lower = user_input.to_lowercase();
    if lower.contains("创建") || lower.contains("新建") || lower.contains("添加") || lower.contains("提醒") || lower.contains("开会") || lower.contains("待办") {
        let clean_title = user_input
            .replace("帮我", "")
            .replace("新建", "")
            .replace("创建", "")
            .replace("添加", "")
            .replace("一个", "")
            .replace("待办", "")
            .replace("任务", "")
            .trim()
            .to_string();
        let title = if clean_title.is_empty() { "新待办事项".to_string() } else { clean_title };
        let priority = if lower.contains("紧急") || lower.contains("高") || lower.contains("重要") { "high" } else { "medium" };
        let category = if lower.contains("学习") { "学习" } else if lower.contains("生活") { "生活" } else { "工作" };

        json!({
            "action": "add",
            "data": {
                "title": title,
                "priority": priority,
                "category": category
            },
            "raw_response": "已识别到您的待办指令，已自动完成分析与录入！"
        })
    } else {
        json!({
            "action": "chat",
            "data": {},
            "raw_response": format!("您好！我收到了您的消息：\"{}\"。我可以帮您创建、管理和记录待办事项，随时告诉我您的任务需求吧！", user_input)
        })
    }
}

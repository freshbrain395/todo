use reqwest::Client;
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use std::time::Duration;
use crate::repository::{todo as todo_repo, DbState};

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

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ChatMessage {
    pub role: String,
    pub content: String,
}

const DEFAULT_SYSTEM_PROMPT: &str = r#"你是一个待办事项智能助手。根据用户的自然语言输入，解析其意图并返回固定格式的 JSON 对象（不要添加任何 markdown 代码块标记以外的文字）。
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

pub fn default_system_prompt() -> &'static str {
    DEFAULT_SYSTEM_PROMPT
}

pub async fn ensure_ollama_running(base_url: &str) {
    if !base_url.contains("11434") {
        return;
    }

    let check_url = "http://127.0.0.1:11434/api/tags";
    let client = Client::builder()
        .timeout(Duration::from_millis(800))
        .build();

    if let Ok(c) = client {
        if c.get(check_url).send().await.is_ok() {
            return;
        }
    }

    #[cfg(target_os = "windows")]
    {
        use std::os::windows::process::CommandExt;
        const CREATE_NO_WINDOW: u32 = 0x08000000;
        let _ = std::process::Command::new("ollama")
            .arg("serve")
            .creation_flags(CREATE_NO_WINDOW)
            .spawn();
    }

    #[cfg(not(target_os = "windows"))]
    {
        let _ = std::process::Command::new("ollama")
            .arg("serve")
            .spawn();
    }

    if let Ok(c) = Client::builder()
        .timeout(Duration::from_millis(500))
        .build()
    {
        for _ in 0..12 {
            tokio::time::sleep(Duration::from_millis(500)).await;
            if c.get(check_url).send().await.is_ok() {
                break;
            }
        }
    }
}

pub async fn fetch_models(base_url: String, api_key: String) -> Result<Vec<String>, String> {
    ensure_ollama_running(&base_url).await;
    let clean_url = base_url.trim().trim_end_matches('/').to_string();
    let api_url = if clean_url.contains("11434") {
        if !clean_url.ends_with("/api") && !clean_url.ends_with("/v1") {
            format!("{}/api/tags", clean_url)
        } else if clean_url.ends_with("/api") {
            format!("{}/tags", clean_url)
        } else {
            format!("{}/models", clean_url)
        }
    } else {
        if !clean_url.ends_with("/v1") && !clean_url.contains("/models") {
            format!("{}/models", clean_url)
        } else if clean_url.ends_with("/v1") {
            format!("{}/models", clean_url)
        } else {
            clean_url
        }
    };

    let client = Client::builder()
        .timeout(Duration::from_secs(10))
        .build()
        .map_err(|e| format!("HTTP客户端初始化失败: {}", e))?;

    let mut req = client.get(&api_url);
    if !api_key.trim().is_empty() {
        req = req.header("Authorization", format!("Bearer {}", api_key.trim()));
    }

    let resp = req.send().await.map_err(|e| format!("网络请求失败: {}", e))?;
    if !resp.status().is_success() {
        return Err(format!("HTTP 状态错误: {}", resp.status()));
    }

    let json_val: Value = resp.json().await.map_err(|e| format!("JSON解析失败: {}", e))?;

    let mut model_names = Vec::new();
    if let Some(data_arr) = json_val.get("data").and_then(|v| v.as_array()) {
        for m in data_arr {
            if let Some(id) = m.get("id").and_then(|v| v.as_str()) {
                model_names.push(id.to_string());
            }
        }
    } else if let Some(models_arr) = json_val.get("models").and_then(|v| v.as_array()) {
        for m in models_arr {
            if let Some(name) = m.get("name").and_then(|v| v.as_str()) {
                model_names.push(name.to_string());
            }
        }
    }

    if model_names.is_empty() {
        return Err("解析成功但未发现任何可用模型".to_string());
    }

    Ok(model_names)
}

pub async fn parse_intent_and_execute(
    user_input: &str,
    config: &LlmConfig,
    db: &DbState,
    user_id: Option<i64>,
    system_prompt: Option<&str>,
    history: Option<&[ChatMessage]>,
) -> Result<AiActionResult, String> {
    ensure_ollama_running(&config.base_url).await;
    let client = Client::builder()
        .timeout(Duration::from_secs(15))
        .build()
        .map_err(|e| e.to_string())?;

    let system_prompt = match system_prompt {
        Some(extra) => format!("{}\n\n{}", DEFAULT_SYSTEM_PROMPT, extra),
        None => DEFAULT_SYSTEM_PROMPT.to_string(),
    };

    let url = if config.provider == "siliconflow" {
        format!("{}/chat/completions", config.base_url.trim_end_matches('/'))
    } else {
        format!("{}/api/generate", config.base_url.trim_end_matches('/'))
    };

    let body = if config.provider == "siliconflow" {
        let mut messages = vec![json!({"role": "system", "content": system_prompt})];
        if let Some(h) = history {
            for m in h {
                messages.push(json!({"role": m.role, "content": m.content}));
            }
        }
        messages.push(json!({"role": "user", "content": user_input}));
        let mut body = json!({
            "model": config.model,
            "messages": messages,
            "response_format": {"type": "json_object"},
            "temperature": 0.2
        });
        if config.enable_thinking {
            body["enable_thinking"] = json!(true);
        }
        body
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

    let display_config = crate::service::display_config::load_display_config();
    let ai_prefix = &display_config.ai_prefix;

    match action {
        "add" => {
            let title = data["title"].as_str().unwrap_or(user_input);
            let priority = data["priority"].as_str().unwrap_or("medium");
            let category = data["category"].as_str().unwrap_or("工作");
            let remind_at = data["remind_at"].as_str();

            let todo_id = todo_repo::add_todo(db, title, priority, category, remind_at, user_id)
                .map_err(|e| format!("写入数据库失败: {}", e))?;

            let reply = parsed_result["raw_response"]
                .as_str()
                .unwrap_or("已为您智能创建待办事项！");

            Ok(AiActionResult {
                action: "add".to_string(),
                data: json!({"id": todo_id, "title": title, "priority": priority, "category": category}),
                message: format!("{} {} \n\n✨ 任务详情：[{}] (分类: {}, 优先级: {})", ai_prefix, reply, title, category, priority),
                should_refresh: true,
            })
        }
        "complete" => {
            let id = data["id"].as_i64().unwrap_or(0);
            if id > 0 {
                let _ = todo_repo::update_todo_status(db, id, true, user_id);
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
                    message: format!("{} {}", ai_prefix, reply),
                    should_refresh: false,
                })
            }
        }
        "delete" => {
            let id = data["id"].as_i64().unwrap_or(0);
            if id > 0 {
                let _ = todo_repo::delete_todo(db, id, user_id);
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
                    message: format!("{} {}", ai_prefix, reply),
                    should_refresh: false,
                })
            }
        }

        "query" => {
            let todos = todo_repo::get_todos(db, "all", "", user_id).unwrap_or_default();
            let mut msg = String::from("📋 已为您查询到的待办事项列表：\n");
            if todos.is_empty() {
                msg.push_str("（暂无任何待办事项）");
            } else {
                for t in todos {
                    let status = if t.completed { "[✔ 已完成]" } else { "[  未完成]" };
                    msg.push_str(&format!("  * ID {:<3} {} : [{}] (分类: {}, 优先级: {})\n", t.id, status, t.title, t.category, t.priority));
                }
            }
            Ok(AiActionResult {
                action: "query".to_string(),
                data: json!({}),
                message: msg,
                should_refresh: false,
            })
        }

        _ => {
            let reply = parsed_result["raw_response"]
                .as_str()
                .unwrap_or("收到！我是您的 Todo Agent 助手，随时为您服务。");
            Ok(AiActionResult {
                action: "chat".to_string(),
                data: json!({}),
                message: format!("{} {}", ai_prefix, reply),
                should_refresh: false,
            })
        }
    }
}

fn fallback_intent_parse(user_input: &str, _reason: &str) -> Value {
    let lower = user_input.to_lowercase();
    if lower.contains("列出") || lower.contains("查看") || lower.contains("显示") || lower.contains("查询") || lower.contains("所有待办") || lower.contains("所有任务") || lower.contains("待办列表") {
        json!({
            "action": "query",
            "data": {},
            "raw_response": "已为您查询待办事项！"
        })
    } else if lower.contains("创建") || lower.contains("新建") || lower.contains("添加") || lower.contains("提醒") || lower.contains("开会") || lower.starts_with("记下") || lower.contains("明早") || lower.contains("明天") {
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

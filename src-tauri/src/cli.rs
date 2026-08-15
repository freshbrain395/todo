use std::io::{self, Write};
use clap::{Parser, Subcommand};
use inquire::Autocomplete;
use inquire::autocompletion::Replacement;
use inquire::CustomUserError;
use crate::api;
use crate::repository::DbState;
use crate::service::ai::{self as ai_service, ChatMessage, LlmConfig};

#[derive(Clone, Debug)]
pub struct SlashCommand {
    pub name: &'static str,
    pub description: &'static str,
}

pub const SLASH_COMMANDS: &[SlashCommand] = &[
    SlashCommand { name: "/help", description: "显示可用命令帮助" },
    SlashCommand { name: "/todo", description: "创建待办任务 (/todo <标题>)" },
    SlashCommand { name: "/add", description: "新建待办任务 (/add <标题>)" },
    SlashCommand { name: "/list", description: "查看所有待办任务" },
    SlashCommand { name: "/done", description: "完成待办任务 (/done <ID>)" },
    SlashCommand { name: "/undone", description: "撤销完成状态 (/undone <ID>)" },
    SlashCommand { name: "/delete", description: "删除待办任务 (/delete <ID>)" },
    SlashCommand { name: "/chat", description: "切换到常规 AI 聊天模式" },
    SlashCommand { name: "/prompt", description: "选择并执行 Prompt 模板" },
    SlashCommand { name: "/agent", description: "切换并进入 Agent 角色模式" },
    SlashCommand { name: "/skill", description: "切换并启用 Skill 技能模式" },
    SlashCommand { name: "/provider", description: "管理/切换模型供应商" },
    SlashCommand { name: "/model", description: "查看/切换当前 LLM 模型" },
    SlashCommand { name: "/clear", description: "清空当前对话上下文历史" },
    SlashCommand { name: "/cls", description: "清空控制台屏幕" },
    SlashCommand { name: "/quit", description: "退出命令行程序" },
    SlashCommand { name: "/exit", description: "退出命令行程序" },
];

#[derive(Clone, Default)]
pub struct SlashCommandCompleter;

impl Autocomplete for SlashCommandCompleter {
    fn get_suggestions(&mut self, input: &str) -> Result<Vec<String>, CustomUserError> {
        if input.starts_with('/') {
            let filter = input.to_lowercase();
            let matches: Vec<String> = SLASH_COMMANDS
                .iter()
                .filter(|c| {
                    c.name.to_lowercase().starts_with(&filter)
                        || c.name.to_lowercase().contains(&filter)
                        || c.description.to_lowercase().contains(&filter.trim_start_matches('/'))
                })
                .map(|c| format!("{:<14} {}", c.name, c.description))
                .collect();
            Ok(matches)
        } else {
            Ok(vec![])
        }
    }

    fn get_completion(
        &mut self,
        _input: &str,
        highlighted_suggestion: Option<String>,
    ) -> Result<Replacement, CustomUserError> {
        if let Some(sug) = highlighted_suggestion {
            let cmd_name = sug.split_whitespace().next().unwrap_or("").to_string();
            let completion_text = match cmd_name.as_str() {
                "/clear" | "/cls" | "/exit" | "/quit" | "/help" | "/mode" | "/chat" => cmd_name,
                _ => format!("{} ", cmd_name),
            };
            Ok(Replacement::Some(completion_text))
        } else {
            Ok(Replacement::None)
        }
    }
}

fn load_llm_config(db: &DbState) -> LlmConfig {
    api::get_llm_config_direct(db)
        .ok()
        .flatten()
        .and_then(|v| serde_json::from_str(&v).ok())
        .unwrap_or_default()
}

fn save_llm_config(db: &DbState, config: &LlmConfig) {
    if let Ok(v) = serde_json::to_string(config) {
        let _ = api::save_llm_config_direct(v, db);
    }
}

struct AgentDef {
    id: &'static str,
    title: &'static str,
    role: &'static str,
}

struct ProviderPreset {
    id: &'static str,
    name: &'static str,
    base_url: &'static str,
    model: &'static str,
}

const PRESET_PROVIDERS: &[ProviderPreset] = &[
    ProviderPreset {
        id: "siliconflow",
        name: "SiliconFlow (硅基流动云端 API)",
        base_url: "https://api.siliconflow.cn/v1",
        model: "deepseek-ai/DeepSeek-V4-Flash",
    },
    ProviderPreset {
        id: "ollama",
        name: "Native Ollama (本地大模型服务)",
        base_url: "http://localhost:11434",
        model: "llama3:latest",
    },
    ProviderPreset {
        id: "openai",
        name: "OpenAI Compatible (OpenAI 兼容协议)",
        base_url: "https://api.openai.com/v1",
        model: "gpt-4o-mini",
    },
    ProviderPreset {
        id: "deepseek",
        name: "DeepSeek Official (DeepSeek 官方 API)",
        base_url: "https://api.deepseek.com/v1",
        model: "deepseek-chat",
    },
];

const AGENTS: &[AgentDef] = &[
    AgentDef { id: "task-manager", title: "任务管理专家", role: "你是一位高效的待办任务管理专家，善于用系统化方法帮助用户规划、分类、排序和复盘任务，请结合我现有待办清单给出可执行建议。" },
    AgentDef { id: "planner", title: "日程规划师", role: "你是一位日程规划师，擅长根据用户的目标、时间与优先级合理分配每天的计划，输出清晰的时间段安排。" },
    AgentDef { id: "reviewer", title: "总结复盘助手", role: "你是一位总结复盘助手，擅长提炼已完成与未完成事项，输出结构化的周报与改进行动项。" },
];

#[derive(Debug, Clone, Copy, PartialEq)]
enum ModeKind {
    Chat,
    Prompt,
    Agent,
    Skill,
}

struct SessionState {
    config: LlmConfig,
    mode: ModeKind,
    mode_item: String,
    history: Vec<ChatMessage>,
}

impl SessionState {
    fn new(config: LlmConfig) -> Self {
        SessionState {
            config,
            mode: ModeKind::Chat,
            mode_item: String::new(),
            history: Vec::new(),
        }
    }

    fn mode_label(&self) -> String {
        match self.mode {
            ModeKind::Chat => "chat".to_string(),
            ModeKind::Prompt => format!("prompt: {}", self.mode_item),
            ModeKind::Agent => format!("agent: {}", self.mode_item),
            ModeKind::Skill => format!("skill: {}", self.mode_item),
        }
    }

    fn build_system_prompt(&self, db: &DbState) -> String {
        let base = ai_service::default_system_prompt();
        match self.mode {
            ModeKind::Chat | ModeKind::Prompt => base.to_string(),
            ModeKind::Agent => {
                let role = AGENTS
                    .iter()
                    .find(|a| a.id == self.mode_item)
                    .map(|a| a.role)
                    .unwrap_or("");
                format!("{}\n\n同时，请扮演以下角色进行回答，保持简洁务实：\n{}", base, role)
            }
            ModeKind::Skill => {
                let skills = api::get_ai_skills_direct(db).unwrap_or_default();
                let prompt = skills
                    .iter()
                    .find(|s| s["id"].as_str().unwrap_or("") == self.mode_item)
                    .and_then(|s| s["systemPrompt"].as_str())
                    .unwrap_or("");
                format!("{}\n\n请应用以下技能处理用户输入：\n{}", base, prompt)
            }
        }
    }
}

#[derive(Parser)]
#[command(name = "todo_agent")]
#[command(about = "Todo Agent CLI & GUI", long_about = None)]
pub struct Cli {
    #[command(subcommand)]
    pub command: Option<Commands>,
}

#[derive(Subcommand, Debug)]
pub enum Commands {
    /// 进入交互式命令行模式 (Interactive Shell)
    Interactive,
    /// 列出待办事项
    List {
        /// 状态过滤: all, pending, completed
        #[arg(short, long, default_value = "all")]
        filter: String,

        /// 关键字搜索
        #[arg(short, long, default_value = "")]
        search: String,
    },
    /// 添加待办事项
    Add {
        /// 待办事项标题
        title: String,

        /// 优先级: high, medium, low
        #[arg(short, long, default_value = "medium")]
        priority: String,

        /// 分类
        #[arg(short, long, default_value = "工作")]
        category: String,

        /// 提醒时间 (格式: YYYY-MM-DD HH:MM)
        #[arg(short, long)]
        remind: Option<String>,
    },
    /// 标记待办事项为已完成
    Done {
        /// 待办事项 ID
        id: i64,
    },
    /// 标记待办事项为未完成
    Undone {
        /// 待办事项 ID
        id: i64,
    },
    /// 删除待办事项
    Delete {
        /// 待办事项 ID
        id: i64,
    },
    /// 使用 AI 智能助手处理任务指令
    Ai {
        /// 自然语言命令，例如: "帮我添加明天下午3点开会的任务"
        prompt: String,
    },
}

pub async fn handle_cli(cli: Cli, db: &DbState) {
    match cli.command {
        Some(Commands::Interactive) | None => {
            run_interactive_shell(db).await;
        }
        Some(cmd) => {
            execute_command(cmd, db, None).await;
        }
    }
}

pub async fn execute_command(command: Commands, db: &DbState, config: Option<&LlmConfig>) {
    match command {
        Commands::Interactive => {
            println!("当前已处于交互式命令行界面。");
        }
        Commands::List { filter, search } => {
            match api::get_todos_direct(filter, search, None, db) {
                Ok(todos) => {
                    if todos.is_empty() {
                        println!("没有找到相关待办事项。");
                    } else {
                        println!("{:<4} | {:<5} | {:<8} | {:<10} | {:<30}", "ID", "状态", "优先级", "分类", "标题");
                        println!("{:-<70}", "");
                        for t in todos {
                            let status = if t.completed { "[✔]" } else { "[ ]" };
                            println!("{:<4} | {:<5} | {:<8} | {:<10} | {:<30}", t.id, status, t.priority, t.category, t.title);
                        }
                    }
                }
                Err(e) => eprintln!("获取待办列表失败: {}", e),
            }
        }
        Commands::Add { title, priority, category, remind } => {
            match api::add_todo_direct(title.clone(), priority, category, remind, None, db) {
                Ok(id) => println!("成功添加待办事项 [ID: {}]: {}", id, title),
                Err(e) => eprintln!("添加待办事项失败: {}", e),
            }
        }
        Commands::Done { id } => {
            match api::update_todo_status_direct(id, true, None, db) {
                Ok(true) => println!("待办事项 [ID: {}] 已标记为完成。", id),
                Ok(false) => println!("未找到待办事项 [ID: {}]。", id),
                Err(e) => eprintln!("更新状态失败: {}", e),
            }
        }
        Commands::Undone { id } => {
            match api::update_todo_status_direct(id, false, None, db) {
                Ok(true) => println!("待办事项 [ID: {}] 已标记为未完成。", id),
                Ok(false) => println!("未找到待办事项 [ID: {}]。", id),
                Err(e) => eprintln!("更新状态失败: {}", e),
            }
        }
        Commands::Delete { id } => {
            match api::delete_todo_direct(id, None, db) {
                Ok(true) => println!("成功删除待办事项 [ID: {}]。", id),
                Ok(false) => println!("未找到待办事项 [ID: {}]。", id),
                Err(e) => eprintln!("删除待办事项失败: {}", e),
            }
        }
        Commands::Ai { prompt } => {
            println!("正在调用 AI 处理指令: \"{}\"...", prompt);
            let config = config.cloned().unwrap_or_default();
            match api::execute_ai_command_direct(prompt, config, None, None, None, db).await {
                Ok(res) => println!("\nAI 执行结果 [{}]:\n{}", res.action, res.message),
                Err(e) => eprintln!("AI 执行失败: {}", e),
            }
        }
    }
}

pub async fn run_interactive_shell(db: &DbState) {
    let mut shell = SessionState::new(load_llm_config(db));
    let config_path = crate::service::display_config::get_display_config_path();

    println!("==================================================");
    println!("  欢迎使用 Todo Agent 交互式命令行界面 (Interactive Mode)");
    println!("  直接输入文字即可与 AI 聊天（支持多轮上下文，自动识别待办操作）");
    println!("  ⚡ 输入 '/' 实时弹出 Slash Commands 自动补全菜单 (支持 ↑/↓ 选择, Tab/Enter 确认)");
    println!("  常用指令: /todo | /list | /done | /delete | /prompt | /agent | /skill");
    println!("  显示配置文件: {}", config_path.display());
    println!("  输入 '/help' 查看帮助，输入 'exit' 或 'quit' 退出");
    println!("==================================================");
    println!("当前模型: {} ({}) | 当前模式: {}", shell.config.model, shell.config.provider, shell.mode_label());
    println!();

    let completer = SlashCommandCompleter;
    loop {
        let display_config = api::get_display_config_direct();
        let prompt_str = format!("{}>", display_config.user_prefix);

        let input_res = inquire::Text::new(&prompt_str)
            .with_autocomplete(completer.clone())
            .with_help_message("输入文本发送 AI；输入 '/' 弹出命令补全 (↑/↓ 选择, Tab 自动填充, Enter 提交)")
            .prompt();

        let line = match input_res {
            Ok(val) => val,
            Err(_) => {
                println!("已退出交互式命令行界面。再见！");
                break;
            }
        };

        let input = line.trim();
        if input.is_empty() {
            continue;
        }

        if input.eq_ignore_ascii_case("exit")
            || input.eq_ignore_ascii_case("quit")
            || input.eq_ignore_ascii_case("/exit")
            || input.eq_ignore_ascii_case("/quit")
        {
            println!("已退出交互式命令行界面。再见！");
            break;
        }

        if input.starts_with('/') {
            handle_shell_command(input, db, &mut shell).await;
            println!();
            continue;
        }

        shell.history.push(ChatMessage {
            role: "user".to_string(),
            content: input.to_string(),
        });
        send_to_ai(input, db, &mut shell).await;
        println!();
    }
}

async fn send_to_ai(input: &str, db: &DbState, shell: &mut SessionState) {
    let system_prompt = shell.build_system_prompt(db);
    let result = api::execute_ai_command_direct(
        input.to_string(),
        shell.config.clone(),
        None,
        Some(shell.history.clone()),
        Some(system_prompt),
        db,
    )
    .await;

    match result {
        Ok(res) => {
            if res.action == "chat" {
                println!("{}", res.message);
            } else {
                println!("\nAI 执行结果 [{}]:\n{}", res.action, res.message);
            }
            shell.history.push(ChatMessage {
                role: "assistant".to_string(),
                content: res.message.clone(),
            });
        }
        Err(e) => eprintln!("AI 执行失败: {}", e),
    }
}

fn find_agent(keyword: &str) -> Option<&'static AgentDef> {
    AGENTS
        .iter()
        .find(|a| a.id == keyword || a.title.contains(keyword))
}

fn list_prompts(db: &DbState) {
    let prompts = api::get_ai_prompts_direct(db).unwrap_or_default();
    let path = crate::service::ai_config::get_prompts_file_path();
    println!("可用 Prompts (共 {} 个, 动态文件: {}):", prompts.len(), path.display());
    for (i, p) in prompts.iter().enumerate() {
        let id = p["id"].as_str().unwrap_or("");
        let title = p["title"].as_str().unwrap_or("");
        let text = p["text"].as_str().unwrap_or("");
        println!("  {}. [{}] {} - {}", i + 1, id, title, text);
    }
    println!("使用 '/prompt <名称>' 切换到对应 Prompt 模式。");
}

fn list_agents() {
    println!("可用 Agents (共 {} 个):", AGENTS.len());
    for (i, a) in AGENTS.iter().enumerate() {
        println!("  {}. [{}] {}", i + 1, a.id, a.title);
    }
    println!("使用 '/agent <名称>' 切换到对应 Agent 模式。");
}

fn list_skills(db: &DbState) {
    let skills = api::get_ai_skills_direct(db).unwrap_or_default();
    let dir = crate::service::ai_config::get_skills_dir_path();
    println!("可用 Skills (共 {} 个, 动态目录: {}):", skills.len(), dir.display());
    for (i, s) in skills.iter().enumerate() {
        let id = s["id"].as_str().unwrap_or("");
        let title = s["title"].as_str().unwrap_or("");
        let desc = s["description"].as_str().unwrap_or("");
        println!("  {}. [{}] {} - {}", i + 1, id, title, desc);
    }
    println!("使用 '/skill <名称>' 切换到对应 Skill 模式。");
}

async fn enter_prompt_mode(db: &DbState, shell: &mut SessionState, keyword: &str) {
    let prompts = api::get_ai_prompts_direct(db).unwrap_or_default();
    let matched = prompts.iter().find(|p| {
        let id = p["id"].as_str().unwrap_or("");
        let title = p["title"].as_str().unwrap_or("");
        id.eq_ignore_ascii_case(keyword) || title.contains(keyword)
    });

    match matched {
        Some(p) => {
            let id = p["id"].as_str().unwrap_or("");
            let title = p["title"].as_str().unwrap_or("");
            let text = p["text"].as_str().unwrap_or("");
            shell.mode = ModeKind::Prompt;
            shell.mode_item = id.to_string();
            shell.history.clear();
            shell.history.push(ChatMessage {
                role: "user".to_string(),
                content: text.to_string(),
            });
            println!("已切换到 Prompt 模式: {}，正在执行模板...", title);
            send_to_ai(text, db, shell).await;
        }
        None => {
            eprintln!("未找到匹配的 Prompt，使用 '/prompt list' 查看可用项。");
        }
    }
}

async fn enter_agent_mode(shell: &mut SessionState, keyword: &str) {
    match find_agent(keyword) {
        Some(def) => {
            shell.mode = ModeKind::Agent;
            shell.mode_item = def.id.to_string();
            shell.history.clear();
            println!("已切换到 Agent 模式: {}，请描述你的需求。", def.title);
        }
        None => {
            eprintln!("未找到匹配的 Agent，使用 '/agent list' 查看可用项。");
        }
    }
}

async fn enter_skill_mode(db: &DbState, shell: &mut SessionState, keyword: &str) {
    let skills = api::get_ai_skills_direct(db).unwrap_or_default();
    let matched = skills.iter().find(|s| {
        let id = s["id"].as_str().unwrap_or("");
        let title = s["title"].as_str().unwrap_or("");
        id.eq_ignore_ascii_case(keyword) || title.contains(keyword)
    });

    match matched {
        Some(s) => {
            let id = s["id"].as_str().unwrap_or("");
            let title = s["title"].as_str().unwrap_or("");
            shell.mode = ModeKind::Skill;
            shell.mode_item = id.to_string();
            shell.history.clear();
            println!("已切换到 Skill 模式: {}，请描述你的需求。", title);
        }
        None => {
            eprintln!("未找到匹配的 Skill，使用 '/skill list' 查看可用项。");
        }
    }
}

async fn interactive_select_prompt(db: &DbState, shell: &mut SessionState) {
    let prompts = api::get_ai_prompts_direct(db).unwrap_or_default();
    if prompts.is_empty() {
        println!("暂无可用 Prompt 模板。");
        return;
    }
    let mut items: Vec<String> = prompts.iter().map(|p| {
        let id = p["id"].as_str().unwrap_or("");
        let title = p["title"].as_str().unwrap_or("");
        format!("[{}] {}", id, title)
    }).collect();
    items.push("❌ 取消".to_string());

    if let Ok(choice) = inquire::Select::new("请选择要执行的 Prompt 模板 (↑/↓ 选择, Enter 确认):", items).prompt() {
        if choice == "❌ 取消" { return; }
        if let Some(id_part) = choice.split(']').next() {
            let id = id_part.trim_start_matches('[');
            enter_prompt_mode(db, shell, id).await;
        }
    }
}

async fn interactive_select_agent(shell: &mut SessionState) {
    let mut items: Vec<String> = AGENTS.iter().map(|a| format!("[{}] {}", a.id, a.title)).collect();
    items.push("❌ 取消".to_string());

    if let Ok(choice) = inquire::Select::new("请选择要进入的 Agent 角色 (↑/↓ 选择, Enter 确认):", items).prompt() {
        if choice == "❌ 取消" { return; }
        if let Some(id_part) = choice.split(']').next() {
            let id = id_part.trim_start_matches('[');
            enter_agent_mode(shell, id).await;
        }
    }
}

async fn interactive_select_skill(db: &DbState, shell: &mut SessionState) {
    let skills = api::get_ai_skills_direct(db).unwrap_or_default();
    if skills.is_empty() {
        println!("暂无可用 Skill 技能。");
        return;
    }
    let mut items: Vec<String> = skills.iter().map(|s| {
        let id = s["id"].as_str().unwrap_or("");
        let title = s["title"].as_str().unwrap_or("");
        format!("[{}] {}", id, title)
    }).collect();
    items.push("❌ 取消".to_string());

    if let Ok(choice) = inquire::Select::new("请选择要启用的 Skill 技能 (↑/↓ 选择, Enter 确认):", items).prompt() {
        if choice == "❌ 取消" { return; }
        if let Some(id_part) = choice.split(']').next() {
            let id = id_part.trim_start_matches('[');
            enter_skill_mode(db, shell, id).await;
        }
    }
}

fn interactive_select_todo_done(db: &DbState) {
    let todos = api::get_todos_direct("all".to_string(), "".to_string(), None, db).unwrap_or_default();
    let pending: Vec<_> = todos.into_iter().filter(|t| !t.completed).collect();
    if pending.is_empty() {
        println!("当前没有未完成的待办事项。");
        return;
    }
    let mut items: Vec<String> = pending.iter().map(|t| format!("[ID: {}] {}", t.id, t.title)).collect();
    items.push("❌ 取消".to_string());

    if let Ok(choice) = inquire::Select::new("请选择要标记完成的待办事项 (↑/↓ 选择, Enter 确认):", items).prompt() {
        if choice == "❌ 取消" { return; }
        if let Some(id_str) = choice.split(']').next().and_then(|s| s.strip_prefix("[ID: ")) {
            if let Ok(id) = id_str.trim().parse::<i64>() {
                match api::update_todo_status_direct(id, true, None, db) {
                    Ok(true) => println!("待办事项 [ID: {}] 已标记为完成。", id),
                    Ok(false) => println!("未找到待办事项 [ID: {}]。", id),
                    Err(e) => eprintln!("更新状态失败: {}", e),
                }
            }
        }
    }
}

fn interactive_select_todo_delete(db: &DbState) {
    let todos = api::get_todos_direct("all".to_string(), "".to_string(), None, db).unwrap_or_default();
    if todos.is_empty() {
        println!("当前没有待办事项。");
        return;
    }
    let mut items: Vec<String> = todos.iter().map(|t| format!("[ID: {}] {} ({})", t.id, t.title, if t.completed { "已完成" } else { "未完成" })).collect();
    items.push("❌ 取消".to_string());

    if let Ok(choice) = inquire::Select::new("请选择要删除的待办事项 (↑/↓ 选择, Enter 确认):", items).prompt() {
        if choice == "❌ 取消" { return; }
        if let Some(id_str) = choice.split(']').next().and_then(|s| s.strip_prefix("[ID: ")) {
            if let Ok(id) = id_str.trim().parse::<i64>() {
                match api::delete_todo_direct(id, None, db) {
                    Ok(true) => println!("成功删除待办事项 [ID: {}]。", id),
                    Ok(false) => println!("未找到待办事项 [ID: {}]。", id),
                    Err(e) => eprintln!("删除待办事项失败: {}", e),
                }
            }
        }
    }
}

fn print_help() {
    println!("\n可用命令帮助:");
    println!("  直接输入文字        与 AI 聊天，支持多轮上下文，自动识别待办操作");
    println!("  /                   弹出交互式命令菜单（支持上下方向键 ↑/↓ 选择）");
    println!("  /mode               查看当前模式与模型");
    println!("  /chat               切换到对话模式（默认，多轮聊天）");
    println!("  /prompt list        列出可用 Prompt 模板 (源自 prompts.json 独立文件)");
    println!("  /prompt <名称>       使用模板进入 Prompt 模式（不传参数弹出选择菜单）");
    println!("  /agent list         列出可用 Agent 角色");
    println!("  /agent <名称>        使用角色进入 Agent 模式（不传参数弹出选择菜单）");
    println!("  /skill list         列出可用 Skills 技能 (源自 skills/ 独立文件夹)");
    println!("  /skill <名称>        使用技能进入 Skill 模式（不传参数弹出选择菜单）");
    println!("  /clear              清空当前对话历史");
    println!("  /list [--filter <all|pending|completed>] [--search <关键字>]");
    println!("  /add <标题> [--priority <high|medium|low>] [--category <分类>]");
    println!("  /done <ID>    完成待办");
    println!("  /undone <ID>  撤销完成");
    println!("  /delete <ID>  删除待办");
    println!("  /provider              查看当前模型供应商配置（不传参数弹出选择菜单）");
    println!("  /provider list         列出所有可用的模型供应商");
    println!("  /provider <id>         切换模型供应商 (如: ollama, siliconflow)");
    println!("  /provider key <key>    设置当前供应商的 API Key");
    println!("  /provider url <url>    设置当前供应商的 Base URL");
    println!("  /model                 查看当前使用的模型（不传参数弹出选择菜单）");
    println!("  /model list            列出所有可用模型");
    println!("  /model <模型名称>       切换到指定模型");
    println!("  exit / quit   退出程序\n");
}

fn list_todos_cli(db: &DbState, filter: &str, search: &str) {
    match api::get_todos_direct(filter.to_string(), search.to_string(), None, db) {
        Ok(todos) => {
            if todos.is_empty() {
                println!("没有找到相关待办事项。");
            } else {
                println!("{:<4} | {:<5} | {:<8} | {:<10} | {:<30}", "ID", "状态", "优先级", "分类", "标题");
                println!("{:-<70}", "");
                for t in todos {
                    let status = if t.completed { "[✔]" } else { "[ ]" };
                    println!("{:<4} | {:<5} | {:<8} | {:<10} | {:<30}", t.id, status, t.priority, t.category, t.title);
                }
            }
        }
        Err(e) => eprintln!("获取待办列表失败: {}", e),
    }
}

async fn show_interactive_slash_menu(db: &DbState, shell: &mut SessionState) {
    let options = vec![
        "💬 /chat         - 切换到对话模式（多轮聊天）",
        "📝 /prompt       - 交互式选择并运行 Prompt 模板",
        "🤖 /agent        - 交互式切换 Agent 角色模式",
        "⚡ /skill        - 交互式切换 Skill 技能模式",
        "📋 /list         - 查看所有待办事项列表",
        "➕ /add          - 交互式新建待办事项",
        "✅ /done         - 交互式标记待办事项完成",
        "🗑️ /delete       - 交互式删除待办事项",
        "🏢 /provider     - 管理与切换 AI 模型服务商",
        "🧠 /model        - 查看与切换当前 LLM 模型",
        "🧹 /clear        - 清空当前对话历史",
        "📺 /cls          - 清屏",
        "❓ /help         - 查看完整文字帮助",
        "🚪 /exit         - 退出 CLI 交互界面",
    ];

    let ans = match inquire::Select::new("⚡ 请使用上下方向键 (↑/↓) 选择命令 (按 Enter 确认):", options).prompt() {
        Ok(choice) => choice,
        Err(_) => {
            println!("已取消菜单选择。");
            return;
        }
    };

    if ans.starts_with("💬 /chat") {
        shell.mode = ModeKind::Chat;
        shell.mode_item.clear();
        shell.history.clear();
        println!("已切换到 chat 模式，历史已清空。");
    } else if ans.starts_with("📝 /prompt") {
        interactive_select_prompt(db, shell).await;
    } else if ans.starts_with("🤖 /agent") {
        interactive_select_agent(shell).await;
    } else if ans.starts_with("⚡ /skill") {
        interactive_select_skill(db, shell).await;
    } else if ans.starts_with("📋 /list") {
        list_todos_cli(db, "all", "");
    } else if ans.starts_with("➕ /add") {
        if let Ok(title) = inquire::Text::new("请输入待办事项标题:").prompt() {
            let title = title.trim();
            if !title.is_empty() {
                let _ = api::add_todo_direct(
                    title.to_string(),
                    "medium".to_string(),
                    "工作".to_string(),
                    None,
                    None,
                    db,
                );
                println!("✅ 成功创建待办事项: \"{}\"", title);
            }
        }
    } else if ans.starts_with("✅ /done") {
        interactive_select_todo_done(db);
    } else if ans.starts_with("🗑️ /delete") {
        interactive_select_todo_delete(db);
    } else if ans.starts_with("🏢 /provider") {
        handle_provider_command(&[], db, shell).await;
    } else if ans.starts_with("🧠 /model") {
        handle_model_command(&[], db, shell).await;
    } else if ans.starts_with("🧹 /clear") {
        shell.history.clear();
        println!("已清空对话历史。");
    } else if ans.starts_with("📺 /cls") {
        print!("\x1B[2J\x1B[1;1H");
        let _ = io::stdout().flush();
    } else if ans.starts_with("❓ /help") {
        print_help();
    } else if ans.starts_with("🚪 /exit") {
        println!("已退出交互式命令行界面。再见！");
        std::process::exit(0);
    }
}

async fn handle_shell_command(input: &str, db: &DbState, shell: &mut SessionState) {
    let parts: Vec<&str> = input.split_whitespace().collect();
    let arg = parts.get(1).copied().unwrap_or("");
    if parts.is_empty() {
        return;
    }
    match parts[0] {
        "/" | "/menu" => {
            show_interactive_slash_menu(db, shell).await;
        }
        "/help" | "/?" => {
            print_help();
        }
        "/mode" => {
            println!("当前模式: {} | 当前模型: {} (供应商: {})", shell.mode_label(), shell.config.model, shell.config.provider);
        }
        "/chat" => {
            shell.mode = ModeKind::Chat;
            shell.mode_item.clear();
            shell.history.clear();
            println!("已切换到 chat 模式，历史已清空。");
        }
        "/provider" => {
            handle_provider_command(&parts[1..], db, shell).await;
        }
        "/prompt" => {
            if arg.is_empty() {
                interactive_select_prompt(db, shell).await;
            } else if arg == "list" {
                list_prompts(db);
            } else {
                enter_prompt_mode(db, shell, arg).await;
            }
        }
        "/agent" => {
            if arg.is_empty() {
                interactive_select_agent(shell).await;
            } else if arg == "list" {
                list_agents();
            } else {
                enter_agent_mode(shell, arg).await;
            }
        }
        "/skill" => {
            if arg.is_empty() {
                interactive_select_skill(db, shell).await;
            } else if arg == "list" {
                list_skills(db);
            } else {
                enter_skill_mode(db, shell, arg).await;
            }
        }
        "/clear" => {
            shell.history.clear();
            println!("已清空对话历史。");
        }
        "/cls" => {
            print!("\x1B[2J\x1B[1;1H");
            let _ = io::stdout().flush();
        }
        "/model" => {
            handle_model_command(&parts[1..], db, shell).await;
        }
        "/todo" | "/add" => {
            let title = input.trim_start_matches("/todo").trim_start_matches("/add").trim();
            if title.is_empty() {
                if let Ok(new_title) = inquire::Text::new("请输入待办事项标题:").prompt() {
                    let new_title = new_title.trim();
                    if !new_title.is_empty() {
                        let _ = api::add_todo_direct(new_title.to_string(), "medium".to_string(), "工作".to_string(), None, None, db);
                        println!("✅ 成功创建待办事项: \"{}\"", new_title);
                    }
                }
            } else {
                let _ = api::add_todo_direct(title.to_string(), "medium".to_string(), "工作".to_string(), None, None, db);
                println!("✅ 成功创建待办事项: \"{}\"", title);
            }
        }
        "/list" => {
            list_todos_cli(db, "all", "");
        }
        "/done" => {
            if arg.is_empty() {
                interactive_select_todo_done(db);
            } else if let Ok(id) = arg.parse::<i64>() {
                match api::update_todo_status_direct(id, true, None, db) {
                    Ok(true) => println!("待办事项 [ID: {}] 已标记为完成。", id),
                    Ok(false) => println!("未找到待办事项 [ID: {}]。", id),
                    Err(e) => eprintln!("更新状态失败: {}", e),
                }
            } else {
                println!("用法: /done <ID>");
            }
        }
        "/undone" => {
            if let Ok(id) = arg.parse::<i64>() {
                match api::update_todo_status_direct(id, false, None, db) {
                    Ok(true) => println!("待办事项 [ID: {}] 已标记为未完成。", id),
                    Ok(false) => println!("未找到待办事项 [ID: {}]。", id),
                    Err(e) => eprintln!("更新状态失败: {}", e),
                }
            } else {
                println!("用法: /undone <ID>");
            }
        }
        "/delete" => {
            if arg.is_empty() {
                interactive_select_todo_delete(db);
            } else if let Ok(id) = arg.parse::<i64>() {
                match api::delete_todo_direct(id, None, db) {
                    Ok(true) => println!("成功删除待办事项 [ID: {}]。", id),
                    Ok(false) => println!("未找到待办事项 [ID: {}]。", id),
                    Err(e) => eprintln!("删除待办事项失败: {}", e),
                }
            } else {
                println!("用法: /delete <ID>");
            }
        }
        "/quit" | "/exit" => {
            println!("已退出交互式命令行界面。再见！");
            std::process::exit(0);
        }
        other => {
            let raw = input.trim_start_matches('/');
            let mut raw_args = vec!["todo_agent".to_string()];
            if let Some(parsed) = shlex::split(raw) {
                raw_args.extend(parsed);
            } else {
                eprintln!("解析输入指令失败，请检查引号是否匹配。");
                return;
            }
            match Cli::try_parse_from(raw_args) {
                Ok(cli_item) => {
                    if let Some(cmd) = cli_item.command {
                        execute_command(cmd, db, Some(&shell.config)).await;
                    } else {
                        println!("未知命令 '{}'，输入 '/help' 查看帮助。", other);
                    }
                }
                Err(e) => {
                    println!("{}", e.render().ansi());
                }
            }
        }
    }
}

fn switch_provider(target_id: &str, db: &DbState, shell: &mut SessionState) {
    let db_providers = api::get_ai_providers_direct(db).unwrap_or_default();
    let db_match = db_providers.iter().find(|p| p["id"].as_str().unwrap_or("").eq_ignore_ascii_case(target_id));

    if let Some(p) = db_match {
        shell.config.provider = p["id"].as_str().unwrap_or(target_id).to_string();
        if let Some(url) = p["base_url"].as_str() {
            if !url.is_empty() { shell.config.base_url = url.to_string(); }
        }
        if let Some(key) = p["api_key"].as_str() {
            if !key.is_empty() { shell.config.api_key = key.to_string(); }
        }
        if let Some(model) = p["model"].as_str() {
            if !model.is_empty() { shell.config.model = model.to_string(); }
        }
    } else if let Some(preset) = PRESET_PROVIDERS.iter().find(|p| p.id.eq_ignore_ascii_case(target_id)) {
        shell.config.provider = preset.id.to_string();
        shell.config.base_url = preset.base_url.to_string();
        shell.config.model = preset.model.to_string();
    } else {
        shell.config.provider = target_id.to_string();
    }

    save_llm_config(db, &shell.config);
    println!("\n✅ 已成功切换模型供应商为: [{}]", shell.config.provider);
    println!("   Base URL : {}", shell.config.base_url);
    println!("   Model    : {}", shell.config.model);
    if shell.config.api_key.is_empty() && target_id != "ollama" {
        println!("   ⚠️ 注意: 当前 API Key 为空。请运行 '/provider key <API_KEY>' 配置密钥。");
    }
}

async fn handle_provider_command(args: &[&str], db: &DbState, shell: &mut SessionState) {
    if args.is_empty() {
        let mut options = Vec::new();
        let mut default_idx = 0;

        for (idx, preset) in PRESET_PROVIDERS.iter().enumerate() {
            let is_current = preset.id.eq_ignore_ascii_case(&shell.config.provider);
            if is_current {
                default_idx = idx;
            }
            let mark = if is_current { " [当前激活]" } else { "" };
            let label = format!("{} ({}){}", preset.name, preset.id, mark);
            options.push(label);
        }

        let ans = inquire::Select::new("请使用 ↑/↓ 方向键选择模型供应商 (按 Enter 确认):", options)
            .with_starting_cursor(default_idx)
            .prompt();

        match ans {
            Ok(choice) => {
                if let Some(pos) = PRESET_PROVIDERS.iter().position(|p| choice.contains(p.id)) {
                    let selected_id = PRESET_PROVIDERS[pos].id;
                    switch_provider(selected_id, db, shell);

                    // 步骤 2: 交互式配置 API Key (对非 Ollama 本地模型)
                    if selected_id != "ollama" {
                        let prompt_msg = if shell.config.api_key.is_empty() {
                            "\n🔑 请输入 API Key (直接按 Enter 跳过/保持为空):"
                        } else {
                            "\n🔑 请输入 API Key (直接按 Enter 保持当前配置):"
                        };
                        if let Ok(input_key) = inquire::Text::new(prompt_msg).prompt() {
                            let trimmed = input_key.trim();
                            if !trimmed.is_empty() {
                                shell.config.api_key = trimmed.to_string();
                                save_llm_config(db, &shell.config);
                                println!("✅ 已更新 API Key。");
                            }
                        }
                    }

                    // 步骤 3: 交互式选择模型
                    println!();
                    handle_model_command(&[], db, shell).await;
                }
            }
            Err(_) => {
                println!("已取消选择。");
            }
        }
        return;
    }

    match args[0] {
        "list" => {
            println!("\n可用模型供应商列表:");
            let db_providers = api::get_ai_providers_direct(db).unwrap_or_default();
            for preset in PRESET_PROVIDERS {
                let db_match = db_providers.iter().find(|p| p["id"].as_str().unwrap_or("").eq_ignore_ascii_case(preset.id));
                let base_url = db_match.and_then(|p| p["base_url"].as_str()).filter(|s| !s.is_empty()).unwrap_or(preset.base_url);
                let model = db_match.and_then(|p| p["model"].as_str()).filter(|s| !s.is_empty()).unwrap_or(preset.model);
                let has_key = db_match.map(|p| !p["api_key"].as_str().unwrap_or("").is_empty()).unwrap_or(false);

                let is_current = preset.id.eq_ignore_ascii_case(&shell.config.provider);
                let mark = if is_current { " <- [当前激活]" } else { "" };
                let key_info = if has_key || (is_current && !shell.config.api_key.is_empty()) {
                    "API Key: 已配置"
                } else if preset.id == "ollama" {
                    "API Key: 不需要"
                } else {
                    "API Key: 未配置"
                };

                println!("  * [{}] {} {}", preset.id, preset.name, mark);
                println!("    Base URL: {} | 默认模型: {} | {}", base_url, model, key_info);
            }
            println!("\n提示: 直接输入 '/provider' 即可使用 ↑/↓ 上下键菜单交互式选择切换。\n");
        }
        "key" => {
            if args.len() < 2 {
                eprintln!("错误: 请提供 API Key。用法: /provider key <your_api_key>");
                return;
            }
            let key = args[1..].join(" ");
            shell.config.api_key = key;
            save_llm_config(db, &shell.config);
            println!("已成功保存供应商 [{}] 的 API Key！", shell.config.provider);
        }
        "url" => {
            if args.len() < 2 {
                eprintln!("错误: 请提供 Base URL。用法: /provider url <http_or_https_url>");
                return;
            }
            let url = args[1];
            shell.config.base_url = url.to_string();
            save_llm_config(db, &shell.config);
            println!("已成功保存供应商 [{}] 的 Base URL 为: {}", shell.config.provider, shell.config.base_url);
        }
        target_id => {
            switch_provider(target_id, db, shell);
        }
    }
}

async fn handle_model_command(args: &[&str], db: &DbState, shell: &mut SessionState) {
    if args.is_empty() || args[0] == "list" {
        println!("正在拉取 [{}] 供应商的可用模型列表，请稍候...", shell.config.provider);
        match api::fetch_models(shell.config.base_url.clone(), shell.config.api_key.clone()).await {
            Ok(models) if !models.is_empty() => {
                let mut options = Vec::new();
                let mut default_idx = 0;
                for (idx, m) in models.iter().enumerate() {
                    let is_current = *m == shell.config.model;
                    if is_current {
                        default_idx = idx;
                    }
                    let mark = if is_current { " [当前激活]" } else { "" };
                    options.push(format!("{}{}", m, mark));
                }

                let ans = inquire::Select::new("请使用 ↑/↓ 方向键选择模型 (按 Enter 确认):", options)
                    .with_starting_cursor(default_idx)
                    .prompt();

                match ans {
                    Ok(choice) => {
                        let selected_model = choice.replace(" [当前激活]", "").trim().to_string();
                        shell.config.model = selected_model;
                        save_llm_config(db, &shell.config);
                        println!("\n✅ 已成功切换当前模型为: {}", shell.config.model);
                    }
                    Err(_) => {
                        println!("已取消选择。");
                    }
                }
            }
            Ok(_) => {
                eprintln!("未获取到可用模型列表。使用 '/model <模型名称>' 手动指定模型。");
            }
            Err(e) => {
                eprintln!("获取模型列表失败: {}", e);
                if shell.config.api_key.is_empty() && shell.config.provider != "ollama" {
                    println!("  💡 提示: 当前 API Key 为空，无法在线拉取模型列表。请运行 '/provider key <API_KEY>' 设置密钥。");
                }
                println!("  也可以使用 '/model <模型名称>' 直接指定模型名称。");
            }
        }
    } else {
        let name = args.join(" ");
        shell.config.model = name;
        save_llm_config(db, &shell.config);
        println!("✅ 已成功切换当前模型为: {}", shell.config.model);
    }
}

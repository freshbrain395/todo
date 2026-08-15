import type { Todo, User, LlmConfig, AiActionResult, LlmProvider, PromptItem, SkillItem, ChatSession } from '../types'

// 兼容性的 Storage 访问器（适配 Node/Vitest、Browser 以及 Tauri 环境）
const inMemoryStorage = new Map<string, string>()

function getStorageItem(key: string): string | null {
  try {
    if (typeof window !== 'undefined' && window.localStorage && typeof window.localStorage.getItem === 'function') {
      return window.localStorage.getItem(key)
    }
    if (typeof localStorage !== 'undefined' && typeof localStorage.getItem === 'function') {
      return localStorage.getItem(key)
    }
  } catch {}
  return inMemoryStorage.get(key) || null
}

function setStorageItem(key: string, value: string): void {
  try {
    if (typeof window !== 'undefined' && window.localStorage && typeof window.localStorage.setItem === 'function') {
      window.localStorage.setItem(key, value)
      return
    }
    if (typeof localStorage !== 'undefined' && typeof localStorage.setItem === 'function') {
      localStorage.setItem(key, value)
      return
    }
  } catch {}
  inMemoryStorage.set(key, value)
}

/**
 * 封装前端与后端（Python FastAPI RPC / Web Fallback）交互的所有 API 接口
 */
export async function invokeApi<T>(cmd: string, args: Record<string, any> = {}): Promise<T> {
  // 1. 处于具备网络 origin 的浏览器环境时，尝试直接请求 Python FastAPI 后端 (/api/invoke)
  if (
    typeof window !== 'undefined' &&
    window.location &&
    typeof window.location.origin === 'string' &&
    window.location.origin.startsWith('http')
  ) {
    try {
      const response = await fetch('/api/invoke', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ cmd, args }),
      })
      if (response.ok) {
        return (await response.json()) as T
      } else if (response.status === 400 || response.status === 500) {
        const errData = await response.json().catch(() => null)
        const errMsg = errData?.detail || `API 请求错误: HTTP ${response.status}`
        throw new Error(errMsg)
      }
    } catch (e: any) {
      if (
        e.message &&
        !e.message.includes('Failed to fetch') &&
        !e.message.includes('NetworkError') &&
        !e.message.includes('Failed to parse URL')
      ) {
        throw e
      }
    }
  }

  // 2. 离线或纯前端测试环境降级使用 Web Fallback
  return webFallbackHandler<T>(cmd, args)
}

function webFallbackHandler<T>(cmd: string, args: Record<string, any>): T {
  const userId = args.user_id || 0
  const todoKey = `web_todos_${userId}`
  const userKey = `web_users`
  const clockKey = `web_clock_config`

  switch (cmd) {
    // === 用户模块 ===
    case 'register_user': {
      const users: User[] = JSON.parse(getStorageItem(userKey) || '[]')
      if (users.some(u => u.username === args.username)) {
        throw new Error('用户名已存在')
      }
      const newUser: User = {
        id: Date.now(),
        username: args.username,
        created_at: new Date().toISOString()
      }
      users.push(newUser)
      setStorageItem(userKey, JSON.stringify(users))
      return newUser as T
    }

    case 'login_user': {
      const users: User[] = JSON.parse(getStorageItem(userKey) || '[]')
      const found = users.find(u => u.username === args.username)
      if (!found) {
        throw new Error('用户不存在或密码错误')
      }
      return found as T
    }

    // === 待办事项模块 ===
    case 'get_todos': {
      if (!getStorageItem(todoKey)) {
        const defaultTodos: Todo[] = [
          {
            id: 1,
            title: '示例待办任务',
            category: '工作',
            priority: 'high',
            completed: false,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
            user_id: userId
          }
        ]
        setStorageItem(todoKey, JSON.stringify(defaultTodos))
      }
      let todos: Todo[] = JSON.parse(getStorageItem(todoKey) || '[]')
      if (args.filter === 'pending') todos = todos.filter(t => !t.completed)
      if (args.filter === 'completed') todos = todos.filter(t => t.completed)
      if (args.search) {
        const s = args.search.toLowerCase()
        todos = todos.filter(t => t.title.toLowerCase().includes(s))
      }
      return todos as T
    }

    case 'add_todo': {
      const todos: Todo[] = JSON.parse(getStorageItem(todoKey) || '[]')
      const newId = Date.now()
      todos.push({
        id: newId,
        title: args.title,
        priority: args.priority || 'medium',
        category: args.category || '工作',
        completed: false,
        remind_at: args.remind_at || null,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        user_id: userId
      })
      setStorageItem(todoKey, JSON.stringify(todos))
      return newId as T
    }

    case 'update_todo_status': {
      const todos: Todo[] = JSON.parse(getStorageItem(todoKey) || '[]')
      const idx = todos.findIndex(t => t.id === args.id)
      if (idx >= 0) {
        todos[idx].completed = args.completed
        todos[idx].updated_at = new Date().toISOString()
        setStorageItem(todoKey, JSON.stringify(todos))
        return true as T
      }
      return false as T
    }

    case 'update_todo': {
      const todos: Todo[] = JSON.parse(getStorageItem(todoKey) || '[]')
      const idx = todos.findIndex(t => t.id === args.id)
      if (idx >= 0) {
        todos[idx].title = args.title
        todos[idx].priority = args.priority
        todos[idx].category = args.category
        todos[idx].remind_at = args.remind_at
        todos[idx].updated_at = new Date().toISOString()
        setStorageItem(todoKey, JSON.stringify(todos))
        return true as T
      }
      return false as T
    }

    case 'delete_todo': {
      let todos: Todo[] = JSON.parse(getStorageItem(todoKey) || '[]')
      const initialLen = todos.length
      todos = todos.filter(t => t.id !== args.id)
      setStorageItem(todoKey, JSON.stringify(todos))
      return (todos.length < initialLen) as T
    }

    // === AI 模块 ===
    case 'fetch_models': {
      return ['deepseek-r1:8b', 'llama3:latest', 'qwen2.5:7b'] as T
    }

    case 'execute_ai_command': {
      const input = (args.input || '') as string
      const result: AiActionResult = {
        action: 'chat',
        message: `[Mock AI] 已接收到命令: "${input}"`,
        should_refresh: false,
        data: null
      }

      if (input.includes('新建') || input.includes('添加') || input.includes('创建')) {
        const title = input.replace(/(帮我|请|新建|添加|创建|任务|待办)/g, '').trim() || '新任务'
        result.action = 'add_todo'
        result.message = `已成功添加任务："${title}"`
        result.should_refresh = true
      }

      return result as T
    }

    // === 时钟配置模块 ===
    case 'get_clock_config': {
      const config = getStorageItem(clockKey)
      return (config || null) as T
    }

    case 'save_clock_config': {
      setStorageItem(clockKey, args.config_json || '{}')
      return true as T
    }

    // === AI 配置模块（Web 降级用 localStorage）===
    case 'get_ai_providers': {
      const raw = getStorageItem('ai_custom_providers')
      return (raw ? JSON.parse(raw) : []) as T
    }

    case 'save_ai_providers': {
      setStorageItem('ai_custom_providers', args.providers_json || '[]')
      return true as T
    }

    case 'get_ai_prompts': {
      const raw = getStorageItem('ai_prompt_library')
      return (raw ? JSON.parse(raw) : []) as T
    }

    case 'save_ai_prompts': {
      setStorageItem('ai_prompt_library', args.prompts_json || '[]')
      return true as T
    }

    case 'get_ai_skills': {
      const raw = getStorageItem('agent_skills_config')
      return (raw ? JSON.parse(raw) : []) as T
    }

    case 'save_ai_skills': {
      setStorageItem('agent_skills_config', args.skills_json || '[]')
      return true as T
    }

    case 'get_ai_sessions': {
      const raw = getStorageItem('ai_chat_sessions')
      return (raw ? JSON.parse(raw) : []) as T
    }

    case 'save_ai_sessions': {
      setStorageItem('ai_chat_sessions', args.sessions_json || '[]')
      return true as T
    }

    case 'get_tool_config': {
      const raw = getStorageItem('agent_enabled_tools')
      return (raw ? JSON.parse(raw) : {}) as T
    }

    case 'save_tool_config': {
      setStorageItem('agent_enabled_tools', args.config_json || '{}')
      return true as T
    }

    case 'get_llm_config': {
      const raw = getStorageItem('llm_config_v2')
      return (raw || null) as T
    }

    case 'save_llm_config': {
      setStorageItem('llm_config_v2', args.config_json || '{}')
      return true as T
    }

    case 'get_app_config': {
      const raw = getStorageItem(`app_config_${args.key || ''}`)
      return (raw || null) as T
    }

    case 'save_app_config': {
      setStorageItem(`app_config_${args.key || ''}`, args.value || '')
      return true as T
    }

    case 'get_local_users': {
      const raw = getStorageItem('app_users_v2')
      return (raw || '{}') as T
    }

    case 'save_local_users': {
      setStorageItem('app_users_v2', args.accounts_json || '{}')
      return true as T
    }

    default:
      throw new Error(`未知的 API 指令: ${cmd}`)
  }
}

// 导出所有 11 个独立 API 函数名
export const api = {
  registerUser: (username: string, password: String) => invokeApi<User>('register_user', { username, password }),
  loginUser: (username: string, password: String) => invokeApi<User>('login_user', { username, password }),
  getTodos: (filter = 'all', search = '', userId?: number) => invokeApi<Todo[]>('get_todos', { filter, search, user_id: userId }),
  addTodo: (title: string, priority = 'medium', category = '工作', remindAt?: string | null, userId?: number) =>
    invokeApi<number>('add_todo', { title, priority, category, remind_at: remindAt, user_id: userId }),
  updateTodoStatus: (id: number, completed: boolean, userId?: number) => invokeApi<boolean>('update_todo_status', { id, completed, user_id: userId }),
  updateTodo: (id: number, title: string, priority: string, category: string, remindAt?: string | null, userId?: number) =>
    invokeApi<boolean>('update_todo', { id, title, priority, category, remind_at: remindAt, user_id: userId }),
  deleteTodo: (id: number, userId?: number) => invokeApi<boolean>('delete_todo', { id, user_id: userId }),
  fetchModels: (baseUrl: string, apiKey: string) => invokeApi<string[]>('fetch_models', { base_url: baseUrl, api_key: apiKey }),
  executeAiCommand: (input: string, config: LlmConfig, userId?: number, history?: { role: string, content: string }[] | null, systemPrompt?: string | null) =>
    invokeApi<AiActionResult>('execute_ai_command', { input, config, user_id: userId, history: history || null, system_prompt: systemPrompt || null }),
  getClockConfig: () => invokeApi<string | null>('get_clock_config', {}),
  saveClockConfig: (configJson: string) => invokeApi<boolean>('save_clock_config', { config_json: configJson }),
  getAiProviders: () => invokeApi<LlmProvider[]>('get_ai_providers', {}),
  saveAiProviders: (providers: LlmProvider[]) => invokeApi<boolean>('save_ai_providers', { providers_json: JSON.stringify(providers) }),
  getAiPrompts: () => invokeApi<PromptItem[]>('get_ai_prompts', {}),
  saveAiPrompts: (prompts: PromptItem[]) => invokeApi<boolean>('save_ai_prompts', { prompts_json: JSON.stringify(prompts) }),
  getAiSkills: () => invokeApi<SkillItem[]>('get_ai_skills', {}),
  saveAiSkills: (skills: SkillItem[]) => invokeApi<boolean>('save_ai_skills', { skills_json: JSON.stringify(skills) }),
  getAiSessions: () => invokeApi<ChatSession[]>('get_ai_sessions', {}),
  saveAiSessions: (sessions: ChatSession[]) => invokeApi<boolean>('save_ai_sessions', { sessions_json: JSON.stringify(sessions) }),
  getToolConfig: () => invokeApi<Record<string, boolean>>('get_tool_config', {}),
  saveToolConfig: (map: Record<string, boolean>) => invokeApi<boolean>('save_tool_config', { config_json: JSON.stringify(map) }),
  getLlmConfig: () => invokeApi<string | null>('get_llm_config', {}),
  saveLlmConfig: (config: LlmConfig) => invokeApi<boolean>('save_llm_config', { config_json: JSON.stringify(config) }),
  getAppConfig: (key: string) => invokeApi<string | null>('get_app_config', { key }),
  saveAppConfig: (key: string, value: string) => invokeApi<boolean>('save_app_config', { key, value }),
  getLocalUsers: () => invokeApi<string>('get_local_users', {}),
  saveLocalUsers: (accountsJson: string) => invokeApi<boolean>('save_local_users', { accounts_json: accountsJson }),
}

import { api } from './apiClient'
import type { LlmConfig, LlmProvider, PromptItem, SkillItem, ChatSession } from '../types'
import { defaultPromptsLibrary, defaultSkillsLibrary } from './aiDefaults'

export const DEFAULT_PROVIDERS: LlmProvider[] = [
  { id: 'ollama', name: 'Native Ollama (本地大模型服务)', base_url: 'http://localhost:11434', api_key: '', model: 'llama3:latest', is_custom: false },
  { id: 'siliconflow', name: 'SiliconFlow (硅基流动云端 API)', base_url: 'https://api.siliconflow.cn/v1', api_key: '', model: 'Qwen/Qwen2.5-7B-Instruct', is_custom: false }
]

const ADMIN_USER = {
  id: 'user_admin',
  username: 'admin',
  password: '123456',
  avatarColor: '#3B82F6',
  lastLoginTime: new Date().toISOString(),
  isAdmin: true
}

const DEFAULT_USER_CONFIG = {
  soundType: 'chime',
  soundVolume: 0.8,
  theme: 'light',
  llmConfig: {
    provider: 'siliconflow',
    base_url: 'https://api.siliconflow.cn/v1',
    api_key: '',
    model: 'Qwen/Qwen2.5-7B-Instruct',
    enable_thinking: false
  },
  categories: ['工作', '个人', '学习', '健康', '财务']
}

let initialized = false

let providersCache: LlmProvider[] = []
let promptsCache: PromptItem[] = []
let skillsCache: SkillItem[] = []
let sessionsCache: ChatSession[] = []
let toolConfigCache: Record<string, boolean> = {}
let llmConfigCache: LlmConfig | null = null
let themeCache: string | null = null
let activePromptIdCache: string = 'p1'
let localUsersCache: Record<string, { user: any, config: any }> = {}

function clone<T>(v: T): T {
  return JSON.parse(JSON.stringify(v))
}

function persist(p: Promise<any>): void {
  p.catch(() => {})
}

function ensureAdmin(): void {
  if (!localUsersCache[ADMIN_USER.id]) {
    localUsersCache[ADMIN_USER.id] = {
      user: clone(ADMIN_USER),
      config: clone(DEFAULT_USER_CONFIG)
    }
    persist(api.saveLocalUsers(JSON.stringify(localUsersCache)))
  }
}

export async function initBackendStorage(): Promise<void> {
  if (initialized) return
  initialized = true

  try {
    const stored = await api.getAiProviders()
    providersCache = stored && stored.length ? stored : clone(DEFAULT_PROVIDERS)
  } catch { providersCache = clone(DEFAULT_PROVIDERS) }

  try {
    const stored = await api.getAiPrompts()
    promptsCache = stored && stored.length ? stored : clone(defaultPromptsLibrary)
  } catch { promptsCache = clone(defaultPromptsLibrary) }

  try {
    const stored = await api.getAiSkills()
    skillsCache = stored && stored.length ? stored : clone(defaultSkillsLibrary)
  } catch { skillsCache = clone(defaultSkillsLibrary) }

  try {
    sessionsCache = await api.getAiSessions()
    if (!Array.isArray(sessionsCache)) sessionsCache = []
  } catch { sessionsCache = [] }

  try {
    toolConfigCache = await api.getToolConfig()
    if (!toolConfigCache || typeof toolConfigCache !== 'object') toolConfigCache = {}
  } catch { toolConfigCache = {} }

  try {
    const raw = await api.getLlmConfig()
    llmConfigCache = raw ? JSON.parse(raw) : null
  } catch { llmConfigCache = null }

  try {
    themeCache = await api.getAppConfig('todo_theme')
  } catch { themeCache = null }

  try {
    activePromptIdCache = (await api.getAppConfig('ai_active_prompt_id')) || 'p1'
  } catch { activePromptIdCache = 'p1' }

  try {
    const raw = await api.getLocalUsers()
    localUsersCache = JSON.parse(raw || '{}')
  } catch { localUsersCache = {} }
  ensureAdmin()
}

// ============ Providers ============
export function getProviders(fallback?: LlmProvider[]): LlmProvider[] {
  return providersCache.length ? providersCache : (fallback && fallback.length ? clone(fallback) : clone(DEFAULT_PROVIDERS))
}
export function saveProviders(list: LlmProvider[]): void {
  providersCache = list
  persist(api.saveAiProviders(list))
}

// ============ Prompts ============
export function getPrompts(fallback?: PromptItem[]): PromptItem[] {
  return promptsCache.length ? promptsCache : (fallback && fallback.length ? clone(fallback) : clone(defaultPromptsLibrary))
}
export function savePrompts(list: PromptItem[]): void {
  promptsCache = list
  persist(api.saveAiPrompts(list))
}
export function getActivePromptId(): string {
  return activePromptIdCache || 'p1'
}
export function setActivePromptId(id: string): void {
  activePromptIdCache = id
  persist(api.saveAppConfig('ai_active_prompt_id', id))
}

// ============ Skills ============
export function getSkills(fallback?: SkillItem[]): SkillItem[] {
  return skillsCache.length ? skillsCache : (fallback && fallback.length ? clone(fallback) : clone(defaultSkillsLibrary))
}
export function saveSkills(list: SkillItem[]): void {
  skillsCache = list
  persist(api.saveAiSkills(list))
}

// ============ Sessions ============
export function getSessions(): ChatSession[] {
  return sessionsCache || []
}
export function saveSessions(list: ChatSession[]): void {
  sessionsCache = list
  persist(api.saveAiSessions(list))
}

// ============ Tools ============
export function getToolConfig(): Record<string, boolean> {
  return toolConfigCache || {}
}
export function saveToolConfig(map: Record<string, boolean>): void {
  toolConfigCache = map
  persist(api.saveToolConfig(map))
}

// ============ LLM Config ============
export function getLlmConfig(): LlmConfig | null {
  return llmConfigCache
}
export function saveLlmConfig(config: LlmConfig): void {
  llmConfigCache = config
  persist(api.saveLlmConfig(config))
}

// ============ Theme ============
export function getTheme(): string | null {
  return themeCache
}
export function saveTheme(theme: string): void {
  themeCache = theme
  persist(api.saveAppConfig('todo_theme', theme))
}

// ============ Local Users ============
export function getLocalUsers(): Record<string, { user: any, config: any }> {
  ensureAdmin()
  return localUsersCache
}
export function saveLocalUsers(map: Record<string, { user: any, config: any }>): void {
  localUsersCache = map
  persist(api.saveLocalUsers(JSON.stringify(map)))
}

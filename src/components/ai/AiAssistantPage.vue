


<template>
  <div class="ai-page-container">
    <!-- Left Navigation Sidebar -->
    <aside class="ai-left-nav">
      <div class="nav-header">
        <div class="header-top-row">
          <div class="ai-avatar-badge">
            <Bot :size="20" class="ai-avatar-icon" />
          </div>
          <div class="nav-title-group">
            <h3 class="nav-app-title">AI Agent 智能体</h3>
            <span class="status-online">● 在线服务中</span>
          </div>
        </div>
        <button class="btn-new-chat" @click="createNewSession">
          <Plus :size="14" /> 新建对话
        </button>
      </div>

      <!-- Session List -->
      <div class="nav-sessions">
        <div class="sessions-header">历史对话记录</div>
        <div
          v-for="s in sessions"
          :key="s.id"
          class="session-item"
          :class="{ active: currentSessionId === s.id }"
          @click="selectSession(s.id)"
        >
          <MessageSquare :size="14" />
          <input
            v-if="editingSessionId === s.id"
            v-model="editingSessionTitle"
            class="session-rename-input"
            @blur="saveRenameSession(s.id)"
            @keyup.enter="saveRenameSession(s.id)"
            @click.stop
          />
          <span v-else class="session-title" @dblclick="startRenameSession(s)">{{ s.title }}</span>
          <button class="session-delete-btn" @click.stop="deleteSession(s.id, $event)" title="删除对话">
            <Trash2 :size="12" />
          </button>
        </div>
      </div>

      <!-- Mode Navigation Footer -->
      <div class="nav-footer">
        <NavbarClock />
        <div class="nav-modes">
          <button
            class="nav-item"
            :class="{ active: currentMode === 'chat' }"
            @click="currentMode = 'chat'"
          >
            <MessageSquare :size="15" /> <span>智能对话</span>
          </button>
          <button
            class="nav-item"
            :class="{ active: currentMode === 'prompts' }"
            @click="currentMode = 'prompts'"
          >
            <Sparkles :size="15" /> <span>Prompt 预设</span>
          </button>
          <button
            class="nav-item"
            :class="{ active: currentMode === 'agent' }"
            @click="currentMode = 'agent'"
          >
            <Wrench :size="15" /> <span>Agent 工具 ({{ enabledToolsCount }})</span>
          </button>
          <button
            class="nav-item"
            :class="{ active: currentMode === 'skills' }"
            @click="currentMode = 'skills'"
          >
            <BookOpen :size="15" /> <span>Skill 技能 ({{ enabledSkillsCount }})</span>
          </button>
          <button
            class="nav-item"
            :class="{ active: currentMode === 'settings' }"
            @click="currentMode = 'settings'"
          >
            <Settings :size="15" /> <span>模型设置</span>
          </button>
        </div>
      </div>
    </aside>

    <!-- Main View Workspace -->
    <main class="ai-main-view">
      <!-- Mode 1: Chat -->
      <div v-if="currentMode === 'chat'" class="chat-workspace">
        <div class="chat-messages-area" ref="chatContainerRef">
          <div v-if="!activeSession || activeSession.messages.length === 0" class="chat-empty-welcome">
            <div class="welcome-badge"><Bot :size="28" /></div>
            <h4>你好！我是您的 AI 智能体助手</h4>
            <p>我可以帮您管理待办事项、安排日程、解答问题以及分析任务执行规划。</p>
            <div class="preset-prompts-grid">
              <button
                v-for="p in defaultPrompts"
                :key="p"
                class="preset-prompt-card"
                @click="sendPresetPrompt(p)"
              >
                ✨ {{ p }}
              </button>
            </div>
          </div>

          <div v-else class="messages-list">
            <div
              v-for="msg in activeSession.messages"
              :key="msg.id"
              class="chat-bubble-row"
              :class="msg.sender"
            >
              <div class="bubble-avatar">
                <User v-if="msg.sender === 'user'" :size="16" />
                <Bot v-else-if="msg.sender === 'ai'" :size="16" />
                <Zap v-else :size="16" />
              </div>
              <div class="bubble-content">
                <div class="bubble-header">
                  <span class="sender-name">{{ msg.sender === 'user' ? '您' : msg.sender === 'ai' ? 'AI Agent' : '系统提示' }}</span>
                  <span class="timestamp">{{ msg.timestamp }}</span>
                </div>
                <div class="bubble-text">{{ msg.text }}</div>
              </div>
            </div>

            <div v-if="isProcessing" class="chat-bubble-row ai loading">
              <div class="bubble-avatar"><Bot :size="16" /></div>
              <div class="bubble-content">
                <div class="bubble-text"><span class="loading-dots">AI 正在思考处理中...</span></div>
              </div>
            </div>
          </div>
        </div>

        <div class="chat-input-toolbar">
          <div class="input-actions-left">
            <button class="btn-tool-action" @click="clearMessages" title="清空对话">
              <Trash2 :size="14" /> 清空
            </button>
          </div>
          <div class="input-box-wrapper">
            <textarea
              v-model="inputQuery"
              class="chat-textarea"
              placeholder="发送消息给 AI Agent（Enter 发送，Shift+Enter 换行）..."
              @keydown.enter.exact.prevent="handleSend"
            ></textarea>
            <button
              class="btn-send-msg"
              :disabled="isProcessing || !inputQuery.trim()"
              @click="handleSend"
            >
              <Send :size="15" /> 发送
            </button>
          </div>
        </div>
      </div>

      <!-- Mode 2: Prompts -->
      <div v-else-if="currentMode === 'prompts'" class="mode-workspace-padded">
        <PromptsSettingsTab
          :prompt-library="promptLibrary"
          v-model:active-prompt-id="activePromptId"
          :editing-prompt-id="editingPromptId"
          :edit-form="editForm"
          @add-new-prompt="addNewPrompt"
          @start-edit-prompt="startEditPrompt"
          @save-edit-prompt="saveEditPrompt"
          @cancel-edit-prompt="cancelEditPrompt"
          @delete-prompt="deletePrompt"
        />
      </div>

      <!-- Mode 3: Agent Tools -->
      <div v-else-if="currentMode === 'agent'" class="mode-workspace-padded">
        <ToolsSettingsTab
          :agent-tools="agentTools"
          @enable-all="enableAllTools"
          @disable-all="disableAllTools"
          @reset-default="resetToolsDefault"
          @save-tools="saveToolsStorage"
        />
      </div>

      <!-- Mode 4: Skills -->
      <div v-else-if="currentMode === 'skills'" class="mode-workspace-padded">
        <SkillsSettingsTab
          :skills-library="skillsLibrary"
          :editing-skill-id="editingSkillId"
          :skill-form="skillForm"
          @enable-all="enableAllSkills"
          @disable-all="disableAllSkills"
          @add-new-skill="addNewSkill"
          @start-edit-skill="startEditSkill"
          @save-edit-skill="saveEditSkill"
          @cancel-edit-skill="cancelEditSkill"
          @delete-skill="deleteSkill"
          @save-skills="saveSkillsStorage"
        />
      </div>

      <!-- Mode 5: Settings -->
      <div v-else-if="currentMode === 'settings'" class="mode-workspace-padded">
        <LlmSettingsTab
          :saved-providers="savedProviders"
          :local-config="localConfig"
          :fetched-models="fetchedModels"
          :is-fetching-models="isFetchingModels"
          :fetch-model-error="fetchModelError"
          @update-provider="onProviderEdited"
          @select-provider="selectProvider"
          @delete-provider="deleteProvider"
          @fetch-models="fetchModels"
          @add-custom-provider="addCustomProvider"
        />
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick } from 'vue'
import {
  MessageSquare, Sparkles, Wrench, BookOpen, Settings, Plus,
  Trash2, Send, User, Bot, Zap, Search, PlusCircle, CheckCircle2, Timer, Bell
} from 'lucide-vue-next'
import NavbarClock from '../widgets/NavbarClock.vue'
import type { ChatMessage, LlmConfig, AiActionResult } from '../../types'
import { showConfirm } from '../../utils/confirmState'
import LlmSettingsTab from './settings/LlmSettingsTab.vue'
import PromptsSettingsTab from './settings/PromptsSettingsTab.vue'
import ToolsSettingsTab from './settings/ToolsSettingsTab.vue'
import SkillsSettingsTab from './settings/SkillsSettingsTab.vue'

const props = defineProps<{
  config: LlmConfig
  isProcessing: boolean
}>()

const emit = defineEmits<{
  (e: 'send', text: string): void
  (e: 'update:config', config: LlmConfig): void
}>()

type AiMode = 'chat' | 'prompts' | 'agent' | 'skills' | 'settings'
const currentMode = ref<AiMode>('chat')

type SettingsSubTab = 'modes' | 'llm' | 'prompts' | 'tools' | 'skills'
const settingsSubTab = ref<SettingsSubTab>('llm')

const inputQuery = ref('')
const chatContainerRef = ref<HTMLElement | null>(null)

const localConfig = ref<LlmConfig>({ ...props.config })
watch(() => props.config, (newVal) => {
  localConfig.value = { ...newVal }
}, { deep: true })

// 监听 localConfig 修改，实现自动保存并回传父组件
watch(localConfig, (newVal) => {
  if (newVal.api_key) {
    localStorage.setItem('siliconflow_api_key', newVal.api_key)
  }
  emit('update:config', { ...newVal })
}, { deep: true })

interface CustomLlmProvider {
  id: string
  name: string
  base_url: string
  api_key: string
  model: string
  is_custom: boolean
}

const defaultProviders: CustomLlmProvider[] = [
  { id: 'ollama', name: 'Native Ollama (本地大模型服务)', base_url: 'http://localhost:11434', api_key: '', model: 'llama3:latest', is_custom: false },
  { id: 'siliconflow', name: 'SiliconFlow (硅基流动云端 API)', base_url: 'https://api.siliconflow.cn/v1', api_key: '', model: 'Qwen/Qwen2.5-7B-Instruct', is_custom: false }
]

const savedProviders = ref<CustomLlmProvider[]>(
  JSON.parse(localStorage.getItem('ai_custom_providers') || 'null') || defaultProviders
)
savedProviders.value.sort((a,b) => (a.id === 'ollama' ? -1 : (b.id === 'ollama' ? 1 : 0)))

const fetchedModels = ref<Record<string, {id: string, name: string}[]>>({})
const isFetchingModels = ref<Record<string, boolean>>({})
const fetchModelError = ref<Record<string, string>>({})
const isManualModel = ref<Record<string, boolean>>({})

async function fetchModels(p: CustomLlmProvider) {
  isFetchingModels.value[p.id] = true
  fetchModelError.value[p.id] = ''
  fetchedModels.value[p.id] = []

  let baseUrl = p.base_url.trim()
  if (baseUrl.endsWith('/')) baseUrl = baseUrl.slice(0, -1)

  try {
    let modelNames: string[] = []

    // 优先调用 Tauri 后端避免跨域 (CORS) 与网络协议问题
    if (typeof window !== 'undefined' && '__TAURI_INTERNALS__' in window) {
      const { invoke } = await import('@tauri-apps/api/core')
      modelNames = await invoke<string[]>('fetch_models', {
        baseUrl: p.base_url,
        apiKey: p.api_key || ''
      })
    } else {
      // 浏览器 Web 模式下降级使用标准 fetch
      let apiUrl = baseUrl + '/models'
      if (baseUrl.includes('11434')) {
        if (!baseUrl.endsWith('/api') && !baseUrl.endsWith('/v1')) {
          apiUrl = baseUrl + '/api/tags'
        } else if (baseUrl.endsWith('/api')) {
          apiUrl = baseUrl + '/tags'
        }
      }
      const headers: Record<string, string> = { 'Content-Type': 'application/json' }
      if (p.api_key) headers['Authorization'] = `Bearer ${p.api_key}`
      const res = await fetch(apiUrl, { headers })
      if (!res.ok) throw new Error(`HTTP Error ${res.status}`)
      const data = await res.json()
      if (data.data && Array.isArray(data.data)) {
        modelNames = data.data.map((m: any) => m.id)
      } else if (data.models && Array.isArray(data.models)) {
        modelNames = data.models.map((m: any) => m.name)
      }
    }

    if (modelNames && modelNames.length > 0) {
      fetchedModels.value[p.id] = modelNames.map(name => ({ id: name, name }))
      isManualModel.value[p.id] = false
    } else {
      throw new Error('没有获取到可用模型')
    }
  } catch (err: any) {
    console.error(err)
    fetchModelError.value[p.id] = '获取失败: ' + (err.message || String(err))
    isManualModel.value[p.id] = true
  } finally {
    isFetchingModels.value[p.id] = false
  }
}

function saveProvidersStorage() {
  localStorage.setItem('ai_custom_providers', JSON.stringify(savedProviders.value))
}

function onProviderEdited(p: CustomLlmProvider) {
  if (localConfig.value.provider === p.id) {
    localConfig.value.base_url = p.base_url
    localConfig.value.api_key = p.api_key
    localConfig.value.model = p.model
    emit('update:config', { ...localConfig.value })
  }
  saveProvidersStorage()
  if (p.base_url) {
    fetchModels(p)
  }
}

watch(() => settingsSubTab.value, (newVal) => {
  if (newVal === 'llm') {
    savedProviders.value.forEach(p => {
      if (p.base_url && !(fetchedModels.value[p.id] && fetchedModels.value[p.id].length > 0)) {
        fetchModels(p)
      }
    })
  }
}, { immediate: true })


function selectProvider(p: CustomLlmProvider) {
  localConfig.value.provider = p.id
  localConfig.value.base_url = p.base_url
  localConfig.value.api_key = p.api_key
  localConfig.value.model = p.model
  saveProvidersStorage()
  emit('update:config', { ...localConfig.value })
}

function addCustomProvider() {
  const name = prompt('请输入新卡片的名称（如: OpenAI）:')
  if (!name) return
  const id = 'custom_' + Date.now()
  const newP = {
    id,
    name,
    base_url: '',
    api_key: '',
    model: '',
    is_custom: true
  }
  savedProviders.value.unshift(newP)
  selectProvider(newP)
}

function deleteProvider(id: string) {
  if (id === 'ollama' || id === 'siliconflow') return
  if (!confirm('确定要删除此服务商卡片吗？')) return
  savedProviders.value = savedProviders.value.filter(p => p.id !== id)
  if (localConfig.value.provider === id && savedProviders.value.length > 0) {
    selectProvider(savedProviders.value[0])
  } else {
    saveProvidersStorage()
  }
}


export interface SkillItem {
  id: string
  title: string
  category: string
  description: string
  systemPrompt: string
  enabled: boolean
}

const defaultSkillsLibrary: SkillItem[] = [
  {
    id: 'skill-gtd',
    title: 'GTD 四象限任务规划',
    category: '时间管理',
    description: '根据紧急与重要维度自动解析待办清单，智能规划当日高效率执行顺序。',
    systemPrompt: '请将用户提交的任务按紧急/重要四象限进行分类，并给出第一优先级的 3 个具体执行建议。',
    enabled: true
  },
  {
    id: 'skill-pomodoro',
    title: '番茄工作法轮巡规划',
    category: '专注执行',
    description: '自动将大块工作时间拆解为 25 分钟专注 + 5 分钟休息的番茄钟节奏，并启动系统倒计时。',
    systemPrompt: '将大任务拆分为若干 25 分钟的番茄专注时段，并自动触发倒计时工具。',
    enabled: true
  },
  {
    id: 'skill-weekly-report',
    title: '周报与工作总结整理',
    category: '总结输出',
    description: '按完成状态、任务分类整理已完成列表，自动提炼生成结构化 Markdown 周报。',
    systemPrompt: '分析已完成待办，提炼本周核心产出、未完成风险及下周计划。',
    enabled: true
  },
  {
    id: 'skill-smart-alarm',
    title: '自然语言时间解构与提醒',
    category: '日程提醒',
    description: '精准识别模糊时间表述（如“明早八点半”、“今晚8点”）并自动联动应用闹钟提醒。',
    systemPrompt: '提取时间点与事件主体，自动调用 set_alarm 工具创建响铃提醒。',
    enabled: true
  },
  {
    id: 'skill-breakdown',
    title: '目标分解与微习惯提炼',
    category: '任务拆解',
    description: '把抽象的大目标（如“准备考试”）一键拆解为 3-5 项单日可完成的细化待办。',
    systemPrompt: '拆解复杂目标为具体、可衡量、有清晰动作的子待办事项。',
    enabled: true
  }
]

const skillsLibrary = ref<SkillItem[]>(
  JSON.parse(localStorage.getItem('agent_skills_config') || 'null') || defaultSkillsLibrary
)

function saveSkillsStorage() {
  localStorage.setItem('agent_skills_config', JSON.stringify(skillsLibrary.value))
}

const enabledSkillsCount = computed(() => {
  return skillsLibrary.value.filter(s => s.enabled).length
})

function enableAllSkills() {
  skillsLibrary.value.forEach(s => (s.enabled = true))
  saveSkillsStorage()
}

function disableAllSkills() {
  skillsLibrary.value.forEach(s => (s.enabled = false))
  saveSkillsStorage()
}

const editingSkillId = ref<string | null>(null)
const skillForm = ref({
  title: '',
  category: '',
  description: '',
  systemPrompt: ''
})

function startEditSkill(item: SkillItem) {
  editingSkillId.value = item.id
  skillForm.value = {
    title: item.title,
    category: item.category,
    description: item.description,
    systemPrompt: item.systemPrompt
  }
}

function cancelEditSkill() {
  editingSkillId.value = null
}

function saveEditSkill(id: string) {
  const target = skillsLibrary.value.find(s => s.id === id)
  if (target) {
    target.title = skillForm.value.title.trim() || '未命名 Skill'
    target.category = skillForm.value.category.trim() || '自定义'
    target.description = skillForm.value.description.trim()
    target.systemPrompt = skillForm.value.systemPrompt.trim()
    saveSkillsStorage()
  }
  editingSkillId.value = null
}

function addNewSkill() {
  const newId = 'skill_' + Date.now()
  const newItem: SkillItem = {
    id: newId,
    title: '新建自定义技能',
    category: '自定义',
    description: '描述该技能的核心作用...',
    systemPrompt: '在此定义该技能的 System Prompt 提示词...',
    enabled: true
  }
  skillsLibrary.value.unshift(newItem)
  saveSkillsStorage()
  startEditSkill(newItem)
}

async function deleteSkill(id: string) {
  const confirmed = await showConfirm({
    title: '删除技能',
    message: '确定要删除该技能配置吗？',
    confirmText: '确认删除',
    type: 'danger'
  })
  if (!confirmed) return

  skillsLibrary.value = skillsLibrary.value.filter(s => s.id !== id)
  saveSkillsStorage()
  if (editingSkillId.value === id) {
    editingSkillId.value = null
  }
}

interface ChatSession {
  id: string
  title: string
  createdAt: number
  updatedAt: number
  messages: ChatMessage[]
}

const DEFAULT_SESSIONS: ChatSession[] = [
  {
    id: 'session-default',
    title: '新对话 1',
    createdAt: Date.now(),
    updatedAt: Date.now(),
    messages: []
  }
]

const savedSessionsStr = localStorage.getItem('ai_chat_sessions')
let parsedSessions: ChatSession[] = []
if (savedSessionsStr) {
  try {
    parsedSessions = JSON.parse(savedSessionsStr)
  } catch (e) {
    console.error('Failed to parse ai_chat_sessions', e)
  }
}
if (!parsedSessions || parsedSessions.length === 0) {
  parsedSessions = DEFAULT_SESSIONS
}

const sessions = ref<ChatSession[]>(parsedSessions)
const currentSessionId = ref<string>(sessions.value[0]?.id || 'session-default')

const editingSessionId = ref<string | null>(null)
const editingSessionTitle = ref('')

function saveSessionsToStorage() {
  localStorage.setItem('ai_chat_sessions', JSON.stringify(sessions.value))
}

const activeSession = computed(() => {
  return sessions.value.find(s => s.id === currentSessionId.value) || sessions.value[0] || DEFAULT_SESSIONS[0]
})

const messages = computed({
  get() {
    return activeSession.value ? activeSession.value.messages : []
  },
  set(val: ChatMessage[]) {
    if (activeSession.value) {
      activeSession.value.messages = val
      activeSession.value.updatedAt = Date.now()
      saveSessionsToStorage()
    }
  }
})

function createNewSession() {
  const newId = 'session_' + Date.now()
  const newSession: ChatSession = {
    id: newId,
    title: `新对话 ${sessions.value.length + 1}`,
    createdAt: Date.now(),
    updatedAt: Date.now(),
    messages: []
  }
  sessions.value.unshift(newSession)
  currentSessionId.value = newId
  if (currentMode.value === 'settings') {
    currentMode.value = 'chat'
  }
  saveSessionsToStorage()
}

function selectSession(id: string) {
  currentSessionId.value = id
  if (currentMode.value === 'settings') {
    currentMode.value = 'chat'
  }
}

function startRenameSession(session: ChatSession, event?: Event) {
  if (event) event.stopPropagation()
  editingSessionId.value = session.id
  editingSessionTitle.value = session.title
}

function saveRenameSession(id: string) {
  const s = sessions.value.find(item => item.id === id)
  if (s && editingSessionTitle.value.trim()) {
    s.title = editingSessionTitle.value.trim()
    saveSessionsToStorage()
  }
  editingSessionId.value = null
}

async function deleteSession(id: string, event?: Event) {
  if (event) event.stopPropagation()
  if (sessions.value.length <= 1) {
    const confirmed = await showConfirm({
      title: '重置当前唯一对话',
      message: '这是您唯一的对话记录，是否清空重置？',
      confirmText: '确认重置',
      type: 'warning'
    })
    if (!confirmed) return
    const s = sessions.value[0]
    s.title = '新对话 1'
    s.messages = []
    saveSessionsToStorage()
    return
  }

  const confirmed = await showConfirm({
    title: '删除历史对话',
    message: '确定要删除该历史对话记录吗？',
    confirmText: '确认删除',
    type: 'danger'
  })
  if (!confirmed) return

  sessions.value = sessions.value.filter(s => s.id !== id)
  if (currentSessionId.value === id) {
    currentSessionId.value = sessions.value[0].id
  }
  saveSessionsToStorage()
}

const defaultPrompts = [
  '帮我安排明天上午 10 点团队周会',
  '提醒我今晚 8 点给客户回复邮件',
  '显示所有高优先级的待办事项',
  '你能为我做些什么？'
]

interface PromptItem {
  id: string
  category: string
  title: string
  text: string
  jsonFormat?: string
}

const defaultPromptsLibrary: PromptItem[] = [
  {
    id: 'p1',
    category: '时间管理',
    title: '高效工作日程划分',
    text: '请帮我规划今天的工作日程，把重要且紧急的任务安排在上午最清醒的时候。'
  },
  {
    id: 'p2',
    category: '任务拆解',
    title: '复杂大项目细化',
    text: '帮我把"完成项目上线"拆解为 5 个具体的、可落地的子待办事项。'
  },
  {
    id: 'p3',
    category: '周报生成',
    title: '工作总结整理',
    text: '请根据我已完成的待办事项，帮我撰写一份简明扼要的本周工作总结。'
  },
  {
    id: 'p4',
    category: '优先级评估',
    title: '待办四象限排序',
    text: '分析我现有的待办列表，并给出最推荐优先处理的前 3 项任务建议。'
  }
]

const promptLibrary = ref<PromptItem[]>(
  JSON.parse(localStorage.getItem('ai_prompt_library') || 'null') || defaultPromptsLibrary
)

const activePromptId = ref<string>('p1')


const editingPromptId = ref<string | null>(null)
const editForm = ref({
  category: '',
  title: '',
  text: '',
  jsonFormat: ''
})

function savePromptLibraryStorage() {
  localStorage.setItem('ai_prompt_library', JSON.stringify(promptLibrary.value))
}

function startEditPrompt(item: PromptItem) {
  editingPromptId.value = item.id
  editForm.value = {
    category: item.category,
    title: item.title,
    text: item.text,
    jsonFormat: item.jsonFormat || ''
  }
}

function cancelEditPrompt() {
  editingPromptId.value = null
}

function saveEditPrompt(id: string) {
  const target = promptLibrary.value.find(p => p.id === id)
  if (target) {
    target.category = editForm.value.category.trim() || '自定义'
    target.title = editForm.value.title.trim() || '未命名提示词'
    target.text = editForm.value.text.trim()
    target.jsonFormat = editForm.value.jsonFormat.trim()
    savePromptLibraryStorage()
  }
  editingPromptId.value = null
}

function addNewPrompt() {
  const newId = 'p_' + Date.now()
  const newItem: PromptItem = {
    id: newId,
    category: '自定义',
    title: '新建提示词',
    text: '在此输入您的 Prompt 指令...',
    jsonFormat: ''
  }
  promptLibrary.value.unshift(newItem)
  activePromptId.value = newId
  savePromptLibraryStorage()
  startEditPrompt(newItem)
}

async function deletePrompt(id: string) {
  const confirmed = await showConfirm({
    title: '删除提示词',
    message: '确定要删除该提示词卡片吗？',
    confirmText: '确认删除',
    type: 'danger'
  })
  if (!confirmed) return

  promptLibrary.value = promptLibrary.value.filter(p => p.id !== id)
  savePromptLibraryStorage()
  if (activePromptId.value === id && promptLibrary.value.length > 0) {
    activePromptId.value = promptLibrary.value[0].id
  }
  if (editingPromptId.value === id) {
    editingPromptId.value = null
  }
}



interface AgentToolItem {
  id: string
  label: string
  description: string
  category: 'database' | 'system'
  categoryText: string
  icon: any
  enabled: boolean
}

const defaultAgentTools: AgentToolItem[] = [
  {
    id: 'add_todo',
    label: '新建待办事项',
    description: '根据自然语言指令解析标题、分类、截止日期与优先级，自动写入 SQLite 数据库与本地存储。',
    category: 'database',
    categoryText: 'SQLite 增',
    icon: PlusCircle,
    enabled: true
  },
  {
    id: 'update_todo_status',
    label: '更新待办状态',
    description: '根据任务名称或 ID 匹配记录，智能将指定待办标记为已完成或取消完成。',
    category: 'database',
    categoryText: 'SQLite 改',
    icon: CheckCircle2,
    enabled: true
  },
  {
    id: 'delete_todo',
    label: '彻底删除待办',
    description: '根据指定的任务关键词或 ID 物理从 SQLite 数据库中完全删除待办事项记录。',
    category: 'database',
    categoryText: 'SQLite 删',
    icon: Trash2,
    enabled: true
  },
  {
    id: 'get_todos',
    label: '智能检索待办',
    description: '提供关键字搜索、按分类筛选和按完成状态多维度调取数据库待办记录列表。',
    category: 'database',
    categoryText: 'SQLite 查',
    icon: Search,
    enabled: true
  },
  {
    id: 'set_alarm',
    label: '设置提醒闹钟',
    description: '自动在系统闹钟模块添加指定时间（如 08:30）与备注标签的准时响铃提醒。',
    category: 'system',
    categoryText: '应用工具',
    icon: Bell,
    enabled: true
  },
  {
    id: 'start_countdown',
    label: '开启专注倒计时',
    description: '在倒计时模块中一键设置并启动指定分钟数（如 25 分钟番茄钟）的专注倒计时。',
    category: 'system',
    categoryText: '应用工具',
    icon: Timer,
    enabled: true
  }
]

const storedToolsConfig = localStorage.getItem('agent_enabled_tools')
let initialEnabledMap: Record<string, boolean> = {}
if (storedToolsConfig) {
  try {
    initialEnabledMap = JSON.parse(storedToolsConfig)
  } catch (e) {}
}

const agentTools = ref<AgentToolItem[]>(
  defaultAgentTools.map(t => ({
    ...t,
    enabled: initialEnabledMap[t.id] !== undefined ? initialEnabledMap[t.id] : t.enabled
  }))
)

const enabledToolsCount = computed(() => {
  return agentTools.value.filter(t => t.enabled).length
})

function saveToolsStorage() {
  const map: Record<string, boolean> = {}
  agentTools.value.forEach(t => {
    map[t.id] = t.enabled
  })
  localStorage.setItem('agent_enabled_tools', JSON.stringify(map))
}

function enableAllTools() {
  agentTools.value.forEach(t => (t.enabled = true))
  saveToolsStorage()
}

function disableAllTools() {
  agentTools.value.forEach(t => (t.enabled = false))
  saveToolsStorage()
}

function resetToolsDefault() {
  agentTools.value.forEach(t => (t.enabled = true))
  saveToolsStorage()
}


function scrollToBottom() {
  nextTick(() => {
    if (chatContainerRef.value) {
      chatContainerRef.value.scrollTop = chatContainerRef.value.scrollHeight
    }
  })
}

watch(messages, () => {
  scrollToBottom()
}, { deep: true })

function handleSend() {
  const text = inputQuery.value.trim()
  if (!text || props.isProcessing) return

  if (activeSession.value && activeSession.value.title.startsWith('新对话')) {
    activeSession.value.title = text.length > 14 ? text.slice(0, 14) + '...' : text
  }

  const newMsg: ChatMessage = {
    id: String(Date.now()),
    sender: 'user',
    text: text,
    timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  }

  if (activeSession.value) {
    activeSession.value.messages.push(newMsg)
    activeSession.value.updatedAt = Date.now()
    saveSessionsToStorage()
  }

  inputQuery.value = ''
  emit('send', text)
  scrollToBottom()
}

function sendPresetPrompt(promptText: string) {
  inputQuery.value = promptText
  handleSend()
}

function appendAiResponse(result: AiActionResult) {
  const newMsg: ChatMessage = {
    id: String(Date.now()),
    sender: 'ai',
    text: result.message,
    timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    actionResult: result
  }
  if (activeSession.value) {
    activeSession.value.messages.push(newMsg)
    activeSession.value.updatedAt = Date.now()
    saveSessionsToStorage()
  }
  scrollToBottom()
}

function appendSystemError(errorMsg: string) {
  const newMsg: ChatMessage = {
    id: String(Date.now()),
    sender: 'system',
    text: `❌ ${errorMsg}`,
    timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  }
  if (activeSession.value) {
    activeSession.value.messages.push(newMsg)
    activeSession.value.updatedAt = Date.now()
    saveSessionsToStorage()
  }
  scrollToBottom()
}

async function clearMessages() {
  const confirmed = await showConfirm({
    title: '清空当前对话历史',
    message: '确定要清空当前对话中的所有记录吗？',
    detail: '清空后当前对话上下文将被重置，无法恢复。',
    confirmText: '清空对话',
    cancelText: '取消',
    type: 'warning'
  })
  if (!confirmed) return
  if (activeSession.value) {
    activeSession.value.messages = []
    saveSessionsToStorage()
  }
}

defineExpose({
  appendAiResponse,
  appendSystemError
})
</script>

<style scoped>
.ai-page-container {
  display: flex;
  flex-direction: row;
  height: 100%;
  width: 100%;
  background-color: var(--bg-app);
  overflow: hidden;
}

/* Left Navigation Sidebar */
.ai-left-nav {
  width: 240px;
  min-width: 200px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  border-right: 1px solid var(--border-color);
  background-color: var(--bg-surface);
  padding: 16px 12px;
  box-sizing: border-box;
  gap: 16px;
  flex-shrink: 0;
}

.nav-header {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding-bottom: 14px;
  border-bottom: 1px dashed var(--border-color);
}

.header-top-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.ai-avatar-badge {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  background-color: rgba(49, 130, 206, 0.12);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--primary);
  flex-shrink: 0;
}

.ai-avatar-icon {
  color: var(--primary);
}

.nav-title-group {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.nav-app-title {
  font-size: 14px;
  font-weight: 800;
  color: var(--text-main);
  margin: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.status-online {
  font-size: 11px;
  color: #38a169;
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.btn-new-chat {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  width: 100%;
  padding: 9px 12px;
  border-radius: 8px;
  background: linear-gradient(135deg, var(--primary), #4f46e5);
  color: #ffffff;
  border: none;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
  box-shadow: 0 2px 6px rgba(79, 70, 229, 0.25);
  transition: all 0.2s ease;
}

.btn-new-chat:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 10px rgba(79, 70, 229, 0.35);
  opacity: 0.95;
}

.session-list-section {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
  gap: 8px;
}

.section-label-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 4px;
}

.section-label {
  font-size: 11px;
  font-weight: 700;
  color: var(--text-muted);
  letter-spacing: 0.5px;
  text-transform: uppercase;
}

.session-count-badge {
  font-size: 10px;
  font-weight: 700;
  padding: 2px 6px;
  border-radius: 10px;
  background-color: var(--bg-app);
  color: var(--text-muted);
  border: 1px solid var(--border-color);
}

.session-items-scroll {
  display: flex;
  flex-direction: column;
  gap: 4px;
  flex: 1;
  overflow-y: auto;
  padding-right: 2px;
}

.session-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 10px;
  border-radius: 8px;
  border: 1px solid transparent;
  background: transparent;
  color: var(--text-muted);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.15s ease;
  position: relative;
  user-select: none;
}

.session-item:hover {
  background-color: var(--bg-app);
  color: var(--text-main);
}

.session-item.active {
  background-color: var(--bg-app);
  color: var(--primary);
  border-color: var(--border-color);
  font-weight: 600;
}

.session-icon {
  flex-shrink: 0;
  opacity: 0.7;
}

.session-item.active .session-icon {
  color: var(--primary);
  opacity: 1;
}

.session-info {
  flex: 1;
  min-width: 0;
  display: flex;
  align-items: center;
}

.session-title {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  font-size: 12.5px;
}

.session-title-input {
  width: 100%;
  border: 1px solid var(--primary);
  border-radius: 4px;
  padding: 2px 4px;
  font-size: 12px;
  background: var(--bg-surface);
  color: var(--text-main);
  outline: none;
}

.session-actions {
  display: none;
  align-items: center;
  gap: 2px;
  flex-shrink: 0;
}

.session-item:hover .session-actions {
  display: flex;
}

.btn-session-action {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 22px;
  height: 22px;
  border-radius: 4px;
  border: none;
  background: transparent;
  color: var(--text-muted);
  cursor: pointer;
  transition: all 0.15s ease;
}

.btn-session-action:hover {
  background-color: var(--border-color);
  color: var(--text-main);
}

.btn-session-action.danger:hover {
  background-color: rgba(229, 62, 62, 0.15);
  color: #e53e3e;
}

.nav-footer {
  padding-top: 12px;
  border-top: 1px dashed var(--border-color);
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  border-radius: 8px;
  border: 1px solid transparent;
  background: transparent;
  color: var(--text-muted);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  text-align: left;
  width: 100%;
  box-sizing: border-box;
}

.nav-item:hover {
  background-color: var(--bg-app);
  color: var(--text-main);
}

.nav-item.active {
  background-color: var(--bg-app);
  color: var(--primary);
  border-color: var(--border-color);
  border-left: 3px solid var(--primary);
  font-weight: 700;
}

.nav-footer {
  padding-top: 12px;
  border-top: 1px dashed var(--border-color);
}

.btn-clear-history-full {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 8px 12px;
  border-radius: 6px;
  border: 1px solid var(--border-color);
  background-color: var(--bg-app);
  color: var(--text-muted);
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-clear-history-full:hover {
  color: #e53e3e;
  border-color: #e53e3e;
}

/* Right Workspace Area */
.ai-right-workspace {
  flex: 1;
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
  min-width: 0;
}

/* Top Workspace Bar & Mode Tabs */
.workspace-top-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 20px;
  background-color: var(--bg-surface);
  border-bottom: 1px solid var(--border-color);
  flex-shrink: 0;
}

.mode-tabs-group {
  display: flex;
  align-items: center;
  gap: 6px;
  background-color: var(--bg-app);
  padding: 3px;
  border-radius: 8px;
  border: 1px solid var(--border-color);
}

.tab-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  border-radius: 6px;
  border: none;
  background: transparent;
  color: var(--text-muted);
  font-size: 12.5px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.tab-btn:hover {
  color: var(--text-main);
}

.tab-btn.active {
  background-color: var(--bg-surface);
  color: var(--primary);
  font-weight: 700;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
}

.workspace-session-meta {
  display: flex;
  align-items: center;
  gap: 8px;
}

.meta-session-name {
  font-size: 12px;
  color: var(--text-muted);
  font-weight: 500;
}

/* 1. Chat Mode View */
.chat-view-wrapper {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

.chat-messages-scroll {
  flex: 1;
  padding: 24px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.chat-welcome-banner {
  max-width: 600px;
  margin: 40px auto;
  text-align: center;
  background-color: var(--bg-surface);
  border: 1px dashed var(--border-color);
  border-radius: var(--radius-lg);
  padding: 30px;
}

.banner-sparkle {
  color: var(--ai-purple);
  margin-bottom: 10px;
}

.chat-welcome-banner h3 {
  font-size: 18px;
  color: var(--primary);
  margin-bottom: 8px;
}

.chat-welcome-banner p {
  font-size: 13px;
  color: var(--text-muted);
  margin-bottom: 20px;
}

.quick-prompts-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.quick-prompt-btn {
  background-color: var(--bg-app);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 10px;
  font-size: 12px;
  color: var(--text-main);
  text-align: left;
  cursor: pointer;
  transition: all 0.2s;
}

.quick-prompt-btn:hover {
  border-color: var(--primary);
  color: var(--primary);
  transform: translateY(-1px);
}

.chat-bubble-row {
  display: flex;
  gap: 12px;
  align-items: flex-start;
  max-width: 800px;
  margin: 0 auto;
  width: 100%;
}

.chat-bubble-row.sender-user {
  flex-direction: row-reverse;
}

.bubble-avatar {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  background-color: var(--bg-surface);
  border: 1px solid var(--border-color);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--primary);
  flex-shrink: 0;
}

.bubble-body {
  max-width: 75%;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.bubble-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 11px;
  color: var(--text-muted);
}

/* 2. Prompts Mode Wrapper & Components */
.prompts-mode-wrapper {
  display: flex;
  flex-direction: column;
  height: 100%;
  width: 100%;
  padding: 18px 24px;
  box-sizing: border-box;
  gap: 14px;
  overflow: hidden;
}

.prompts-selector-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  background-color: var(--bg-surface);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  padding: 10px 14px;
  flex-shrink: 0;
}

.selector-title-group {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  font-weight: 700;
  color: var(--primary);
  white-space: nowrap;
}

.prompt-chips-scroll {
  display: flex;
  align-items: center;
  gap: 8px;
  overflow-x: auto;
  flex: 1;
  padding-bottom: 2px;
}

.prompt-chip-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background-color: var(--bg-app);
  border: 1px solid var(--border-color);
  border-radius: 16px;
  padding: 4px 12px;
  font-size: 11.5px;
  color: var(--text-main);
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.2s ease;
}

.prompt-chip-btn:hover {
  border-color: var(--primary);
  background-color: var(--bg-card-hover);
}

.prompt-chip-btn.active {
  border-color: var(--primary);
  background-color: rgba(66, 153, 225, 0.12);
  color: var(--primary);
  font-weight: 600;
}

.chip-cat {
  font-size: 10px;
  opacity: 0.8;
  background-color: rgba(0, 0, 0, 0.06);
  padding: 1px 5px;
  border-radius: 4px;
}

.active-prompt-banner {
  background-color: var(--bg-surface);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  padding: 12px 16px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  flex-shrink: 0;
}

.banner-top-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.prompt-identity {
  display: flex;
  align-items: center;
  gap: 8px;
}

.badge-cat {
  font-size: 10px;
  font-weight: 700;
  background-color: rgba(66, 153, 225, 0.15);
  color: var(--primary);
  padding: 2px 8px;
  border-radius: 4px;
}

.prompt-name {
  font-size: 13.5px;
  font-weight: 700;
  color: var(--text-main);
  margin: 0;
}

.prompt-desc-text {
  font-size: 12px;
  color: var(--text-muted);
  font-style: italic;
  margin: 0;
  line-height: 1.4;
}

.json-badge-hint {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  color: #38A169;
  background-color: rgba(56, 161, 105, 0.08);
  padding: 4px 10px;
  border-radius: 6px;
  width: fit-content;
}

.prompt-edit-inline {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.text-area-sm {
  font-size: 12px;
  width: 100%;
}

.edit-actions-sm {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

.btn-xs {
  padding: 3px 8px;
  font-size: 11px;
  border-radius: 4px;
}

.prompts-chat-panel {
  display: flex;
  flex-direction: column;
  flex: 1;
  background-color: var(--bg-surface);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  overflow: hidden;
}

.executed-tool-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 11.5px;
  font-weight: 700;
  color: #DD6B20;
  background-color: rgba(221, 107, 32, 0.12);
  border: 1px dashed #DD6B20;
  padding: 4px 10px;
  border-radius: 6px;
  margin-top: 8px;
  width: fit-content;
}

.zap-icon {
  color: #DD6B20;
}

.json-code-box {
  background-color: var(--bg-app);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  margin-top: 8px;
  overflow: hidden;
}

.code-box-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background-color: var(--bg-card-hover);
  padding: 4px 10px;
  font-size: 10.5px;
  font-weight: 700;
  color: var(--text-muted);
  border-bottom: 1px solid var(--border-color);
}

.code-tag {
  background-color: var(--primary);
  color: #ffffff;
  padding: 1px 5px;
  border-radius: 3px;
  font-size: 9.5px;
}

.json-pre-code {
  font-family: 'Fira Code', 'Courier New', monospace;
  font-size: 11px;
  color: #319795;
  padding: 8px 12px;
  margin: 0;
  overflow-x: auto;
  line-height: 1.4;
}

.prompts-quick-triggers {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 14px;
  background-color: var(--bg-app);
  border-top: 1px solid var(--border-color);
  overflow-x: auto;
  flex-shrink: 0;
}

.trigger-label {
  font-size: 11px;
  font-weight: 700;
  color: var(--text-muted);
  white-space: nowrap;
}

.chip-trigger {
  background-color: var(--bg-surface);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 3px 10px;
  font-size: 11px;
  color: var(--text-main);
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.2s ease;
}

.chip-trigger:hover {
  border-color: var(--primary);
  color: var(--primary);
}

.sender-user .bubble-header {
  justify-content: flex-end;
}

.bubble-text {
  padding: 12px 16px;
  border-radius: 12px;
  font-size: 13.5px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
}

.sender-user .bubble-text {
  background-color: var(--primary);
  color: #ffffff;
  border-top-right-radius: 2px;
}

.sender-ai .bubble-text {
  background-color: var(--bg-surface);
  color: var(--text-main);
  border: 1px solid var(--border-color);
  border-top-left-radius: 2px;
}

.sender-system .bubble-text {
  background-color: rgba(229, 62, 62, 0.1);
  color: #e53e3e;
  border: 1px solid rgba(229, 62, 62, 0.3);
}

.action-result-card {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 8px 12px;
  background-color: rgba(128, 90, 213, 0.1);
  border: 1px solid rgba(128, 90, 213, 0.3);
  border-radius: 8px;
  margin-top: 4px;
  font-size: 12px;
}

.card-action-type {
  font-weight: 700;
  color: var(--ai-purple);
  display: flex;
  align-items: center;
  gap: 4px;
}

.card-action-msg {
  color: var(--text-main);
}

.thinking-box {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  background-color: var(--bg-surface);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  font-size: 12px;
  color: var(--text-muted);
}

.thinking-box .dot {
  width: 6px;
  height: 6px;
  background-color: var(--primary);
  border-radius: 50%;
  animation: bounce 1.4s infinite ease-in-out both;
}

.thinking-box .dot:nth-child(1) { animation-delay: -0.32s; }
.thinking-box .dot:nth-child(2) { animation-delay: -0.16s; }

@keyframes bounce {
  0%, 80%, 100% { transform: scale(0); }
  40% { transform: scale(1); }
}

.chat-input-bar {
  padding: 16px 24px;
  background-color: var(--bg-surface);
  border-top: 1px solid var(--border-color);
  display: flex;
  align-items: center;
  gap: 16px;
  max-width: 900px;
  margin: 0 auto;
  width: 100%;
  box-sizing: border-box;
}

.chat-textarea {
  flex: 1;
  padding: 10px 14px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--border-color);
  background-color: var(--bg-app);
  color: var(--text-main);
  font-family: inherit;
  font-size: 13px;
  outline: none;
  resize: none;
}

.chat-textarea:focus {
  border-color: var(--primary);
}

.btn-send-msg {
  background-color: var(--ai-purple);
  color: #ffffff;
  border: none;
  padding: 12px 20px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-send-msg:hover:not(:disabled) {
  opacity: 0.9;
  transform: translateY(-1px);
}

.btn-inner {
  display: flex;
  align-items: center;
  gap: 6px;
}

/* 2. Prompts View */
.prompts-view-wrapper {
  padding: 30px;
  overflow-y: auto;
  max-width: 900px;
  margin: 0 auto;
  width: 100%;
}

.prompts-header-box {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 20px;
}

.prompts-header-text {
  flex: 1;
}

.prompts-header-text h3 {
  font-size: 16px;
  color: var(--primary);
  margin-bottom: 6px;
}

.prompts-header-text p {
  font-size: 12px;
  color: var(--text-muted);
}

.btn-add-prompt {
  white-space: nowrap;
  flex-shrink: 0;
}

.prompts-cards-single-column {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.prompt-single-card {
  background-color: var(--bg-surface);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  padding: 16px 20px;
  transition: all 0.2s ease;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.03);
}

.prompt-single-card:hover {
  border-color: var(--primary);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.06);
}

.prompt-single-card.is-editing {
  border-color: var(--primary);
  background-color: var(--bg-card);
}

.prompt-view-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
}

.card-left-info {
  display: flex;
  flex-direction: column;
  gap: 8px;
  flex: 1;
  min-width: 0;
}

.card-top-header {
  display: flex;
  align-items: center;
  gap: 10px;
}

.category-badge {
  font-size: 10px;
  background-color: rgba(66, 153, 225, 0.15);
  color: var(--primary);
  padding: 2px 8px;
  border-radius: 4px;
  font-weight: 600;
  flex-shrink: 0;
}

.prompt-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-main);
  margin: 0;
}

.prompt-text {
  font-size: 12.5px;
  color: var(--text-muted);
  line-height: 1.5;
  margin: 0;
  word-break: break-word;
}

.btn-clear-topbar {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 5px 12px;
  border-radius: 6px;
  border: 1px solid rgba(229, 62, 62, 0.25);
  background-color: rgba(229, 62, 62, 0.06);
  color: #e53e3e;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  margin-left: 8px;
}

.btn-clear-topbar:hover {
  background-color: #e53e3e;
  color: #ffffff;
  border-color: #e53e3e;
  box-shadow: 0 2px 8px rgba(229, 62, 62, 0.3);
}

/* 4. Full Featured AI Settings View */
.ai-settings-view {
  flex: 1;
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
  background-color: var(--bg-app);
}

.settings-header-banner {
  padding: 20px 24px 14px 24px;
  background-color: var(--bg-surface);
  border-bottom: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  gap: 16px;
  flex-shrink: 0;
}

.banner-title-group {
  display: flex;
  align-items: center;
  gap: 14px;
}

.intro-icon {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  background-color: rgba(49, 130, 206, 0.12);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--primary);
  flex-shrink: 0;
}

.intro-text h3 {
  font-size: 17px;
  font-weight: 800;
  margin: 0 0 4px 0;
  color: var(--text-main);
}

.intro-text p {
  font-size: 12.5px;
  color: var(--text-muted);
  margin: 0;
}

/* Settings Sub Tabs */
.settings-sub-tabs {
  display: flex;
  align-items: center;
  gap: 8px;
  overflow-x: auto;
  padding-bottom: 2px;
}

.sub-tab-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  border-radius: 8px;
  border: 1px solid var(--border-color);
  background-color: var(--bg-app);
  color: var(--text-muted);
  font-size: 12.5px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  white-space: nowrap;
}

.sub-tab-btn:hover {
  border-color: var(--primary);
  color: var(--text-main);
}

.sub-tab-btn.active {
  background-color: var(--primary);
  color: #ffffff;
  border-color: var(--primary);
  box-shadow: 0 2px 8px rgba(49, 130, 206, 0.3);
}

/* Scroll Content Area */
.settings-content-scroll {
  flex: 1;
  padding: 24px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.settings-section-card {
  background-color: var(--bg-surface);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.02);
}

.section-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-bottom: 12px;
  border-bottom: 1px dashed var(--border-color);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.section-icon {
  color: var(--primary);
}

.header-left h4 {
  font-size: 15px;
  font-weight: 700;
  color: var(--text-main);
  margin: 0;
}

.section-badge {
  font-size: 11px;
  font-weight: 700;
  padding: 3px 8px;
  border-radius: 6px;
  background-color: rgba(49, 130, 206, 0.1);
  color: var(--primary);
}

.section-desc {
  font-size: 12.5px;
  color: var(--text-muted);
  margin: 0;
}

/* Section 1 LLM Form */
.presets-row {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
}

.preset-title {
  color: var(--text-muted);
}

.preset-chip {
  background-color: var(--bg-app);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 5px 12px;
  font-size: 12px;
  color: var(--text-main);
  cursor: pointer;
  transition: all 0.2s ease;
}

.preset-chip:hover {
  border-color: var(--primary);
  color: var(--primary);
}

.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  width: 100%;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
  width: 100%;
}

.form-label {
  font-size: 12px;
  font-weight: 700;
  color: var(--text-main);
}

.select-input,
.text-input {
  width: 100% !important;
  box-sizing: border-box !important;
  height: 38px;
  padding: 8px 12px;
  font-size: 13px;
  border-radius: 8px;
  border: 1px solid var(--border-color);
  background-color: var(--bg-app);
  color: var(--text-main);
  outline: none;
}

.select-input:focus,
.text-input:focus {
  border-color: var(--primary);
}

/* Section 2 Prompts Settings Grid */
.prompts-settings-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 14px;
}

.prompt-setting-card {
  background-color: var(--bg-app);
  border: 1px solid var(--border-color);
  border-radius: 10px;
  padding: 14px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  transition: all 0.2s ease;
}

.prompt-setting-card.active {
  border-color: var(--primary);
  box-shadow: 0 0 0 2px rgba(49, 130, 206, 0.2);
  background-color: var(--bg-surface);
}

.card-top-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.badge-group {
  display: flex;
  align-items: center;
  gap: 6px;
}

.badge-active-tag {
  font-size: 10px;
  font-weight: 700;
  padding: 2px 6px;
  border-radius: 4px;
  background-color: #38a169;
  color: #ffffff;
}

.card-btn-group {
  display: flex;
  align-items: center;
  gap: 4px;
}

.btn-icon-action {
  width: 26px;
  height: 26px;
  border-radius: 6px;
  border: 1px solid var(--border-color);
  background-color: var(--bg-surface);
  color: var(--text-muted);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.15s ease;
}

.btn-icon-action:hover {
  border-color: var(--primary);
  color: var(--primary);
}

.btn-icon-action.is-selected {
  background-color: #38a169;
  color: #ffffff;
  border-color: #38a169;
}

.btn-icon-action.danger:hover {
  background-color: #e53e3e;
  color: #ffffff;
  border-color: #e53e3e;
}

.card-prompt-title {
  font-size: 13.5px;
  font-weight: 700;
  color: var(--text-main);
  margin: 0;
  cursor: pointer;
}

.card-prompt-text {
  font-size: 12px;
  color: var(--text-muted);
  margin: 0;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* Edit Mode inside Card */
.card-edit-form {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.edit-row {
  display: flex;
  gap: 6px;
}

.edit-input-sm {
  width: 80px;
  padding: 4px 8px;
  font-size: 11px;
  border-radius: 4px;
  border: 1px solid var(--border-color);
  background: var(--bg-surface);
  color: var(--text-main);
}

.edit-input-title {
  flex: 1;
  padding: 4px 8px;
  font-size: 12px;
  border-radius: 4px;
  border: 1px solid var(--border-color);
  background: var(--bg-surface);
  color: var(--text-main);
  font-weight: 700;
}

.edit-textarea {
  width: 100%;
  box-sizing: border-box;
  padding: 6px 8px;
  font-size: 12px;
  border-radius: 6px;
  border: 1px solid var(--border-color);
  background: var(--bg-surface);
  color: var(--text-main);
  resize: vertical;
  font-family: inherit;
}

.edit-actions {
  display: flex;
  gap: 6px;
  justify-content: flex-end;
}

/* Section 3 Tools Settings List */
.tools-settings-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.tool-setting-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 14px;
  border-radius: 8px;
  border: 1px solid var(--border-color);
  background-color: var(--bg-app);
  transition: all 0.2s ease;
}

.tool-setting-row.disabled {
  opacity: 0.6;
}

.tool-left-info {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
  min-width: 0;
}

.checkbox-container {
  display: inline-flex;
  position: relative;
  cursor: pointer;
  user-select: none;
}

.checkbox-container input {
  position: absolute;
  opacity: 0;
  cursor: pointer;
  height: 0;
  width: 0;
}

.checkmark {
  height: 18px;
  width: 18px;
  background-color: var(--bg-surface);
  border: 1.5px solid var(--border-color);
  border-radius: 4px;
  transition: all 0.2s ease;
}

.checkbox-container:hover input ~ .checkmark {
  border-color: var(--primary);
}

.checkbox-container input:checked ~ .checkmark {
  background-color: var(--primary);
  border-color: var(--primary);
}

.checkmark:after {
  content: "";
  position: absolute;
  display: none;
  left: 6px;
  top: 2px;
  width: 4px;
  height: 9px;
  border: solid white;
  border-width: 0 2px 2px 0;
  transform: rotate(45deg);
}

.checkbox-container input:checked ~ .checkmark:after {
  display: block;
}

.tool-text-meta {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.tool-title-line {
  display: flex;
  align-items: center;
  gap: 8px;
}

.tool-desc {
  font-size: 12px;
  color: var(--text-muted);
  margin: 0;
}

.tool-right-switch {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
}

.switch-status {
  font-size: 12px;
  color: var(--text-muted);
  font-weight: 500;
}

.switch-status.active {
  color: #38a169;
  font-weight: 700;
}

/* Section 4 Skills Settings Grid */
.skills-settings-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 14px;
}

.skill-setting-card {
  background-color: var(--bg-app);
  border: 1px solid var(--border-color);
  border-radius: 10px;
  padding: 14px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  transition: all 0.2s ease;
}

.skill-setting-card.disabled {
  opacity: 0.65;
}

.skill-card-body {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.skill-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.skill-title-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.skill-cat-badge {
  font-size: 10px;
  font-weight: 700;
  padding: 2px 6px;
  border-radius: 4px;
  background-color: rgba(128, 90, 213, 0.15);
  color: #805ad5;
}

.skill-name {
  font-size: 13.5px;
  font-weight: 700;
  color: var(--text-main);
  margin: 0;
}

.skill-actions {
  display: flex;
  gap: 4px;
}

.skill-desc {
  font-size: 12px;
  color: var(--text-muted);
  margin: 0;
  line-height: 1.4;
}

.skill-prompt-preview {
  background-color: var(--bg-surface);
  border: 1px dashed var(--border-color);
  border-radius: 6px;
  padding: 6px 8px;
  font-size: 11px;
  color: var(--text-muted);
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.preview-label {
  font-weight: 700;
  color: var(--primary);
  font-size: 10px;
}

.preview-text {
  word-break: break-all;
  white-space: pre-wrap;
}

/* Save Footer (Fixed at bottom of settings view) */
.settings-actions-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 12px 24px;
  background-color: var(--bg-surface);
  border-top: 1px solid var(--border-color);
  flex-shrink: 0;
}

.footer-save-summary {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.footer-save-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-muted);
  white-space: nowrap;
}

.footer-provider-tag,
.footer-model-tag {
  font-size: 11.5px;
  font-weight: 700;
  padding: 3px 10px;
  border-radius: 12px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 180px;
}

.footer-provider-tag {
  background-color: rgba(49, 130, 206, 0.12);
  color: var(--primary);
}

.footer-model-tag {
  background-color: rgba(128, 90, 213, 0.12);
  color: var(--ai-purple);
}

.btn-save-all {
  padding: 10px 24px !important;
  font-size: 14px !important;
  font-weight: 700 !important;
  border-radius: 10px !important;
  flex-shrink: 0;
}

/* Interactive Modes Switcher & Guide Cards in Settings */
.settings-mode-nav-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 6px;
}

.mode-nav-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 18px;
  border-radius: 10px;
  border: 1.5px solid var(--border-color);
  background-color: var(--bg-app);
  color: var(--text-muted);
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s ease;
}

.mode-nav-btn:hover {
  border-color: var(--primary);
  color: var(--text-main);
}

.mode-nav-btn.active {
  background-color: var(--primary);
  color: #ffffff;
  border-color: var(--primary);
  box-shadow: 0 4px 12px rgba(49, 130, 206, 0.3);
}

.active-dot {
  font-size: 11px;
  opacity: 0.9;
  background: rgba(255, 255, 255, 0.2);
  padding: 2px 6px;
  border-radius: 10px;
}

.modes-guide-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 16px;
}

.mode-guide-card {
  background-color: var(--bg-app);
  border: 1.5px solid var(--border-color);
  border-radius: 12px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  gap: 14px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.mode-guide-card:hover {
  border-color: var(--primary);
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.05);
}

.mode-guide-card.active {
  border-color: var(--primary);
  background-color: var(--bg-surface);
  box-shadow: 0 0 0 2px rgba(49, 130, 206, 0.25);
}

.guide-card-header {
  display: flex;
  align-items: center;
  gap: 12px;
}

.guide-icon-badge {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.guide-icon-badge.chat {
  background-color: rgba(49, 130, 206, 0.12);
  color: #3182ce;
}

.guide-icon-badge.prompts {
  background-color: rgba(128, 90, 213, 0.12);
  color: #805ad5;
}

.guide-icon-badge.agent {
  background-color: rgba(56, 161, 105, 0.12);
  color: #38a169;
}

.guide-title-group {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.guide-title-group h5 {
  font-size: 13.5px;
  font-weight: 800;
  color: var(--text-main);
  margin: 0;
}

.guide-tag {
  font-size: 11px;
  font-weight: 600;
  color: var(--text-muted);
}

.guide-body {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.guide-field {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.field-label {
  font-size: 11.5px;
  font-weight: 700;
  color: var(--text-main);
}

.guide-field p {
  font-size: 12px;
  color: var(--text-muted);
  margin: 0;
  line-height: 1.45;
}

.guide-card-footer {
  display: flex;
  justify-content: flex-end;
  padding-top: 4px;
}

.btn-success {
  background-color: #38a169 !important;
  color: #ffffff !important;
  border-color: #38a169 !important;
  font-weight: 700 !important;
}

/* Summary Tips Box */
.modes-summary-tip-box {
  background: linear-gradient(135deg, rgba(49, 130, 206, 0.06), rgba(128, 90, 213, 0.06));
  border: 1px dashed var(--primary);
  border-radius: 10px;
  padding: 14px 16px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.summary-tip-header {
  display: flex;
  align-items: center;
  gap: 6px;
}

.tip-sparkle {
  color: var(--primary);
}

.summary-tip-title {
  font-size: 13px;
  font-weight: 800;
  color: var(--text-main);
}

.summary-tip-list {
  margin: 0;
  padding-left: 20px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 12.5px;
  color: var(--text-muted);
}

.summary-tip-list li strong {
  color: var(--text-main);
}
</style>

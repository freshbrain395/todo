<template>
  <div class="settings-container animate-fade-in">
    <div class="settings-layout">
      <!-- VS Code 风格左侧设置导航栏 -->
      <aside class="settings-sidebar">
        <div class="settings-sidebar-header">
          <h2 class="sidebar-title"><Settings :size="18" /> 系统设置</h2>
        </div>

        <nav class="settings-nav-list">
          <button
            class="settings-nav-item"
            :class="{ active: activeTab === 'llm' }"
            @click="activeTab = 'llm'"
          >
            <Brain :size="16" /> <span>大模型参数</span>
          </button>

          <button
            class="settings-nav-item"
            :class="{ active: activeTab === 'prompts' }"
            @click="activeTab = 'prompts'"
          >
            <Sparkles :size="16" />
            <span class="nav-text">Prompts 预设</span>
            <span class="nav-badge">{{ promptLibrary.length }}</span>
          </button>

          <button
            class="settings-nav-item"
            :class="{ active: activeTab === 'tools' }"
            @click="activeTab = 'tools'"
          >
            <Wrench :size="16" />
            <span class="nav-text">Agent 工具</span>
            <span class="nav-badge">{{ enabledToolsCount }}/{{ agentTools.length }}</span>
          </button>

          <button
            class="settings-nav-item"
            :class="{ active: activeTab === 'skills' }"
            @click="activeTab = 'skills'"
          >
            <BookOpen :size="16" />
            <span class="nav-text">Skills 技能库</span>
            <span class="nav-badge">{{ enabledSkillsCount }}/{{ skillsLibrary.length }}</span>
          </button>

          <button
            class="settings-nav-item"
            :class="{ active: activeTab === 'appearance' }"
            @click="activeTab = 'appearance'"
          >
            <Palette :size="16" /> <span>外观与主题</span>
          </button>

          <button
            class="settings-nav-item"
            :class="{ active: activeTab === 'audio' }"
            @click="activeTab = 'audio'"
          >
            <Volume2 :size="16" /> <span>提示与音效</span>
          </button>

          <button
            class="settings-nav-item"
            :class="{ active: activeTab === 'account' }"
            @click="activeTab = 'account'"
          >
            <User :size="16" /> <span>账号与权限</span>
          </button>

          <button
            class="settings-nav-item"
            :class="{ active: activeTab === 'backup' }"
            @click="activeTab = 'backup'"
          >
            <FileJson :size="16" /> <span>备份与危险区</span>
          </button>
        </nav>
      </aside>

      <!-- 右侧设置详细内容区 -->
      <main class="settings-content">

      <!-- 选项卡 1 ~ 4: AI 模块相关设置 (渲染 AiSettingsView) -->
      <div v-if="['llm', 'prompts', 'tools', 'skills'].includes(activeTab)" class="tab-pane">
        <AiSettingsView
          :active-tab="(activeTab as 'llm' | 'prompts' | 'tools' | 'skills')"
          :saved-providers="savedProviders"
          :local-config="llmConfig"
          :fetched-models="fetchedModels"
          :is-fetching-models="isFetchingModels"
          :fetch-model-error="fetchModelError"
          :prompt-library="promptLibrary"
          v-model:active-prompt-id="activePromptId"
          :editing-prompt-id="editingPromptId"
          :edit-form="editForm"
          :agent-tools="agentTools"
          :skills-library="skillsLibrary"
          :editing-skill-id="editingSkillId"
          :skill-form="skillForm"
          @update-provider="onProviderEdited"
          @select-provider="selectProvider"
          @delete-provider="deleteProvider"
          @fetch-models="fetchModels"
          @add-custom-provider="addCustomProvider"
          @update-thinking="val => llmConfig.enable_thinking = val"
          @add-new-prompt="addNewPrompt"
          @start-edit-prompt="startEditPrompt"
          @save-edit-prompt="saveEditPrompt"
          @cancel-edit-prompt="cancelEditPrompt"
          @delete-prompt="deletePrompt"
          @enable-all-tools="enableAllTools"
          @disable-all-tools="disableAllTools"
          @reset-default-tools="resetToolsDefault"
          @save-tools="saveToolsStorage"
          @enable-all-skills="enableAllSkills"
          @disable-all-skills="disableAllSkills"
          @add-new-skill="addNewSkill"
          @start-edit-skill="startEditSkill"
          @save-edit-skill="saveEditSkill"
          @cancel-edit-skill="cancelEditSkill"
          @delete-skill="deleteSkill"
          @save-skills="saveSkillsStorage"
        />
      </div>

      <!-- 选项卡 5: 外观界面主题 -->
      <div v-else-if="activeTab === 'appearance'" class="tab-pane">
        <div class="settings-section">
          <h3 class="section-title"><Palette :size="16" /> 界面主题与视觉外观</h3>
          <div class="setting-item">
            <div class="item-label">
              <span>系统应用主题</span>
              <small>选择您喜爱的界面视觉风格（浅色、暗黑或极光风格）</small>
            </div>
            <div class="item-control">
              <select v-model="theme" class="select-input" @change="saveThemeSettings">
                <option value="light">浅色明亮 (Light Classic)</option>
                <option value="dark">暗黑现代 (Dark Modern)</option>
                <option value="nord">极光冰蓝 (Nord Aurora)</option>
              </select>
            </div>
          </div>

          <div class="setting-item">
            <div class="item-label">
              <span>导航栏布局位置</span>
              <small>选择导航栏展示在顶部或作为类似 VS Code 的左侧边栏</small>
            </div>
            <div class="item-control">
              <select v-model="navPosition" class="select-input" @change="saveNavPositionSettings">
                <option value="top">顶部导航栏 (Top Navbar)</option>
                <option value="left">左侧边栏 (VS Code 风格)</option>
                <option value="desktop">桌面图标视图 (Desktop OS 风格)</option>
              </select>
            </div>
          </div>
        </div>
      </div>

      <!-- 选项卡 6: 提示与音效 -->
      <div v-else-if="activeTab === 'audio'" class="tab-pane">
        <div class="settings-section">
          <h3 class="section-title"><Volume2 :size="16" /> 定时与响铃提醒音效设置</h3>

          <div class="setting-item">
            <div class="item-label">
              <span>提醒音效类型</span>
              <small>在番茄钟、倒计时与闹钟响铃时播放的声音</small>
            </div>
            <div class="item-control">
              <select v-model="soundType" class="select-input" @change="saveAudioSettings">
                <option value="chime">清脆金铃 (Digital Chime)</option>
                <option value="marimba">柔和木鱼 (Soft Marimba)</option>
                <option value="cyber">科技和声 (Cyber Pulse)</option>
                <option value="beep">警报哔哔 (Beep Alert)</option>
              </select>
              <button class="btn btn-listen" @click="testSound">
                <Volume2 :size="14" /> 试听音效
              </button>
            </div>
          </div>

          <div class="setting-item">
            <div class="item-label">
              <span>响铃音量大小 ({{ Math.round(soundVolume * 100) }}%)</span>
              <small>调节提醒声音播放音量</small>
            </div>
            <div class="item-control">
              <input
                type="range"
                min="0"
                max="1"
                step="0.05"
                v-model.number="soundVolume"
                class="volume-slider"
                @input="saveAudioSettings"
              />
            </div>
          </div>
        </div>
      </div>

      <!-- 选项卡 7: 账号与权限 -->
      <div v-else-if="activeTab === 'account'" class="tab-pane">
        <div class="settings-section">
          <h3 class="section-title"><User :size="16" /> 用户账号与权限配置</h3>
          <div class="setting-item">
            <div class="item-label">
              <span>当前登录账号：<strong>{{ currentUserName }}</strong> <span v-if="isAdmin" class="admin-tag"><Crown :size="12" /> 管理员</span></span>
              <small>当前账号配置均实时存储在前端 JSON 集合中</small>
            </div>
            <div class="item-control">
              <button v-if="isAdmin" class="btn btn-admin-manage" @click="isAdminModalOpen = true">
                <ShieldCheck :size="14" /> 管理员用户列表与权限
              </button>
              <button class="btn btn-listen" @click="isSwitchModalOpen = true">
                <Users :size="14" /> 切换 / 新增用户账号
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- 选项卡 8: 数据备份与危险区 -->
      <div v-else-if="activeTab === 'backup'" class="tab-pane">
        <div class="settings-section">
          <h3 class="section-title"><FileJson :size="16" /> JSON 格式配置导出与恢复</h3>

          <div class="setting-item">
            <div class="item-label">
              <span>备份与恢复独立 JSON 配置文件</span>
              <small>将当前用户的全套偏好配置导出为 .json 文件，或从已有 JSON 配置文件中一键导入</small>
            </div>
            <div class="item-control">
              <button class="btn btn-listen" @click="exportJsonConfig">
                <Download :size="14" /> 导出 JSON 配置
              </button>
              <button class="btn btn-listen" @click="triggerImport">
                <Upload :size="14" /> 导入 JSON 配置
              </button>
              <input
                type="file"
                ref="fileInputRef"
                accept=".json,application/json"
                style="display: none;"
                @change="handleImportJson"
              />
            </div>
          </div>
        </div>

        <div class="settings-section">
          <h3 class="section-title"><Trash2 :size="16" /> 重置与危险操作区</h3>

          <div class="setting-item">
            <div class="item-label">
              <span>恢复默认设置与应用缓存</span>
              <small>重置所有音效偏好、主题配置和页面交互历史状态</small>
            </div>
            <div class="item-control">
              <button class="btn btn-reset-danger" @click="resetAllSettings">
                <RotateCcw :size="14" /> 重置当前用户偏好设置
              </button>
            </div>
          </div>
        </div>
      </div>
    </main>
  </div>

    <!-- 用户切换弹窗 -->
    <UserSwitchModal
      :isOpen="isSwitchModalOpen"
      @close="isSwitchModalOpen = false"
      @userSwitched="onUserSwitched"
    />

    <!-- 管理员用户管理弹窗 -->
    <AdminUserManagementModal
      :isOpen="isAdminModalOpen"
      @close="isAdminModalOpen = false"
      @refresh="onUserSwitched"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import {
  Settings, Volume2, Trash2, RotateCcw, User, Users,
  FileJson, Download, Upload, ShieldCheck, Palette, Brain,
  Sparkles, Wrench, BookOpen, Crown
} from 'lucide-vue-next'
import { soundPlayer, type SoundType } from '../../utils/audio'
import { showConfirm } from '../../utils/confirmState'
import UserSwitchModal from './UserSwitchModal.vue'
import AdminUserManagementModal from './AdminUserManagementModal.vue'
import AiSettingsView from '../ai/AiSettingsView.vue'

import {
  getCurrentUserId,
  getUserConfig,
  saveUserConfig,
  getAllUserAccountsMap,
  isCurrentAdmin,
  DEFAULT_USER_CONFIG,
  type UserAppConfig
} from '../../utils/configManager'
import type { LlmConfig, ThemeType, NavPosition } from '../../types'
import {
  defaultAgentTools,
  type SkillItem,
  type PromptItem,
  type AgentToolItem
} from '../../utils/aiDefaults'
import {
  getProviders,
  saveProviders,
  getPrompts,
  savePrompts,
  getActivePromptId,
  setActivePromptId,
  getSkills,
  saveSkills,
  getToolConfig,
  saveToolConfig,
  saveNavPosition
} from '../../utils/aiStorage'



const emit = defineEmits<{
  (e: 'update:soundType', type: SoundType): void
  (e: 'update:soundVolume', vol: number): void
  (e: 'update:theme', theme: ThemeType): void
  (e: 'update:navPosition', pos: NavPosition): void
  (e: 'update:config', config: LlmConfig): void
  (e: 'userChanged'): void
}>()

const isSwitchModalOpen = ref(false)
const isAdminModalOpen = ref(false)
const fileInputRef = ref<HTMLInputElement | null>(null)

const userId = ref(getCurrentUserId())
const currentConfig = ref<UserAppConfig>(getUserConfig(userId.value))

const soundType = ref<SoundType>(currentConfig.value.soundType)
const soundVolume = ref<number>(currentConfig.value.soundVolume)
const theme = ref<ThemeType>(currentConfig.value.theme || 'light')
const navPosition = ref<NavPosition>(currentConfig.value.navPosition || 'top')

// Theme save
function saveThemeSettings() {
  saveUserConfig(userId.value, { theme: theme.value })
  document.documentElement.setAttribute('data-theme', theme.value)
  emit('update:theme', theme.value)
}

// Nav position save
function saveNavPositionSettings() {
  saveUserConfig(userId.value, { navPosition: navPosition.value })
  saveNavPosition(navPosition.value)
  emit('update:navPosition', navPosition.value)
}

// Single Flat Tab Navigation State (8 items in PRD order)
type SettingsFlatTab = 'llm' | 'prompts' | 'tools' | 'skills' | 'appearance' | 'audio' | 'account' | 'backup'
const activeTab = ref<SettingsFlatTab>('llm')

const llmConfig = ref<LlmConfig>({ ...currentConfig.value.llmConfig })

watch(() => currentConfig.value.llmConfig, (newVal) => {
  if (newVal) {
    llmConfig.value = { ...newVal }
  }
}, { deep: true })

watch(llmConfig, (newVal) => {
  saveUserConfig(userId.value, { llmConfig: newVal })
  emit('update:config', { ...newVal })
}, { deep: true })

interface CustomLlmProvider {
  id: string
  name: string
  base_url: string
  api_key: string
  model: string
  is_custom?: boolean
}

const savedProviders = ref<CustomLlmProvider[]>(getProviders())

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

    if (typeof window !== 'undefined' && '__TAURI_INTERNALS__' in window) {
      const { invoke } = await import('@tauri-apps/api/core')
      modelNames = await invoke<string[]>('fetch_models', {
        baseUrl: p.base_url,
        apiKey: p.api_key || ''
      })
    } else {
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
    fetchModelError.value[p.id] = '获取失败: ' + (err.message || String(err))
    isManualModel.value[p.id] = true
  } finally {
    isFetchingModels.value[p.id] = false
  }
}

function saveProvidersStorage() {
  saveProviders(savedProviders.value)
}

function onProviderEdited(p: CustomLlmProvider) {
  if (llmConfig.value.provider === p.id) {
    llmConfig.value.base_url = p.base_url
    llmConfig.value.api_key = p.api_key
    llmConfig.value.model = p.model
  }
  saveProvidersStorage()
  if (p.base_url) {
    fetchModels(p)
  }
}

function selectProvider(p: CustomLlmProvider) {
  llmConfig.value.provider = p.id
  llmConfig.value.base_url = p.base_url
  llmConfig.value.api_key = p.api_key
  llmConfig.value.model = p.model
  saveProvidersStorage()
}

function addCustomProvider() {
  const name = prompt('请输入新卡片的名称（如: OpenAI）:')
  if (!name) return
  const id = 'custom_' + Date.now()
  const newP: CustomLlmProvider = {
    id,
    name,
    base_url: '',
    api_key: '',
    model: '',
    is_custom: true
  }
  savedProviders.value.push(newP)
  saveProvidersStorage()
  selectProvider(newP)
}

function deleteProvider(id: string) {
  savedProviders.value = savedProviders.value.filter(p => p.id !== id)
  saveProvidersStorage()
}

// Prompts State & Functions
const promptLibrary = ref<PromptItem[]>(getPrompts())
const activePromptId = ref<string>(getActivePromptId())
const editingPromptId = ref<string | null>(null)
const editForm = ref({ category: '', title: '', text: '', jsonFormat: '' })

watch(activePromptId, (newId) => {
  setActivePromptId(newId)
})

function savePromptLibraryStorage() {
  savePrompts(promptLibrary.value)
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

function deletePrompt(id: string) {
  if (!confirm('确定要删除该提示词卡片吗？')) return
  promptLibrary.value = promptLibrary.value.filter(p => p.id !== id)
  savePromptLibraryStorage()
  if (activePromptId.value === id && promptLibrary.value.length > 0) {
    activePromptId.value = promptLibrary.value[0].id
  }
  if (editingPromptId.value === id) {
    editingPromptId.value = null
  }
}

// Agent Tools State & Functions
const storedToolsConfig = getToolConfig()
let initialEnabledMap: Record<string, boolean> = storedToolsConfig || {}

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
  saveToolConfig(map)
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

// Skills State & Functions
const skillsLibrary = ref<SkillItem[]>(getSkills())

const enabledSkillsCount = computed(() => skillsLibrary.value.filter(s => s.enabled).length)

function saveSkillsStorage() {
  saveSkills(skillsLibrary.value)
}

function enableAllSkills() {
  skillsLibrary.value.forEach(s => s.enabled = true)
  saveSkillsStorage()
}

function disableAllSkills() {
  skillsLibrary.value.forEach(s => s.enabled = false)
  saveSkillsStorage()
}

const editingSkillId = ref<string | null>(null)
const skillForm = ref({ title: '', category: '', description: '', systemPrompt: '' })

function startEditSkill(item: SkillItem) {
  editingSkillId.value = item.id
  skillForm.value = { title: item.title, category: item.category, description: item.description, systemPrompt: item.systemPrompt }
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
  skillsLibrary.value.push({
    id: newId,
    title: '新建自定义技能',
    category: '自定义',
    description: '技能描述说明...',
    systemPrompt: '技能提示词...',
    enabled: true
  })
  saveSkillsStorage()
}

function deleteSkill(id: string) {
  if (!confirm('确定删除此 Skill 技能吗？')) return
  skillsLibrary.value = skillsLibrary.value.filter(s => s.id !== id)
  saveSkillsStorage()
}

const isAdmin = computed(() => isCurrentAdmin())

const currentUserName = computed(() => {
  const map = getAllUserAccountsMap()
  return map[userId.value]?.user.username || '未知用户'
})

function syncFromConfig() {
  userId.value = getCurrentUserId()
  currentConfig.value = getUserConfig(userId.value)
  soundType.value = currentConfig.value.soundType
  soundVolume.value = currentConfig.value.soundVolume
  theme.value = currentConfig.value.theme || 'light'
  navPosition.value = currentConfig.value.navPosition || 'top'
  llmConfig.value = { ...currentConfig.value.llmConfig }
}

onMounted(() => {
  syncFromConfig()
})

function testSound() {
  soundPlayer.play(soundType.value, soundVolume.value)
}

function saveAudioSettings() {
  saveUserConfig(userId.value, {
    soundType: soundType.value,
    soundVolume: soundVolume.value,
  })
  emit('update:soundType', soundType.value)
  emit('update:soundVolume', soundVolume.value)
}

function onUserSwitched() {
  syncFromConfig()
  emit('update:soundType', soundType.value)
  emit('update:soundVolume', soundVolume.value)
  emit('update:theme', theme.value)
  emit('update:navPosition', navPosition.value)
  emit('update:config', llmConfig.value)
  emit('userChanged')
}

// JSON 导出
function exportJsonConfig() {
  const configData = getUserConfig(userId.value)
  const jsonStr = JSON.stringify(configData, null, 2)
  const blob = new Blob([jsonStr], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `user_config_${userId.value}.json`
  a.click()
  URL.revokeObjectURL(url)
}

// JSON 导入
function triggerImport() {
  fileInputRef.value?.click()
}

function handleImportJson(e: Event) {
  const target = e.target as HTMLInputElement
  if (!target.files || target.files.length === 0) return
  const file = target.files[0]
  const reader = new FileReader()
  reader.onload = (event) => {
    try {
      const imported = JSON.parse(event.target?.result as string)
      if (typeof imported === 'object' && imported !== null) {
        saveUserConfig(userId.value, imported)
        syncFromConfig()
        emit('update:soundType', soundType.value)
        emit('update:soundVolume', soundVolume.value)
        emit('update:theme', theme.value)
        emit('update:navPosition', navPosition.value)
        emit('update:config', llmConfig.value)
        emit('userChanged')
        alert('配置已成功从 JSON 文件导入并保存！')
      }
    } catch (err) {
      alert('导入失败：不是有效的 JSON 文件格式')
    }
  }
  reader.readAsText(file)
  target.value = ''
}

async function resetAllSettings() {
  const confirmed = await showConfirm({
    title: '重置所有设置',
    message: '确定要将当前用户的偏好、提醒音效与系统参数重置为默认 JSON 配置吗？',
    detail: '重置后音量将恢复为 80%，提醒音效恢复为清脆金铃。',
    confirmText: '确认重置',
    cancelText: '取消',
    type: 'warning'
  })

  if (!confirmed) return

  saveUserConfig(userId.value, JSON.parse(JSON.stringify(DEFAULT_USER_CONFIG)))
  syncFromConfig()
  saveAudioSettings()
  saveThemeSettings()
  saveNavPositionSettings()
}
</script>

<style scoped>
.settings-container {
  display: flex;
  width: 100%;
  height: 100%;
  padding: 0;
  margin: 0;
  overflow: hidden;
  box-sizing: border-box;
  background-color: var(--bg-app);
}

.settings-layout {
  display: flex;
  flex-direction: row;
  width: 100%;
  height: 100%;
  max-width: 100%;
  background: transparent;
  border: none;
  border-radius: 0;
  box-shadow: none;
  overflow: hidden;
  min-height: 0;
  flex: 1;
}

/* Left Sidebar Navigation (VS Code Settings Full-Screen Style) */
.settings-sidebar {
  width: 240px;
  min-width: 240px;
  max-width: 240px;
  background-color: var(--bg-surface);
  border-right: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  padding: 20px 12px;
  box-sizing: border-box;
  flex-shrink: 0;
}

.settings-sidebar-header {
  padding: 4px 8px 14px 8px;
  border-bottom: 1px solid var(--border-color);
  margin-bottom: 10px;
}

.sidebar-title {
  font-size: 16px;
  font-weight: 700;
  color: var(--primary);
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0;
}

.settings-nav-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
  flex: 1;
  overflow-y: auto;
}

.settings-nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  background: transparent;
  border: 1px solid transparent;
  border-left: 3px solid transparent;
  border-radius: 8px;
  color: var(--text-muted);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.18s ease;
  text-align: left;
  width: 100%;
  box-sizing: border-box;
}

.settings-nav-item .nav-text {
  flex: 1;
}

.settings-nav-item .nav-badge {
  font-size: 11px;
  background-color: var(--bg-app);
  color: var(--text-muted);
  padding: 1px 6px;
  border-radius: 10px;
  font-weight: 600;
}

.settings-nav-item:hover {
  background-color: var(--bg-hover);
  color: var(--text-main);
}

.settings-nav-item.active {
  background-color: var(--bg-hover);
  color: var(--primary);
  border-left-color: var(--primary);
  font-weight: 600;
}

.settings-nav-item.active .nav-badge {
  background-color: var(--primary);
  color: #fff;
}

/* Right Content Area */
.settings-content {
  flex: 1;
  min-width: 0;
  min-height: 0;
  padding: 32px 48px;
  overflow-y: auto;
  box-sizing: border-box;
  background-color: var(--bg-app);
}

@media (max-width: 768px) {
  .settings-container {
    padding: 8px;
  }

  .settings-layout {
    flex-direction: column;
    height: 100%;
  }

  .settings-sidebar {
    width: 100%;
    min-width: 100%;
    max-width: 100%;
    border-right: none;
    border-bottom: 1px solid var(--border-color);
    padding: 10px;
  }

  .settings-nav-list {
    flex-direction: row;
    overflow-x: auto;
  }

  .settings-nav-item {
    border-left: 1px solid transparent;
    border-bottom: 3px solid transparent;
    padding: 6px 10px;
  }

  .settings-nav-item.active {
    border-left-color: transparent;
    border-bottom-color: var(--primary);
  }

  .settings-content {
    padding: 16px;
  }
}

.tab-pane {
  display: flex;
  flex-direction: column;
  gap: 20px;
  max-width: 960px;
  width: 100%;
  animation: tabFadeIn 0.2s ease-in-out;
}

@keyframes tabFadeIn {
  from {
    opacity: 0;
    transform: translateY(4px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.settings-section {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding-top: 16px;
  border-top: 1px solid var(--border-color);
}

.section-title {
  font-size: 14px;
  font-weight: 700;
  color: var(--text-main);
  display: flex;
  align-items: center;
  gap: 6px;
  margin: 0;
}

.settings-sub-tabs {
  display: flex;
  gap: 8px;
  border-bottom: 1px solid var(--border-color);
  padding-bottom: 10px;
}

.sub-tab-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: 6px;
  border: 1px solid var(--border-color);
  background-color: var(--bg-app);
  color: var(--text-main);
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.sub-tab-btn.active {
  background-color: var(--primary);
  color: #fff;
  border-color: var(--primary);
}

.ai-settings-sub-content {
  padding-top: 8px;
}

.setting-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  padding: 8px 0;
}

.item-label {
  display: flex;
  flex-direction: column;
}

.item-label span {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-main);
}

.item-label small {
  font-size: 11px;
  color: var(--text-muted);
}

.item-control {
  display: flex;
  align-items: center;
  gap: 10px;
}

.select-input, .text-input {
  padding: 6px 10px;
  border-radius: 6px;
  border: 1px solid var(--border-color);
  background-color: var(--bg-app);
  color: var(--text-main);
  font-size: 12px;
  width: 220px;
}

.volume-slider {
  width: 180px;
  accent-color: var(--primary);
}

.admin-tag {
  font-size: 11px;
  background-color: rgba(59, 130, 246, 0.12);
  color: #3b82f6;
  padding: 2px 6px;
  border-radius: 4px;
  margin-left: 6px;
}

.btn-admin-manage {
  background-color: rgba(59, 130, 246, 0.1);
  border: 1px solid rgba(59, 130, 246, 0.3);
  border-radius: 6px;
  padding: 6px 12px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 4px;
  color: #3b82f6;
  white-space: nowrap;
}

.btn-admin-manage:hover {
  background-color: rgba(59, 130, 246, 0.2);
}

.btn-listen {
  background-color: var(--bg-app);
  border: 1px solid var(--border-color);
  border-radius: 6px;
  padding: 6px 12px;
  font-size: 12px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 4px;
  color: var(--primary);
  white-space: nowrap;
}

.btn-reset-danger {
  background-color: rgba(239, 68, 68, 0.08);
  border: 1px solid rgba(239, 68, 68, 0.3);
  border-radius: 6px;
  padding: 6px 14px;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  color: #EF4444;
  transition: all 0.2s ease;
}

.btn-reset-danger:hover {
  background-color: rgba(239, 68, 68, 0.18);
  border-color: #EF4444;
}

.save-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 10px;
}
</style>

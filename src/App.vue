<template>
  <div
    class="app-layout"
    :class="[navPosition === 'left' ? 'layout-nav-left' : 'layout-nav-top']"
    :data-theme="theme"
  >
    <!-- 1. Header Bar with Navigation Tabs -->
    <header class="header">
      <div class="header-left">
        <!-- Mobile Navigation Toggle Button (< 640px) -->
        <button
          class="mobile-nav-toggle-btn"
          @click="toggleMobileNavMenu"
          :title="showMobileNavMenu ? '关闭导航菜单' : '展开导航菜单'"
        >
          <X v-if="showMobileNavMenu" :size="18" />
          <Menu v-else :size="18" />
        </button>

        <h1 class="app-title"><ListTodo :size="20" /> Todo Agent</h1>
      </div>

      <!-- Center Navbar Navigation Tabs (Desktop & Tablet) -->
      <nav class="navbar-tabs">
        <button
          class="nav-tab-btn"
          :class="{ active: currentTab === 'todos' }"
          @click="currentTab = 'todos'"
          title="待办事项"
          data-tooltip="待办事项"
        >
          <CheckSquare :size="15" /> <span>待办事项</span>
        </button>

        <button
          class="nav-tab-btn"
          :class="{ active: currentTab === 'calendar' }"
          @click="currentTab = 'calendar'"
          title="任务日历"
          data-tooltip="任务日历"
        >
          <Calendar :size="15" /> <span>任务日历</span>
        </button>

        <button
          class="nav-tab-btn"
          :class="{ active: currentTab === 'local-clock' }"
          @click="currentTab = 'local-clock'"
          title="本地时钟"
          data-tooltip="本地时钟"
        >
          <Clock :size="15" /> <span>本地时钟</span>
        </button>

        <button
          class="nav-tab-btn"
          :class="{ active: currentTab === 'countdown' }"
          @click="currentTab = 'countdown'"
          title="倒计时"
          data-tooltip="倒计时"
        >
          <Hourglass :size="15" /> <span>倒计时</span>
        </button>

        <button
          class="nav-tab-btn"
          :class="{ active: currentTab === 'alarm' }"
          @click="currentTab = 'alarm'"
          title="闹钟"
          data-tooltip="闹钟"
        >
          <Bell :size="15" /> <span>闹钟</span>
        </button>

        <button
          class="nav-tab-btn"
          :class="{ active: currentTab === 'pomodoro' }"
          @click="currentTab = 'pomodoro'"
          title="番茄时钟"
          data-tooltip="番茄时钟"
        >
          <Flame :size="15" /> <span>番茄时钟</span>
        </button>

        <button
          class="nav-tab-btn"
          :class="{ active: currentTab === 'settings' }"
          @click="currentTab = 'settings'"
          title="系统设置"
          data-tooltip="系统设置"
        >
          <Settings :size="15" /> <span>系统设置</span>
        </button>
      </nav>

      <!-- Mobile Dropdown Navigation Menu (< 640px) -->
      <div v-if="showMobileNavMenu" class="mobile-dropdown-menu animate-fade-in" @click.stop>
        <div class="mobile-nav-links">
          <button
            class="mobile-nav-item"
            :class="{ active: currentTab === 'todos' }"
            @click="selectMobileTab('todos')"
          >
            <CheckSquare :size="16" /> <span>待办事项</span>
          </button>
          <button
            class="mobile-nav-item"
            :class="{ active: currentTab === 'calendar' }"
            @click="selectMobileTab('calendar')"
          >
            <Calendar :size="16" /> <span>任务日历</span>
          </button>
          <button
            class="mobile-nav-item"
            :class="{ active: currentTab === 'local-clock' }"
            @click="selectMobileTab('local-clock')"
          >
            <Clock :size="16" /> <span>本地时钟</span>
          </button>
          <button
            class="mobile-nav-item"
            :class="{ active: currentTab === 'countdown' }"
            @click="selectMobileTab('countdown')"
          >
            <Hourglass :size="16" /> <span>倒计时</span>
          </button>
          <button
            class="mobile-nav-item"
            :class="{ active: currentTab === 'alarm' }"
            @click="selectMobileTab('alarm')"
          >
            <Bell :size="16" /> <span>闹钟</span>
          </button>
          <button
            class="mobile-nav-item"
            :class="{ active: currentTab === 'pomodoro' }"
            @click="selectMobileTab('pomodoro')"
          >
            <Flame :size="16" /> <span>番茄时钟</span>
          </button>
          <button
            class="mobile-nav-item"
            :class="{ active: currentTab === 'settings' }"
            @click="selectMobileTab('settings')"
          >
            <Settings :size="16" /> <span>系统设置</span>
          </button>
        </div>
      </div>
    </header>


    <!-- 2. Main Content Area -->
    <main class="main-content">
      <!-- Tab 1: Todos List View -->
      <template v-if="currentTab === 'todos'">
        <!-- Filter & Search Toolbar -->
        <div class="toolbar">
          <div class="filter-group">
            <span class="label-sm">筛选:</span>
            <button
              class="filter-btn"
              :class="{ active: currentFilter === 'all' }"
              @click="setFilter('all')"
            >
              全部
            </button>
            <button
              class="filter-btn"
              :class="{ active: currentFilter === 'pending' }"
              @click="setFilter('pending')"
            >
              未完成
            </button>
            <button
              class="filter-btn"
              :class="{ active: currentFilter === 'completed' }"
              @click="setFilter('completed')"
            >
              已完成
            </button>
          </div>

          <div class="toolbar-right">
            <div class="search-box">
              <Search :size="14" class="search-icon" />
              <input
                type="text"
                v-model="searchKeyword"
                placeholder="搜索待办事项..."
                @input="loadTodos"
              />
            </div>

            <button class="btn btn-primary" @click="openAddModal">
              <Plus :size="14" /> 新建任务
            </button>
          </div>
        </div>

        <!-- Todo List Grid / Card View -->
        <div class="todo-scroll-area">
          <div v-if="loading" class="empty-state">
            <div class="spinner"></div>
            <p>加载中...</p>
          </div>

          <div v-else-if="todos.length === 0" class="empty-state">
            <div class="empty-icon"><Inbox :size="42" :stroke-width="1.5" /></div>
            <p class="empty-text">暂无待办事项，点击右上角 "+ 新建任务" 或使用快捷创建吧！</p>
          </div>

          <div v-else class="todo-grid">
            <div
              v-for="todo in todos"
              :key="todo.id"
              class="todo-card animate-fade-in"
              :class="{ completed: todo.completed }"
            >
              <div class="card-left">
                <input
                  type="checkbox"
                  class="todo-checkbox"
                  :checked="todo.completed"
                  @change="toggleStatus(todo)"
                />
              </div>

              <div class="card-body">
                <div class="card-title" :class="{ strike: todo.completed }">
                  {{ todo.title }}
                </div>
                <div class="card-meta">
                  <span class="tag tag-category"><Folder :size="11" /> {{ todo.category }}</span>
                  <span class="tag" :class="'tag-prio-' + todo.priority">
                    {{ priorityLabel(todo.priority) }}
                  </span>
                  <span v-if="todo.remind_at" class="tag tag-reminder">
                    <Clock :size="11" /> {{ todo.remind_at }}
                  </span>
                </div>
              </div>

              <div class="card-actions">
                <button class="icon-btn edit-btn" @click="openEditModal(todo)" title="编辑任务">
                  <Edit3 :size="14" />
                </button>
                <button class="icon-btn delete-btn" @click="deleteTodo(todo.id)" title="删除任务">
                  <Trash2 :size="14" />
                </button>
              </div>
            </div>
          </div>
        </div>
      </template>

      <!-- Tab 2: Calendar View -->
      <template v-else-if="currentTab === 'calendar'">
        <CalendarView
          :todos="todos"
          @delete-todo="deleteTodo"
        />
      </template>

      <!-- Tab 4: Local Clock View -->
      <template v-else-if="currentTab === 'local-clock'">
        <LocalClockPage />
      </template>

      <!-- Tab 5: Countdown Timer View -->
      <template v-else-if="currentTab === 'countdown'">
        <AlarmCountdown />
      </template>

      <!-- Tab 6: Alarm View -->
      <template v-else-if="currentTab === 'alarm'">
        <AlarmCountdown mode="alarm" />
      </template>

      <!-- Tab 7: Pomodoro Timer View -->
      <template v-else-if="currentTab === 'pomodoro'">
        <PomodoroTimer />
      </template>

      <!-- Tab 8: Settings View -->
      <template v-else-if="currentTab === 'settings'">
        <SettingsPage
          v-model:theme="theme"
          v-model:config="llmConfig"
          @update:navPosition="val => navPosition = val"
          @logout="handleLogout"
          @userChanged="loadTodos"
        />
      </template>
    </main>







    <!-- Modals -->
    <!-- Add / Edit Modal -->
    <div v-if="showAddEditModal" class="modal-backdrop" @click.self="showAddEditModal = false">
      <div class="modal-card animate-fade-in">
        <h2 class="modal-title">
          <Edit3 v-if="editingTodo" :size="18" />
          <Plus v-else :size="18" />
          <span>{{ editingTodo ? '编辑待办事项' : '添加新待办事项' }}</span>
        </h2>

        <div class="form-group">
          <label>任务标题 *</label>
          <input type="text" v-model="todoForm.title" placeholder="请输入任务标题..." />
        </div>

        <div class="form-row">
          <div class="form-group flex-1">
            <label>任务分类</label>
            <input type="text" v-model="todoForm.category" placeholder="如: 工作 / 生活 / 学习" />
          </div>

          <div class="form-group flex-1">
            <label>优先级</label>
            <select v-model="todoForm.priority">
              <option value="high">高优 (high)</option>
              <option value="medium">中优 (medium)</option>
              <option value="low">低优 (low)</option>
            </select>
          </div>
        </div>

        <div class="form-group">
          <label class="checkbox-label">
            <input type="checkbox" v-model="todoForm.enableReminder" />
            设置定时提醒时间
          </label>
          <input
            v-if="todoForm.enableReminder"
            type="datetime-local"
            v-model="todoForm.remindAt"
            class="datetime-picker"
          />
        </div>

        <div class="modal-actions">
          <button class="btn" @click="showAddEditModal = false">取消</button>
          <button class="btn btn-primary" @click="saveTodoForm">保存</button>
        </div>
      </div>
    </div>

    <!-- Model Config Modal -->
    <div v-if="showModelModal" class="modal-backdrop" @click.self="showModelModal = false">
      <div class="modal-card animate-fade-in">
        <h2 class="modal-title"><Settings :size="18" /> <span>配置大语言模型 (LLM)</span></h2>

        <div class="form-group">
          <label>服务提供商 (Provider) *</label>
          <select v-model="llmConfig.provider" @change="onProviderChange">
            <option value="siliconflow">SiliconFlow (硅基流动云端 API)</option>
            <option value="ollama">Native Ollama (本地大模型)</option>
          </select>
        </div>

        <div class="form-group">
          <label>接口地址 (Base URL)</label>
          <input type="text" v-model="llmConfig.base_url" placeholder="http/https 接口地址" />
        </div>

        <div class="form-group">
          <label>API Key (密钥)</label>
          <input
            type="password"
            v-model="llmConfig.api_key"
            placeholder="sk-..."
            :disabled="llmConfig.provider === 'ollama'"
          />
        </div>

        <div class="form-group">
          <label>模型名称 (Model Name) *</label>
          <input type="text" v-model="llmConfig.model" placeholder="例如: deepseek-ai/DeepSeek-V4-Flash" />
        </div>

        <div class="form-group">
          <label class="checkbox-label">
            <input type="checkbox" v-model="llmConfig.enable_thinking" />
            启用深度思考与推理过程 (Think Mode)
          </label>
        </div>

        <div class="modal-actions">
          <button class="btn" @click="showModelModal = false">取消</button>
          <button class="btn btn-primary" @click="saveLlmConfig">保存配置</button>
        </div>
      </div>
    </div>

    <!-- Login / Registration / Local Mode Modal -->
    <LoginPage
      v-if="showAuthModal"
      @login-success="onLoginSuccess"
      @use-local-mode="onUseLocalMode"
      @close="showAuthModal = false"
    />
  </div>
</template>


<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue'
import {
  CheckSquare, Calendar, Clock, Flame, Settings, Menu, X, Hourglass, Bell,
  Plus, Edit3, Trash2, Folder, Search, ListTodo, Inbox
} from 'lucide-vue-next'
import type { Todo, LlmConfig, FilterType, ThemeType, NavPosition, User } from './types'
import { showConfirm } from './utils/confirmState'
import { getLlmConfig, saveLlmConfig as persistLlmConfig, getTheme, saveTheme, getNavPosition, saveNavPosition } from './utils/aiStorage'
import { getUserConfig, getCurrentUserId } from './utils/configManager'
import LocalClockPage from './components/productivity/LocalClockPage.vue'
import CalendarView from './components/productivity/CalendarView.vue'
import PomodoroTimer from './components/productivity/PomodoroTimer.vue'
import AlarmCountdown from './components/productivity/AlarmCountdown.vue'
import SettingsPage from './components/common/SettingsPage.vue'
import LoginPage from './components/common/LoginPage.vue'

// User Auth & Local Mode State
const currentUser = ref<User | null>(
  localStorage.getItem('todo_current_user')
    ? JSON.parse(localStorage.getItem('todo_current_user')!)
    : null
)
const showAuthModal = ref(false)

// User Dropdown Menu State & Event Listeners
const showUserMenu = ref(false)

// Mobile Navigation Dropdown Menu State (< 640px)
const showMobileNavMenu = ref(false)

function toggleUserMenu(e: Event) {
  e.stopPropagation()
  showUserMenu.value = !showUserMenu.value
  showMobileNavMenu.value = false
}
void toggleUserMenu

function closeUserMenu() {
  showUserMenu.value = false
  showMobileNavMenu.value = false
}

function toggleMobileNavMenu(e: Event) {
  e.stopPropagation()
  showMobileNavMenu.value = !showMobileNavMenu.value
  showUserMenu.value = false
}

function selectMobileTab(tab: 'todos' | 'calendar' | 'local-clock' | 'countdown' | 'alarm' | 'pomodoro' | 'settings') {
  currentTab.value = tab
  showMobileNavMenu.value = false
}

onMounted(() => {
  window.addEventListener('click', closeUserMenu)
})

onUnmounted(() => {
  window.removeEventListener('click', closeUserMenu)
})

function onLoginSuccess(user: User) {
  currentUser.value = user
  localStorage.setItem('todo_current_user', JSON.stringify(user))
  localStorage.removeItem('todo_guest_mode')
  showAuthModal.value = false
  statusMessage.value = `🔑 已登录为 [${user.username}] (ID: ${user.id})`
  loadTodos()
}

function onUseLocalMode() {
  currentUser.value = null
  localStorage.removeItem('todo_current_user')
  localStorage.setItem('todo_guest_mode', 'true')
  showAuthModal.value = false
  statusMessage.value = `🏠 已切换为【游客模式】（离线本地可用）`
  loadTodos()
}

function handleLogout() {
  currentUser.value = null
  localStorage.removeItem('todo_current_user')
  localStorage.removeItem('todo_guest_mode')
  showAuthModal.value = true
  statusMessage.value = `↩️ 已退出登录`
  loadTodos()
}

// Navigation Tab State
type TabType = 'todos' | 'calendar' | 'local-clock' | 'countdown' | 'alarm' | 'pomodoro' | 'settings'
const currentTab = ref<TabType>('todos')

// Theme State
const storedTheme = getTheme() as ThemeType | null
const theme = ref<ThemeType>(storedTheme || 'light')
watch(theme, (newVal) => {
  saveTheme(newVal)
  document.documentElement.setAttribute('data-theme', newVal)
}, { immediate: true })

// Navigation Position State (top | left)
const userInitialConfig = getUserConfig(getCurrentUserId())
const storedNavPos = getNavPosition() as NavPosition | null
const navPosition = ref<NavPosition>(storedNavPos || userInitialConfig.navPosition || 'top')
watch(navPosition, (newVal) => {
  saveNavPosition(newVal)
})

// LLM Config State
const storedLlmConfig = getLlmConfig()
const llmConfig = ref<LlmConfig>(storedLlmConfig || {
  provider: 'siliconflow',
  base_url: 'https://api.siliconflow.cn/v1',
  api_key: '',
  model: 'deepseek-ai/DeepSeek-V4-Flash',
  enable_thinking: false
})

// Todos State
const todos = ref<Todo[]>([])
const loading = ref(false)
const currentFilter = ref<FilterType>('all')
const searchKeyword = ref('')
const statusMessage = ref('就绪 - Rust 后端与 SQLite 数据库连接正常')

// Modals State
const showAddEditModal = ref(false)
const editingTodo = ref<Todo | null>(null)
const todoForm = ref({
  title: '',
  category: '工作',
  priority: 'medium' as 'high' | 'medium' | 'low',
  enableReminder: false,
  remindAt: ''
})

const showModelModal = ref(false)

// Tauri Invoke Helper (with fallback for web browser testing)
async function tauriInvoke<T>(cmd: string, args: Record<string, any> = {}): Promise<T> {
  try {
    const { invoke } = await import('@tauri-apps/api/core')
    return await invoke<T>(cmd, args)
  } catch (e) {
    console.warn(`[Tauri Web Fallback] ${cmd}`, args, e)
    // Web fallback mock implementation with user_id isolation
    const storageKey = `web_todos_${args.user_id || 0}`
    if (cmd === 'get_todos') {
      if (!localStorage.getItem(storageKey)) {
        const defaultData: Todo[] = [
          { id: 1, title: '完成项目整体架构设计', category: '工作', priority: 'high', completed: true, created_at: new Date().toISOString(), updated_at: new Date().toISOString(), user_id: args.user_id || 0 },
          { id: 2, title: '完成 Tauri Rust SQLite 数据库集成', category: '工作', priority: 'high', completed: true, created_at: new Date().toISOString(), updated_at: new Date().toISOString(), user_id: args.user_id || 0 },
          { id: 3, title: '集成大语言模型配置与语义解析', category: 'AI', priority: 'medium', completed: false, created_at: new Date().toISOString(), updated_at: new Date().toISOString(), user_id: args.user_id || 0 }
        ]
        localStorage.setItem(storageKey, JSON.stringify(defaultData))
      }
      const stored = JSON.parse(localStorage.getItem(storageKey) || '[]') as Todo[]
      return stored as T
    }
    if (cmd === 'add_todo') {
      const stored = JSON.parse(localStorage.getItem(storageKey) || '[]') as Todo[]
      const newId = Date.now()
      stored.push({
        id: newId,
        title: args.title,
        priority: args.priority,
        category: args.category,
        completed: false,
        remind_at: args.remind_at,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        user_id: args.user_id || 0
      })
      localStorage.setItem(storageKey, JSON.stringify(stored))
      return newId as T
    }
    if (cmd === 'update_todo_status') {
      const stored = JSON.parse(localStorage.getItem(storageKey) || '[]') as Todo[]
      const idx = stored.findIndex(t => t.id === args.id)
      if (idx >= 0) stored[idx].completed = args.completed
      localStorage.setItem(storageKey, JSON.stringify(stored))
      return true as T
    }
    if (cmd === 'update_todo') {
      const stored = JSON.parse(localStorage.getItem(storageKey) || '[]') as Todo[]
      const idx = stored.findIndex(t => t.id === args.id)
      if (idx >= 0) {
        stored[idx].title = args.title
        stored[idx].category = args.category
        stored[idx].priority = args.priority
        stored[idx].remind_at = args.remind_at
        stored[idx].updated_at = new Date().toISOString()
      }
      localStorage.setItem(storageKey, JSON.stringify(stored))
      return true as T
    }
    if (cmd === 'delete_todo') {
      let stored = JSON.parse(localStorage.getItem(storageKey) || '[]') as Todo[]
      stored = stored.filter(t => t.id !== args.id)
      localStorage.setItem(storageKey, JSON.stringify(stored))
      return true as T
    }
    if (cmd === 'execute_ai_command') {
      const input = (args.input || '') as string
      const config = (args.config || {}) as LlmConfig
      const userId = args.user_id || 0

      // 1. 如果配置了 API Key，在 Web Fallback 下直接请求大模型 API
      if (config.api_key && config.provider === 'siliconflow') {
        try {
          const resp = await fetch(`${config.base_url}/chat/completions`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${config.api_key}`
            },
            body: JSON.stringify({
              model: config.model || 'deepseek-ai/DeepSeek-V4-Flash',
              messages: [
                { role: 'system', content: '你是一个高效智能的 Todo 待办事项助手。' },
                { role: 'user', content: input }
              ]
            })
          })
          const json = await resp.json()
          if (json.choices && json.choices.length > 0) {
            const aiText = json.choices[0].message.content
            return {
              action: 'chat',
              message: aiText,
              should_refresh: false,
              data: null
            } as T
          }
        } catch (apiErr) {
          console.warn('Web API Fetch Failed, fallback to mock parser:', apiErr)
        }
      }

      // 2. 离线模式 / 未填 Key 时的智能待办指令解析
      let stored = JSON.parse(localStorage.getItem(storageKey) || '[]') as Todo[]

      if (input.includes('新建') || input.includes('创建') || input.includes('添加') || input.includes('提醒我') || input.includes('安排')) {
        let title = input.replace(/(帮我|请|提醒我|新建|创建|添加|安排|待办|任务)/g, '').trim()
        if (!title) title = '新智能待办任务'
        const newTodo: Todo = {
          id: Date.now(),
          title: title,
          category: input.includes('工作') ? '工作' : input.includes('学习') ? '学习' : '生活',
          priority: input.includes('高') || input.includes('紧急') ? 'high' : 'medium',
          completed: false,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
          user_id: userId
        }
        stored.push(newTodo)
        localStorage.setItem(storageKey, JSON.stringify(stored))
        return {
          action: 'add',
          message: `已自动为您创建待办任务：【${title}】`,
          should_refresh: true,
          data: newTodo
        } as T
      } else if (input.includes('完成') || input.includes('做完') || input.includes('标记')) {
        if (stored.length > 0) {
          stored[0].completed = true
          localStorage.setItem(storageKey, JSON.stringify(stored))
          return {
            action: 'complete',
            message: `已为您标记任务【${stored[0].title}】为已完成！`,
            should_refresh: true,
            data: stored[0]
          } as T
        }
      } else if (input.includes('删除') || input.includes('清理')) {
        if (stored.length > 0) {
          const deleted = stored.shift()
          localStorage.setItem(storageKey, JSON.stringify(stored))
          return {
            action: 'delete',
            message: `已为您删除任务【${deleted?.title || ''}】`,
            should_refresh: true,
            data: null
          } as T
        }
      }

      return {
        action: 'chat',
        message: `收到！我是您的 AI 待办助手。您刚才说："${input}"。我可以帮助您创建、完成或整理待办事项！在“系统设置”或 AI 聊天页配置您的 LLM API Key，即可开启完全通用的智能深度对话！`,
        should_refresh: false,
        data: null
      } as T
    }
    throw e
  }
}

// Priority Helpers
function priorityLabel(prio: string) {
  if (prio === 'high') return '🔴 高优'
  if (prio === 'low') return '🔵 低优'
  return '🟡 中优'
}

// Load Todos
async function loadTodos() {
  loading.value = true
  try {
    const uid = currentUser.value ? currentUser.value.id : 0
    const result = await tauriInvoke<Todo[]>('get_todos', {
      filter: currentFilter.value,
      search: searchKeyword.value,
      user_id: uid
    })
    todos.value = result || []
    statusMessage.value = `${currentUser.value ? `👤 [${currentUser.value.username}]` : '🏠 [本地模式]'} 共加载 ${todos.value.length} 项待办任务`
  } catch (err: any) {
    statusMessage.value = `❌ 加载失败: ${err?.message || err}`
  } finally {
    loading.value = false
  }
}

function setFilter(filter: FilterType) {
  currentFilter.value = filter
  loadTodos()
}

// Toggle Status
async function toggleStatus(todo: Todo) {
  const newStatus = !todo.completed
  try {
    const uid = currentUser.value ? currentUser.value.id : 0
    await tauriInvoke('update_todo_status', { id: todo.id, completed: newStatus, user_id: uid })
    todo.completed = newStatus
    statusMessage.value = newStatus ? `✅ 标记任务 [${todo.title}] 已完成` : `↩️ 恢复任务 [${todo.title}] 为未完成`
  } catch (err: any) {
    statusMessage.value = `❌ 更新状态失败: ${err}`
  }
}

// Add/Edit Form Actions
function openAddModal() {
  editingTodo.value = null
  todoForm.value = {
    title: '',
    category: '工作',
    priority: 'medium',
    enableReminder: false,
    remindAt: ''
  }
  showAddEditModal.value = true
}

function openEditModal(todo: Todo) {
  editingTodo.value = todo
  todoForm.value = {
    title: todo.title,
    category: todo.category,
    priority: todo.priority,
    enableReminder: !!todo.remind_at,
    remindAt: todo.remind_at || ''
  }
  showAddEditModal.value = true
}

async function saveTodoForm() {
  if (!todoForm.value.title.trim()) {
    alert('任务标题不能为空！')
    return
  }

  const remindStr = todoForm.value.enableReminder && todoForm.value.remindAt ? todoForm.value.remindAt.replace('T', ' ') + ':00' : null
  const uid = currentUser.value ? currentUser.value.id : 0

  try {
    if (editingTodo.value) {
      await tauriInvoke('update_todo', {
        id: editingTodo.value.id,
        title: todoForm.value.title.trim(),
        category: todoForm.value.category.trim(),
        priority: todoForm.value.priority,
        remind_at: remindStr,
        user_id: uid
      })
      statusMessage.value = `✅ 待办事项 [${todoForm.value.title}] 更新成功`
    } else {
      await tauriInvoke('add_todo', {
        title: todoForm.value.title.trim(),
        category: todoForm.value.category.trim(),
        priority: todoForm.value.priority,
        remind_at: remindStr,
        user_id: uid
      })
      statusMessage.value = `✨ 成功创建待办事项 [${todoForm.value.title}]`
    }
    showAddEditModal.value = false
    loadTodos()
  } catch (err: any) {
    statusMessage.value = `❌ 保存失败: ${err}`
  }
}

// Delete Todo
async function deleteTodo(id: number, skipConfirm = false) {
  if (!skipConfirm) {
    const confirmed = await showConfirm({
      title: '彻底删除任务',
      message: '确定要彻底删除该待办事项吗？删除后不可恢复。',
      type: 'danger'
    })
    if (!confirmed) return
  }
  try {
    const uid = currentUser.value ? currentUser.value.id : 0
    await tauriInvoke('delete_todo', { id, user_id: uid })
    statusMessage.value = `🗑️ 任务已成功删除`
    loadTodos()
  } catch (err: any) {
    statusMessage.value = `❌ 删除失败: ${err}`
  }
}

// Provider Change
function onProviderChange() {
  if (llmConfig.value.provider === 'siliconflow') {
    llmConfig.value.base_url = 'https://api.siliconflow.cn/v1'
  } else {
    llmConfig.value.base_url = 'http://localhost:11434'
  }
}

function saveLlmConfig() {
  persistLlmConfig(llmConfig.value)
  showModelModal.value = false
  statusMessage.value = `⚙️ LLM 配置已更新 [Provider: ${llmConfig.value.provider}, Model: ${llmConfig.value.model}]`
}

onMounted(() => {
  document.documentElement.setAttribute('data-theme', theme.value)
  loadTodos()
  
  // 启动软件后，若未登录且未记住游客模式，自动弹出 3D 登录/注册卡片
  const isGuest = localStorage.getItem('todo_guest_mode') === 'true'
  if (!currentUser.value && !isGuest) {
    showAuthModal.value = true
  }
})
</script>

<style scoped>
.app-layout {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background-color: var(--bg-app);
}

/* VS Code style Left Navigation Sidebar */
.layout-nav-left {
  flex-direction: row;
  height: 100vh;
  overflow: hidden;
}

.layout-nav-left .header {
  width: 200px;
  min-width: 200px;
  max-width: 200px;
  height: 100vh;
  flex-direction: column;
  justify-content: flex-start;
  align-items: stretch;
  padding: 16px 12px;
  border-bottom: none;
  border-right: 1px solid var(--border-color);
  box-sizing: border-box;
  flex-shrink: 0;
  gap: 16px;
  background-color: var(--bg-surface);
}

.layout-nav-left .header-left {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 8px;
  padding: 0 4px 12px 4px;
  border-bottom: 1px solid var(--border-color);
  width: 100%;
}

.layout-nav-left .app-title {
  font-size: 16px;
  font-weight: 700;
  color: var(--primary);
  margin: 0;
}

.layout-nav-left .navbar-tabs {
  display: flex;
  flex-direction: column;
  align-items: stretch;
  gap: 4px;
  background: transparent;
  border: none;
  padding: 0;
  width: 100%;
  flex: 1;
  overflow-y: auto;
}

.layout-nav-left .nav-tab-btn {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 10px;
  padding: 9px 12px;
  border-radius: 6px;
  width: 100%;
  font-size: 13px;
  font-weight: 500;
  text-align: left;
  border: 1px solid transparent;
  color: var(--text-muted);
  box-sizing: border-box;
  transition: all 0.18s ease;
}

.layout-nav-left .nav-tab-btn span {
  display: inline-block !important;
}

.layout-nav-left .nav-tab-btn:hover {
  background-color: var(--bg-hover);
  color: var(--text-main);
}

.layout-nav-left .nav-tab-btn.active {
  background-color: var(--bg-hover);
  color: var(--primary);
  border-left: 3px solid var(--primary);
  border-radius: 4px;
  font-weight: 600;
  box-shadow: none;
}

.layout-nav-left .main-content {
  flex: 1;
  height: 100vh;
  min-height: 0;
  overflow-y: auto;
}

@media (max-width: 640px) {
  .layout-nav-left {
    flex-direction: column;
  }

  .layout-nav-left .header {
    width: 100%;
    min-width: 100%;
    max-width: 100%;
    height: auto;
    flex-direction: row;
    align-items: center;
    justify-content: space-between;
    padding: 12px 16px;
    border-right: none;
    border-bottom: 1px solid var(--border-color);
  }

  .layout-nav-left .header-left {
    flex-direction: row;
    align-items: center;
    border-bottom: none;
    padding-bottom: 0;
    width: auto;
  }

  .layout-nav-left .navbar-tabs {
    display: none;
  }
}

.header {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 20px;
  background-color: var(--bg-surface);
  border-bottom: 1px solid var(--border-color);
  gap: 12px;
  flex-wrap: nowrap;
  z-index: 100;
}

.mobile-nav-toggle-btn {
  display: none;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 8px;
  border: 1px solid var(--border-color);
  background: var(--bg-app);
  color: var(--text-main);
  cursor: pointer;
  transition: all 0.2s ease;
}

.mobile-nav-toggle-btn:hover {
  background: var(--bg-hover);
  border-color: var(--primary);
  color: var(--primary);
}

.navbar-tabs {
  display: flex;
  align-items: center;
  gap: 4px;
  background-color: var(--bg-app);
  padding: 4px;
  border-radius: 10px;
  border: 1px solid var(--border-color);
  flex-shrink: 1;
}

.nav-tab-btn {
  position: relative;
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  border-radius: 8px;
  border: none;
  background: transparent;
  color: var(--text-muted);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.2s ease;
  flex-shrink: 0;
}

.nav-tab-btn:hover {
  color: var(--text-main);
  background-color: var(--bg-hover);
}

.nav-tab-btn.active {
  color: var(--primary);
  background-color: var(--bg-surface);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

/* Mobile Dropdown Navigation Styles (< 640px) */
.mobile-dropdown-menu {
  position: absolute;
  top: calc(100% + 1px);
  left: 0;
  right: 0;
  background-color: var(--bg-surface);
  border-bottom: 1px solid var(--border-color);
  box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.15);
  padding: 12px 16px;
  z-index: 999;
  display: flex;
  flex-direction: column;
  gap: 12px;
  backdrop-filter: blur(12px);
}

.mobile-nav-links {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px;
}

.mobile-nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  border-radius: 8px;
  border: 1px solid var(--border-color);
  background-color: var(--bg-app);
  color: var(--text-muted);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.mobile-nav-item:hover {
  background-color: var(--bg-hover);
  color: var(--text-main);
  border-color: var(--primary);
}

.mobile-nav-item.active {
  background-color: var(--primary);
  color: #ffffff;
  border-color: var(--primary);
  font-weight: 600;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

.mobile-nav-divider {
  height: 1px;
  background-color: var(--border-color);
  margin: 2px 0;
}

.mobile-user-section {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.mobile-user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  font-weight: 600;
  color: var(--text-main);
}

.mobile-action-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  border-radius: 8px;
  border: none;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.mobile-action-btn.primary {
  background-color: var(--primary);
  color: #ffffff;
}

.mobile-action-btn.danger {
  background-color: rgba(239, 68, 68, 0.1);
  color: #ef4444;
}

.mobile-action-btn.danger:hover {
  background-color: #ef4444;
  color: #ffffff;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
  white-space: nowrap;
}

.app-title {
  font-size: 18px;
  font-weight: 700;
  color: var(--primary);
  white-space: nowrap;
}

.sub-badge {
  font-size: 11px;
  font-weight: 600;
  background-color: var(--border-color);
  color: var(--text-muted);
  padding: 2px 8px;
  border-radius: 12px;
  white-space: nowrap;
}

.model-badge-btn {
  background-color: var(--bg-app);
  color: var(--ai-purple);
  border: 1px solid var(--border-color);
  border-radius: 16px;
  padding: 4px 12px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.2s;
}

.model-badge-btn:hover {
  border-color: var(--ai-purple);
  transform: translateY(-1px);
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
  white-space: nowrap;
}

/* Responsive Header Styles */
@media (max-width: 1024px) {
  .header {
    padding: 10px 14px;
    gap: 8px;
  }

  .sub-badge {
    display: none;
  }

  .nav-tab-btn {
    padding: 5px 10px;
    font-size: 12px;
  }
}

@media (max-width: 860px) {
  .nav-tab-btn span {
    display: none;
  }

  .nav-tab-btn {
    padding: 6px 10px;
  }

  /* Show Hover Tooltip when text is hidden */
  .nav-tab-btn[data-tooltip]:hover::after {
    content: attr(data-tooltip);
    position: absolute;
    top: calc(100% + 8px);
    left: 50%;
    transform: translateX(-50%);
    background-color: var(--text-main);
    color: var(--bg-surface);
    padding: 4px 8px;
    border-radius: 6px;
    font-size: 11px;
    font-weight: 500;
    white-space: nowrap;
    pointer-events: none;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    z-index: 1000;
  }

  .app-title {
    font-size: 16px;
  }
}

@media (max-width: 640px) {
  .mobile-nav-toggle-btn {
    display: flex;
  }

  .navbar-tabs {
    display: none;
  }

  .header-right .user-dropdown-container {
    display: none;
  }

  .ai-assistant-toggle-btn span {
    display: none;
  }

  .app-title {
    font-size: 15px;
  }

  .main-content {
    padding: 12px 10px;
  }

  .toolbar {
    flex-direction: column;
    align-items: stretch;
    gap: 10px;
  }

  .toolbar-right {
    width: 100%;
    justify-content: space-between;
  }

  .search-box {
    flex: 1;
  }

  .search-box input {
    width: 100%;
  }

  .filter-group {
    flex-wrap: wrap;
  }
}

@media (max-width: 480px) {
  .todo-card {
    padding: 10px 12px;
  }

  .card-meta {
    flex-wrap: wrap;
    gap: 4px;
  }
}

.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.toolbar-right {
  display: flex;
  align-items: center;
  gap: 10px;
}

.filter-group {
  display: flex;
  align-items: center;
  gap: 6px;
}

.filter-btn {
  font-size: 12px;
  padding: 5px 12px;
  border-radius: 6px;
  border: 1px solid var(--border-color);
  background-color: var(--bg-surface);
  color: var(--text-main);
  cursor: pointer;
  transition: all 0.2s;
}

.filter-btn.active {
  background-color: var(--primary);
  color: #FFFFFF;
  border-color: var(--primary);
}

.todo-scroll-area {
  flex: 1;
  overflow-y: auto;
  padding-right: 4px;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 240px;
  color: var(--text-muted);
}

.empty-icon {
  font-size: 40px;
  margin-bottom: 8px;
}

.todo-grid {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.todo-card {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  background-color: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-sm);
  transition: all 0.2s ease;
}

.todo-card:hover {
  border-color: var(--border-color-focus);
  background-color: var(--bg-card-hover);

}

.todo-card.completed {
  opacity: 0.7;
}

.card-left {
  margin-right: 14px;
}

.todo-checkbox {
  width: 18px;
  height: 18px;
  cursor: pointer;
  accent-color: var(--primary);
}

.card-body {
  flex: 1;
}

.card-title {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-main);
  margin-bottom: 4px;
}

.card-title.strike {
  text-decoration: line-through;
  color: var(--text-muted);
}

.card-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 11px;
}

.tag {
  padding: 2px 8px;
  border-radius: 4px;
  font-weight: 500;
}

.tag-category {
  background-color: rgba(113, 128, 150, 0.15);
  color: var(--text-muted);
}

.tag-prio-high {
  background-color: rgba(229, 62, 62, 0.15);
  color: #E53E3E;
}

.tag-prio-medium {
  background-color: rgba(221, 107, 32, 0.15);
  color: #DD6B20;
}

.tag-prio-low {
  background-color: rgba(49, 130, 206, 0.15);
  color: #3182CE;
}

.tag-reminder {
  background-color: rgba(128, 90, 213, 0.15);
  color: var(--ai-purple);
}

.card-actions {
  display: flex;
  align-items: center;
  gap: 6px;
}

.icon-btn {
  background: transparent;
  border: none;
  cursor: pointer;
  padding: 4px 6px;
  border-radius: 4px;
  font-size: 14px;
  transition: background-color 0.2s;
}

.icon-btn:hover {
  background-color: var(--border-color);
}

.ai-input-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 20px;
  background-color: var(--bg-surface);
  border-top: 1px solid var(--border-color);
}

.ai-input-bar input {
  flex: 1;
}



/* Modals */
.modal-backdrop {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
  backdrop-filter: blur(4px);
}

.modal-card {
  width: 440px;
  max-width: calc(100vw - 24px);
  box-sizing: border-box;
  background-color: var(--bg-surface);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  padding: 24px;
  box-shadow: var(--shadow-lg);
}

.modal-title {
  font-size: 16px;
  font-weight: 700;
  margin-bottom: 18px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-bottom: 14px;
}

.form-group label {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-muted);
}

.form-row {
  display: flex;
  gap: 12px;
}

.flex-1 {
  flex: 1;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

.modal-actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 20px;
}

/* User Dropdown Menu */
.user-dropdown {
  position: relative;
  display: inline-block;
}

.user-avatar-btn {
  background-color: var(--bg-app);
  border: 1px solid var(--border-color);
  color: var(--text-main);
  border-radius: 16px;
  padding: 5px 12px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.user-avatar-btn:hover {
  border-color: var(--primary);
  color: var(--primary);
}

.dropdown-menu {
  position: absolute;
  top: calc(100% + 6px);
  right: 0;
  background-color: var(--bg-surface);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-lg);
  min-width: 130px;
  display: none;
  flex-direction: column;
  padding: 4px;
  z-index: 1000;
}

.user-dropdown:hover .dropdown-menu {
  display: flex;
}

.dropdown-item {
  padding: 8px 12px;
  font-size: 12px;
  font-weight: 500;
  color: var(--text-main);
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.2s ease;
}

.dropdown-item:hover {
  background-color: var(--bg-card-hover);
  color: var(--primary);
}

.dropdown-item.danger {
  color: #E53E3E;
}

.dropdown-item.danger:hover {
  background-color: rgba(229, 62, 62, 0.1);
}

.main-content {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 20px;
  display: flex;
  flex-direction: column;
  box-sizing: border-box;
}

/* User Auth Badge Styles */
.user-badge {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 10px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
}

.user-dropdown-container {
  position: relative;
}

.user-badge-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  background-color: rgba(59, 130, 246, 0.1);
  border: 1px solid rgba(59, 130, 246, 0.3);
  color: var(--primary, #3b82f6);
  padding: 4px 10px;
  border-radius: 20px;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.user-badge-btn:hover {
  background-color: rgba(59, 130, 246, 0.2);
  border-color: var(--primary, #3b82f6);
}

.chevron-icon {
  transition: transform 0.2s ease;
  color: var(--text-muted, #64748b);
}

.chevron-icon.open {
  transform: rotate(180deg);
}

.user-dropdown-menu {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  width: 170px;
  background-color: var(--bg-card, #ffffff);
  border: 1px solid var(--border-color, #e2e8f0);
  border-radius: 10px;
  box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.12), 0 8px 10px -6px rgba(0, 0, 0, 0.06);
  padding: 6px;
  z-index: 1000;
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.dropdown-header {
  padding: 6px 8px;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.dropdown-user-name {
  font-weight: 700;
  font-size: 13px;
  color: var(--text-main, #0f172a);
}

.dropdown-user-id {
  font-size: 11px;
  color: var(--text-muted, #64748b);
}

.dropdown-divider {
  height: 1px;
  background-color: var(--border-color, #e2e8f0);
  margin: 2px 0;
}

.dropdown-item {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 7px 10px;
  border-radius: 6px;
  border: none;
  background: transparent;
  color: var(--text-main, #334155);
  font-size: 12px;
  cursor: pointer;
  transition: background-color 0.15s ease, color 0.15s ease;
  text-align: left;
}

.dropdown-item:hover {
  background-color: var(--bg-hover, #f1f5f9);
  color: var(--primary, #3b82f6);
}

.dropdown-item.danger {
  color: #ef4444;
}

.dropdown-item.danger:hover {
  background-color: rgba(239, 68, 68, 0.1);
  color: #dc2626;
}

.user-name-label {
  font-weight: 700;
  max-width: 110px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.user-badge.local-mode {
  background-color: rgba(16, 185, 129, 0.1);
  border: 1px solid rgba(16, 185, 129, 0.3);
  color: #059669;
}

.mode-label {
  font-weight: 600;
}

.login-trigger-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  background-color: var(--primary, #3b82f6);
  color: #ffffff;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.login-trigger-btn:hover {
  opacity: 0.9;
  transform: translateY(-1px);
}
</style>


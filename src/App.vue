<template>
  <div class="app-layout" :data-theme="theme">
    <!-- 1. Header Bar with Navigation Tabs -->
    <header class="header">
      <div class="header-left">
        <h1 class="app-title">📝 Todo Agent</h1>
      </div>

      <!-- Center Navbar Navigation Tabs -->
      <nav class="navbar-tabs">
        <button
          class="nav-tab-btn"
          :class="{ active: currentTab === 'todos' }"
          @click="currentTab = 'todos'"
          title="待办事项"
        >
          <CheckSquare :size="15" /> <span>待办事项</span>
        </button>

        <button
          class="nav-tab-btn"
          :class="{ active: currentTab === 'ai-chat' }"
          @click="currentTab = 'ai-chat'"
          title="AI 聊天"
        >
          <MessageSquare :size="15" /> <span>AI 聊天</span>
        </button>

        <button
          class="nav-tab-btn"
          :class="{ active: currentTab === 'calendar' }"
          @click="currentTab = 'calendar'"
          title="任务日历"
        >
          <Calendar :size="15" /> <span>任务日历</span>
        </button>

        <button
          class="nav-tab-btn"
          :class="{ active: currentTab === 'local-clock' }"
          @click="currentTab = 'local-clock'"
          title="本地时钟"
        >
          <Clock :size="15" /> <span>本地时钟</span>
        </button>

        <button
          class="nav-tab-btn"
          :class="{ active: currentTab === 'clock' }"
          @click="currentTab = 'clock'"
          title="专注时钟"
        >
          <Flame :size="15" /> <span>专注时钟</span>
        </button>

        <button
          class="nav-tab-btn"
          :class="{ active: currentTab === 'settings' }"
          @click="currentTab = 'settings'"
          title="系统设置"
        >
          <Settings :size="15" /> <span>系统设置</span>
        </button>
      </nav>

      <div class="header-right">
        <button
          class="nav-tab-btn"
          :class="{ active: showAiSidebar }"
          @click="showAiSidebar = !showAiSidebar"
          title="打开/收起 AI 聊天侧边栏"
        >
          <MessageSquare :size="15" /> <span>AI 助手</span>
        </button>
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
              <input
                type="text"
                v-model="searchKeyword"
                placeholder="🔍 搜索待办事项..."
                @input="loadTodos"
              />
            </div>

            <button class="btn btn-primary" @click="openAddModal">
              + 新建任务
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
            <p class="empty-icon">📌</p>
            <p class="empty-text">暂无待办事项，点击右上角 "+ 新建任务" 或使用 AI 创建吧！</p>
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
                  <span class="tag tag-category">📁 {{ todo.category }}</span>
                  <span class="tag" :class="'tag-prio-' + todo.priority">
                    {{ priorityLabel(todo.priority) }}
                  </span>
                  <span v-if="todo.remind_at" class="tag tag-reminder">
                    ⏰ {{ todo.remind_at }}
                  </span>
                </div>
              </div>

              <div class="card-actions">
                <button class="icon-btn edit-btn" @click="openEditModal(todo)" title="编辑任务">
                  ✏️
                </button>
                <button class="icon-btn delete-btn" @click="deleteTodo(todo.id)" title="删除任务">
                  🗑️
                </button>
              </div>
            </div>
          </div>
        </div>
      </template>

      <!-- Tab 3: AI Chat View -->
      <template v-else-if="currentTab === 'ai-chat'">
        <div class="ai-chat-page-wrapper">
          <AiChatSidebar
            :config="llmConfig"
            :is-processing="aiProcessing"
            :hide-toggle-btn="true"
            @send="handleAiPageSend"
            @update:config="onLlmConfigUpdate"
          />
        </div>
      </template>

      <!-- Tab 3: Calendar View -->
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

      <!-- Tab 5: Pomodoro Focus Clock View -->
      <template v-else-if="currentTab === 'clock'">
        <ClockPage />
      </template>

      <!-- Tab 5: Settings View -->
      <template v-else-if="currentTab === 'settings'">
        <SettingsPage
          v-model:theme="theme"
          v-model:config="llmConfig"
        />
      </template>
    </main>





    <!-- Floating AI Chat Sidebar Drawer Overlay -->
    <div v-if="showAiSidebar && currentTab !== 'ai-chat'" class="ai-drawer-overlay">
      <div class="drawer-backdrop" @click="showAiSidebar = false"></div>
      <div class="drawer-content">
        <AiChatSidebar
          :config="llmConfig"
          :is-processing="aiProcessing"
          :hide-toggle-btn="true"
          @send="handleAiPageSend"
          @update:config="onLlmConfigUpdate"
          @close="showAiSidebar = false"
        />
      </div>
    </div>

    <!-- Modals -->
    <!-- Add / Edit Modal -->
    <div v-if="showAddEditModal" class="modal-backdrop" @click.self="showAddEditModal = false">
      <div class="modal-card animate-fade-in">
        <h2 class="modal-title">{{ editingTodo ? '✏️ 编辑待办事项' : '➕ 添加新待办事项' }}</h2>

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
              <option value="high">🔴 高优 (high)</option>
              <option value="medium">🟡 中优 (medium)</option>
              <option value="low">🔵 低优 (low)</option>
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
        <h2 class="modal-title">⚙️ 配置大语言模型 (LLM)</h2>

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
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { CheckSquare, Calendar, Clock, Flame, Settings, MessageSquare } from 'lucide-vue-next'
import type { Todo, LlmConfig, FilterType, ThemeType } from './types'
import { showConfirm } from './utils/confirmState'
import LocalClockPage from './components/productivity/LocalClockPage.vue'
import CalendarView from './components/productivity/CalendarView.vue'
import ClockPage from './components/productivity/ClockPage.vue'
import SettingsPage from './components/common/SettingsPage.vue'
import AiChatSidebar from './components/ai/AiChatSidebar.vue'

// Navigation Tab State
type TabType = 'todos' | 'ai-chat' | 'calendar' | 'local-clock' | 'clock' | 'settings'
const currentTab = ref<TabType>('todos')
const showAiSidebar = ref(false)

function handleAiPageSend(text: string) {
  aiInput.value = text
  sendAiCommand()
}

function onLlmConfigUpdate(newConfig: LlmConfig) {
  llmConfig.value = { ...newConfig }
  localStorage.setItem('siliconflow_api_key', newConfig.api_key)
}

// Theme State
const theme = ref<ThemeType>((localStorage.getItem('todo_theme') as ThemeType) || 'light')
watch(theme, (newVal) => {
  localStorage.setItem('todo_theme', newVal)
  document.documentElement.setAttribute('data-theme', newVal)
})

// LLM Config State
const llmConfig = ref<LlmConfig>({
  provider: 'siliconflow',
  base_url: 'https://api.siliconflow.cn/v1',
  api_key: localStorage.getItem('siliconflow_api_key') || '',
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

// AI Input State
const aiInput = ref('')
const aiProcessing = ref(false)

// Tauri Invoke Helper (with fallback for web browser testing)
async function tauriInvoke<T>(cmd: string, args: Record<string, any> = {}): Promise<T> {
  try {
    const { invoke } = await import('@tauri-apps/api/core')
    return await invoke<T>(cmd, args)
  } catch (e) {
    console.warn(`[Tauri Web Fallback] ${cmd}`, args, e)
    // Web fallback mock implementation
    if (cmd === 'get_todos') {
      if (!localStorage.getItem('web_todos')) {
        const defaultData: Todo[] = [
          { id: 1, title: '完成项目整体架构设计', category: '工作', priority: 'high', completed: true, created_at: new Date().toISOString(), updated_at: new Date().toISOString() },
          { id: 2, title: '完成 Tauri Rust SQLite 数据库集成', category: '工作', priority: 'high', completed: true, created_at: new Date().toISOString(), updated_at: new Date().toISOString() },
          { id: 3, title: '集成大语言模型配置与语义解析', category: 'AI', priority: 'medium', completed: false, created_at: new Date().toISOString(), updated_at: new Date().toISOString() }
        ]
        localStorage.setItem('web_todos', JSON.stringify(defaultData))
      }
      const stored = JSON.parse(localStorage.getItem('web_todos') || '[]') as Todo[]
      return stored as T
    }
    if (cmd === 'add_todo') {
      const stored = JSON.parse(localStorage.getItem('web_todos') || '[]') as Todo[]
      const newId = Date.now()
      stored.push({
        id: newId,
        title: args.title,
        priority: args.priority,
        category: args.category,
        completed: false,
        remind_at: args.remind_at,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      })
      localStorage.setItem('web_todos', JSON.stringify(stored))
      return newId as T
    }
    if (cmd === 'update_todo_status') {
      const stored = JSON.parse(localStorage.getItem('web_todos') || '[]') as Todo[]
      const idx = stored.findIndex(t => t.id === args.id)
      if (idx >= 0) stored[idx].completed = args.completed
      localStorage.setItem('web_todos', JSON.stringify(stored))
      return true as T
    }
    if (cmd === 'update_todo') {
      const stored = JSON.parse(localStorage.getItem('web_todos') || '[]') as Todo[]
      const idx = stored.findIndex(t => t.id === args.id)
      if (idx >= 0) {
        stored[idx].title = args.title
        stored[idx].category = args.category
        stored[idx].priority = args.priority
        stored[idx].remind_at = args.remind_at
        stored[idx].updated_at = new Date().toISOString()
      }
      localStorage.setItem('web_todos', JSON.stringify(stored))
      return true as T
    }
    if (cmd === 'delete_todo') {
      let stored = JSON.parse(localStorage.getItem('web_todos') || '[]') as Todo[]
      stored = stored.filter(t => t.id !== args.id)
      localStorage.setItem('web_todos', JSON.stringify(stored))
      return true as T
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
    const result = await tauriInvoke<Todo[]>('get_todos', {
      filter: currentFilter.value,
      search: searchKeyword.value
    })
    todos.value = result || []
    statusMessage.value = `当前共加载 ${todos.value.length} 项待办任务`
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
    await tauriInvoke('update_todo_status', { id: todo.id, completed: newStatus })
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

  try {
    if (editingTodo.value) {
      await tauriInvoke('update_todo', {
        id: editingTodo.value.id,
        title: todoForm.value.title.trim(),
        category: todoForm.value.category.trim(),
        priority: todoForm.value.priority,
        remind_at: remindStr
      })
      statusMessage.value = `✅ 待办事项 [${todoForm.value.title}] 更新成功`
    } else {
      await tauriInvoke('add_todo', {
        title: todoForm.value.title.trim(),
        category: todoForm.value.category.trim(),
        priority: todoForm.value.priority,
        remind_at: remindStr
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
    await tauriInvoke('delete_todo', { id })
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
  localStorage.setItem('siliconflow_api_key', llmConfig.value.api_key)
  showModelModal.value = false
  statusMessage.value = `⚙️ LLM 配置已更新 [Provider: ${llmConfig.value.provider}, Model: ${llmConfig.value.model}]`
}

// Send AI Command
async function sendAiCommand() {
  const text = aiInput.value.trim()
  if (!text) return

  aiProcessing.value = true
  statusMessage.value = '🧠 AI 智能体分析思考并执行中...'

  try {
    const res = await tauriInvoke<any>('execute_ai_command', {
      input: text,
      config: llmConfig.value
    })
    aiInput.value = ''
    statusMessage.value = `✅ AI 任务完成：${res.message}`
    if (res.should_refresh) {
      loadTodos()
    }
  } catch (err: any) {
    statusMessage.value = `❌ AI 执行异常: ${err?.message || err}`
  } finally {
    aiProcessing.value = false
  }
}

onMounted(() => {
  document.documentElement.setAttribute('data-theme', theme.value)
  loadTodos()
})
</script>

<style scoped>
.app-layout {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background-color: var(--bg-app);
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 20px;
  background-color: var(--bg-surface);
  border-bottom: 1px solid var(--border-color);
  gap: 12px;
  flex-wrap: nowrap;
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
  background-color: rgba(255, 255, 255, 0.08);
}

.nav-tab-btn.active {
  color: var(--primary);
  background-color: var(--bg-surface);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
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

@media (max-width: 820px) {
  .nav-tab-btn {
    padding: 5px 8px;
    gap: 4px;
  }

  .header-right {
    gap: 8px;
  }
}

@media (max-width: 680px) {
  .nav-tab-btn span {
    display: none;
  }

  .nav-tab-btn {
    padding: 6px 10px;
  }

  .app-title {
    font-size: 15px;
  }

  .header-right .btn-primary {
    padding: 6px 10px;
    font-size: 12px;
  }
}

.theme-select-group {
  display: flex;
  align-items: center;
  gap: 6px;
}

.label-sm {
  font-size: 12px;
  color: var(--text-muted);
  font-weight: 500;
}

.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 16px 20px;
  overflow: hidden;
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

/* AI Chat Page & Drawer Layout */
.ai-chat-page-wrapper {
  width: 100%;
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: stretch;
  background-color: var(--bg-surface);
  overflow: hidden;
}

.ai-chat-page-wrapper :deep(.ai-sidebar) {
  width: 100%;
  max-width: 900px;
  border-left: none;
  box-shadow: 0 0 16px rgba(0, 0, 0, 0.05);
}

.ai-drawer-overlay {
  position: fixed;
  top: 0;
  right: 0;
  bottom: 0;
  left: 0;
  z-index: 100;
  display: flex;
  justify-content: flex-end;
}

.drawer-backdrop {
  position: absolute;
  top: 0;
  right: 0;
  bottom: 0;
  left: 0;
  background-color: rgba(0, 0, 0, 0.35);
  backdrop-filter: blur(2px);
}

.drawer-content {
  position: relative;
  width: 420px;
  max-width: 90vw;
  height: 100%;
  z-index: 101;
  box-shadow: -4px 0 20px rgba(0, 0, 0, 0.18);
  background-color: var(--bg-surface);
  animation: drawerSlideIn 0.22s cubic-bezier(0.16, 1, 0.3, 1);
}

@keyframes drawerSlideIn {
  from {
    transform: translateX(100%);
  }
  to {
    transform: translateX(0);
  }
}

.drawer-content :deep(.ai-sidebar) {
  width: 100% !important;
  border-left: none;
}
</style>

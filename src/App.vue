<template>
  <div class="app-layout" :data-theme="theme">
    <!-- 1. Header Bar -->
    <header class="header">
      <div class="header-left">
        <h1 class="app-title">📝 Todo Agent</h1>
        <span class="sub-badge">Rust + Vue 3</span>
      </div>

      <div class="header-center">
        <button class="model-badge-btn" @click="showModelModal = true" title="点击配置大语言模型">
          🧠 {{ llmConfig.model }} ⚙️
        </button>
      </div>

      <div class="header-right">
        <div class="theme-select-group">
          <label class="label-sm">主题:</label>
          <select v-model="theme" class="theme-select">
            <option value="light">☀️ 浅色明亮</option>
            <option value="dark">🌙 赛博暗黑</option>
            <option value="nord">❄️ 极光冰蓝</option>
          </select>
        </div>

        <button class="btn btn-primary" @click="openAddModal">
          + 新建任务
        </button>
      </div>
    </header>

    <!-- 2. Main Content -->
    <main class="main-content">
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

        <div class="search-box">
          <input
            type="text"
            v-model="searchKeyword"
            placeholder="🔍 搜索待办事项..."
            @input="loadTodos"
          />
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
    </main>

    <!-- 3. AI Command Input Bar -->
    <div class="ai-input-bar">
      <input
        type="text"
        v-model="aiInput"
        placeholder="✨ 输入 AI 智能体指令（例：'帮我安排明天上午10点和团队开会'）..."
        @keyup.enter="sendAiCommand"
        :disabled="aiProcessing"
      />
      <button class="btn btn-ai" @click="sendAiCommand" :disabled="aiProcessing || !aiInput.trim()">
        <span v-if="aiProcessing" class="spinner-sm"></span>
        <span v-else>🤖 AI 执行</span>
      </button>
    </div>

    <!-- 4. Status Bar -->
    <footer class="status-bar">
      <span class="status-text">{{ statusMessage }}</span>
    </footer>

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
import type { Todo, LlmConfig, FilterType, ThemeType } from './types'

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
async function deleteTodo(id: number) {
  if (!confirm('确定要彻底删除该待办事项吗？')) return
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
}

.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.app-title {
  font-size: 18px;
  font-weight: 700;
  color: var(--primary);
}

.sub-badge {
  font-size: 11px;
  font-weight: 600;
  background-color: var(--border-color);
  color: var(--text-muted);
  padding: 2px 8px;
  border-radius: 12px;
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
  transition: all 0.2s;
}

.model-badge-btn:hover {
  border-color: var(--ai-purple);
  transform: translateY(-1px);
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
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

.status-bar {
  padding: 6px 20px;
  background-color: var(--bg-surface);
  border-top: 1px solid var(--border-color);
  font-size: 12px;
  color: var(--text-muted);
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
</style>

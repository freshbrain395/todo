<template>
  <div class="search-engine-container animate-fade-in">
    <!-- Top Minimalist Utility Bar -->
    <header class="search-top-bar">
      <div class="top-bar-left">
        <div class="date-chip">
          <Calendar :size="14" />
          <span>{{ currentDateString }}</span>
        </div>
      </div>

      <div class="top-bar-right">
        <button class="top-nav-btn" @click="emit('openApp', 'todos')" title="待办事项">
          <CheckSquare :size="15" /> <span>待办清单</span>
        </button>
        <button class="top-nav-btn" @click="emit('openApp', 'calendar')" title="任务日历">
          <Calendar :size="15" /> <span>日历</span>
        </button>
        <button class="top-nav-btn" @click="emit('openApp', 'pomodoro')" title="番茄时钟">
          <Flame :size="15" /> <span>番茄钟</span>
        </button>
        <button class="top-nav-btn" @click="emit('openApp', 'countdown')" title="倒计时">
          <Hourglass :size="15" /> <span>倒计时</span>
        </button>
        <button class="top-nav-btn" @click="emit('openApp', 'alarm')" title="闹钟">
          <Bell :size="15" /> <span>闹钟</span>
        </button>
        <button class="top-nav-btn" @click="emit('openApp', 'local-clock')" title="本地时钟">
          <Clock :size="15" /> <span>时钟</span>
        </button>
        <button class="top-nav-btn btn-settings" @click="emit('openApp', 'settings')" title="系统设置">
          <Settings :size="15" /> <span>设置</span>
        </button>
      </div>
    </header>

    <!-- Center Hero Section -->
    <main class="search-center-wrapper">
      <!-- Search Engine Branding Logo -->
      <div class="brand-hero">
        <div class="brand-logo-icon">
          <Sparkles :size="38" class="sparkle-svg" />
        </div>
        <h1 class="brand-title">
          <span class="brand-accent">Todo</span>
          <span class="brand-text">Search</span>
        </h1>
        <p class="brand-tagline">自然语言意图规划 · 全局待办检索 · 智能助理</p>
      </div>

      <!-- Main Search Bar Box (Input box with left dropdown selector) -->
      <div class="search-box-card" :class="{ 'has-focus': isInputFocused, 'has-results': searchResults.length > 0 || aiLoading || aiResultMessage }">
        <!-- 1. Left Dropdown Select Box (下拉框) -->
        <div class="search-select-wrapper">
          <select v-model="searchType" class="search-type-select" @change="onTypeChange">
            <option value="todo">📝 待办任务</option>
            <option value="ai">🤖 AI 智能规划</option>
            <option value="all">🔍 全局搜索</option>
            <option value="bing">🌐 必应搜索</option>
            <option value="baidu">🇨🇳 百度搜索</option>
            <option value="google">🌍 谷歌搜索</option>
          </select>
          <ChevronDown :size="13" class="select-arrow" />
        </div>

        <div class="search-divider"></div>

        <!-- 2. Center Search Input Box (输入框) -->
        <div class="search-input-wrapper">
          <input
            ref="inputRef"
            type="text"
            v-model="searchQuery"
            :placeholder="inputPlaceholder"
            class="search-main-input"
            @focus="isInputFocused = true"
            @blur="onInputBlur"
            @keyup.enter="handleSearch"
          />
          <button v-if="searchQuery" class="btn-clear" @click="clearQuery" title="清空">
            <X :size="14" />
          </button>
        </div>

        <!-- 3. Right Action Search Button -->
        <button
          class="btn-search-action"
          :class="{ 'btn-ai-active': searchType === 'ai', loading: aiLoading }"
          :disabled="aiLoading"
          @click="handleSearch"
          :title="searchType === 'ai' ? '发送并让 AI 执行规划' : '搜索'"
        >
          <Loader2 v-if="aiLoading" :size="18" class="animate-spin" />
          <Send v-else-if="searchType === 'ai'" :size="18" />
          <Search v-else :size="18" />
        </button>
      </div>

      <!-- Search Suggestions & Quick Execution Buttons -->
      <div class="search-actions-row">
        <button class="action-pill-btn" @click="handleSearch">
          <Search :size="13" /> 立即检索
        </button>
        <button class="action-pill-btn" @click="switchToAiAndSearch">
          <Sparkles :size="13" /> AI 智能解析
        </button>
        <button class="action-pill-btn" @click="openQuickAdd">
          <Plus :size="13" /> 快速新建任务
        </button>
      </div>

      <!-- AI Execution Status Message Card -->
      <div v-if="aiResultMessage || aiLoading" class="ai-result-panel animate-fade-in">
        <div class="ai-panel-header">
          <div class="ai-badge">
            <Sparkles :size="14" />
            <span>AI 执行结果</span>
          </div>
          <button v-if="!aiLoading" class="btn-close-panel" @click="aiResultMessage = ''">
            <X :size="13" />
          </button>
        </div>
        <div class="ai-panel-body">
          <div v-if="aiLoading" class="ai-loading-state">
            <Loader2 :size="16" class="animate-spin" />
            <span>正在解析意图并规划执行，请稍候...</span>
          </div>
          <div v-else class="ai-message-text">
            {{ aiResultMessage }}
          </div>
        </div>
      </div>

      <!-- Real-time Matching Todos Results Card (when searching in todo/all mode) -->
      <div v-if="searchQuery.trim() && (searchType === 'todo' || searchType === 'all')" class="search-results-panel animate-fade-in">
        <div class="results-header">
          <span class="results-count">找到 {{ searchResults.length }} 项相关待办</span>
          <button
            v-if="searchResults.length === 0"
            class="btn-add-as-todo"
            @click="quickAddCurrentQuery"
          >
            <Plus :size="13" /> 将「{{ searchQuery }}」添加为新待办
          </button>
        </div>

        <div v-if="searchResults.length > 0" class="results-list">
          <div
            v-for="item in searchResults"
            :key="item.id"
            class="result-item"
            :class="{ completed: item.completed }"
          >
            <div class="item-left" @click="toggleTodoStatus(item)">
              <span class="item-checkbox" :class="{ checked: item.completed }">
                <Check v-if="item.completed" :size="12" />
              </span>
              <span class="item-title">{{ item.title }}</span>
            </div>
            <div class="item-right">
              <span class="badge-cat">{{ item.category }}</span>
              <span class="badge-prio" :class="'prio-' + item.priority">{{ getPriorityLabel(item.priority) }}</span>
              <button class="btn-item-del" @click="deleteItem(item.id)" title="删除任务">
                <Trash2 :size="13" />
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Quick Shortcuts Grid -->
      <div class="shortcuts-grid">
        <div class="shortcut-card" @click="emit('openApp', 'todos')">
          <div class="shortcut-icon icon-todos">
            <CheckSquare :size="20" />
          </div>
          <div class="shortcut-text">
            <span class="shortcut-name">待办任务</span>
            <span class="shortcut-desc">{{ pendingCount }} 项未完成</span>
          </div>
        </div>

        <div class="shortcut-card" @click="emit('openApp', 'calendar')">
          <div class="shortcut-icon icon-calendar">
            <Calendar :size="20" />
          </div>
          <div class="shortcut-text">
            <span class="shortcut-name">任务日历</span>
            <span class="shortcut-desc">视图与排期</span>
          </div>
        </div>

        <div class="shortcut-card" @click="emit('openApp', 'pomodoro')">
          <div class="shortcut-icon icon-pomodoro">
            <Flame :size="20" />
          </div>
          <div class="shortcut-text">
            <span class="shortcut-name">番茄专注</span>
            <span class="shortcut-desc">25+5 分钟</span>
          </div>
        </div>

        <div class="shortcut-card" @click="emit('openApp', 'countdown')">
          <div class="shortcut-icon icon-countdown">
            <Hourglass :size="20" />
          </div>
          <div class="shortcut-text">
            <span class="shortcut-name">倒计时 / 闹钟</span>
            <span class="shortcut-desc">计时提醒</span>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import {
  Search, Sparkles, CheckSquare, Calendar, Flame, Hourglass, Bell,
  Clock, Settings, ChevronDown, X, Send, Check, Trash2, Plus, Loader2
} from 'lucide-vue-next'
import type { Todo, LlmConfig } from '../../types'

const props = defineProps<{
  todos: Todo[]
  llmConfig: LlmConfig
}>()

const emit = defineEmits<{
  (e: 'openApp', tab: string): void
  (e: 'openAddTodo'): void
  (e: 'addTodo', title: string): void
  (e: 'toggleStatus', todo: Todo): void
  (e: 'deleteTodo', id: number): void
  (e: 'executeAi', input: string): void
}>()

const searchType = ref<'todo' | 'ai' | 'all' | 'bing' | 'baidu' | 'google'>('todo')
const searchQuery = ref('')
const isInputFocused = ref(false)
const inputRef = ref<HTMLInputElement | null>(null)
const aiLoading = ref(false)
const aiResultMessage = ref('')

const currentDateString = computed(() => {
  const d = new Date()
  const days = ['星期日', '星期一', '星期二', '星期三', '星期四', '星期五', '星期六']
  return `${d.getFullYear()}年${d.getMonth() + 1}月${d.getDate()}日 ${days[d.getDay()]}`
})

const pendingCount = computed(() => props.todos.filter(t => !t.completed).length)

const inputPlaceholder = computed(() => {
  switch (searchType.value) {
    case 'ai':
      return '输入自然语言任务规划，例如：明天下午3点提醒我开会、制定本周学习计划...'
    case 'todo':
      return '输入任务名称搜索待办，或输入新任务后按回车快速添加...'
    case 'all':
      return '输入关键词全局检索待办与相关事项...'
    case 'bing':
      return '在必应 (Bing) 中搜索网页内容，按回车跳转...'
    case 'baidu':
      return '在百度 (Baidu) 中搜索互联网信息，按回车跳转...'
    case 'google':
      return '在谷歌 (Google) 中搜索网络内容，按回车跳转...'
  }
})

const searchResults = computed(() => {
  const q = searchQuery.value.trim().toLowerCase()
  if (!q) return []
  return props.todos.filter(t =>
    t.title.toLowerCase().includes(q) ||
    t.category.toLowerCase().includes(q)
  )
})

function onTypeChange() {
  inputRef.value?.focus()
}

function onInputBlur() {
  setTimeout(() => {
    isInputFocused.value = false
  }, 200)
}

function clearQuery() {
  searchQuery.value = ''
  aiResultMessage.value = ''
  inputRef.value?.focus()
}

function switchToAiAndSearch() {
  searchType.value = 'ai'
  handleSearch()
}

function openQuickAdd() {
  emit('openAddTodo')
}

function quickAddCurrentQuery() {
  if (!searchQuery.value.trim()) return
  emit('addTodo', searchQuery.value.trim())
  searchQuery.value = ''
}

function handleSearch() {
  const q = searchQuery.value.trim()
  if (!q) return

  if (searchType.value === 'bing') {
    window.open(`https://www.bing.com/search?q=${encodeURIComponent(q)}`, '_blank')
    return
  }
  if (searchType.value === 'baidu') {
    window.open(`https://www.baidu.com/s?wd=${encodeURIComponent(q)}`, '_blank')
    return
  }
  if (searchType.value === 'google') {
    window.open(`https://www.google.com/search?q=${encodeURIComponent(q)}`, '_blank')
    return
  }

  if (searchType.value === 'ai') {
    emit('executeAi', q)
    return
  }

  if (searchType.value === 'todo') {
    // If no matching todos, allow quick add
    if (searchResults.value.length === 0) {
      emit('addTodo', q)
      searchQuery.value = ''
    }
  }
}

function toggleTodoStatus(todo: Todo) {
  emit('toggleStatus', todo)
}

function deleteItem(id: number) {
  emit('deleteTodo', id)
}

function getPriorityLabel(prio: string) {
  switch (prio) {
    case 'high': return '高优'
    case 'medium': return '中优'
    case 'low': return '低优'
    default: return prio
  }
}
</script>

<style scoped>
.search-engine-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  width: 100%;
  background: var(--bg-app);
  overflow-y: auto;
  position: relative;
  box-sizing: border-box;
}

/* Top Minimalist Bar */
.search-top-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 28px;
  width: 100%;
  box-sizing: border-box;
  z-index: 10;
}

.top-bar-left .date-chip {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 500;
  color: var(--text-muted, #64748b);
  background: var(--bg-card, rgba(255, 255, 255, 0.7));
  padding: 6px 14px;
  border-radius: 20px;
  border: 1px solid var(--border-color, rgba(0, 0, 0, 0.08));
}

.top-bar-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.top-nav-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 7px 13px;
  border-radius: 20px;
  font-size: 13px;
  font-weight: 500;
  background: var(--bg-card, rgba(255, 255, 255, 0.8));
  color: var(--text-main, #334155);
  border: 1px solid var(--border-color, rgba(0, 0, 0, 0.08));
  cursor: pointer;
  transition: all 0.2s ease;
}

.top-nav-btn:hover {
  background: var(--primary, #3b82f6);
  color: #ffffff;
  border-color: var(--primary, #3b82f6);
  transform: translateY(-1px);
}

.top-nav-btn.btn-settings {
  color: var(--text-muted, #64748b);
}

/* Center Wrapper */
.search-center-wrapper {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 20px 24px 80px 24px;
  max-width: 860px;
  margin: 0 auto;
  width: 100%;
  box-sizing: border-box;
}

/* Brand Hero */
.brand-hero {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  margin-bottom: 32px;
}

.brand-logo-icon {
  width: 64px;
  height: 64px;
  border-radius: 20px;
  background: linear-gradient(135deg, var(--primary, #3b82f6), #8b5cf6);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #ffffff;
  box-shadow: 0 10px 25px -5px rgba(59, 130, 246, 0.4);
  margin-bottom: 16px;
}

.brand-title {
  margin: 0;
  font-size: 40px;
  font-weight: 800;
  letter-spacing: -0.5px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.brand-accent {
  color: var(--primary, #3b82f6);
}

.brand-text {
  color: var(--text-main, #1e293b);
}

.brand-tagline {
  margin: 8px 0 0 0;
  font-size: 14px;
  color: var(--text-muted, #64748b);
  font-weight: 400;
}

/* Central Search Box Card */
.search-box-card {
  display: flex;
  align-items: center;
  width: 100%;
  max-width: 740px;
  background: var(--bg-card, #ffffff);
  border: 1.5px solid var(--border-color, #e2e8f0);
  border-radius: 36px;
  padding: 6px 10px 6px 18px;
  box-shadow: 0 8px 30px -4px rgba(0, 0, 0, 0.08);
  transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
  box-sizing: border-box;
}

.search-box-card.has-focus,
.search-box-card:hover {
  border-color: var(--primary, #3b82f6);
  box-shadow: 0 12px 36px -4px rgba(59, 130, 246, 0.18);
  transform: translateY(-1px);
}

/* Dropdown Selector on the left */
.search-select-wrapper {
  position: relative;
  display: flex;
  align-items: center;
  flex-shrink: 0;
}

.search-type-select {
  appearance: none;
  -webkit-appearance: none;
  border: none;
  background: transparent;
  padding: 8px 24px 8px 8px;
  font-size: 14px;
  font-weight: 600;
  color: var(--text-main, #1e293b);
  cursor: pointer;
  outline: none;
}

.search-type-select:hover {
  color: var(--primary, #3b82f6);
}

.select-arrow {
  position: absolute;
  right: 6px;
  pointer-events: none;
  color: var(--text-muted, #64748b);
}

.search-divider {
  width: 1px;
  height: 24px;
  background-color: var(--border-color, #e2e8f0);
  margin: 0 10px;
  flex-shrink: 0;
}

/* Center Input Field */
.search-input-wrapper {
  flex: 1;
  display: flex;
  align-items: center;
  position: relative;
  min-width: 0;
}

.search-main-input {
  width: 100%;
  border: none;
  outline: none;
  background: transparent;
  font-size: 15px;
  color: var(--text-main, #0f172a);
  padding: 8px 26px 8px 4px;
}

.search-main-input::placeholder {
  color: var(--text-muted, #94a3b8);
  font-size: 14px;
}

.btn-clear {
  position: absolute;
  right: 6px;
  background: transparent;
  border: none;
  color: var(--text-muted, #94a3b8);
  cursor: pointer;
  padding: 4px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.btn-clear:hover {
  background: var(--bg-hover, #f1f5f9);
  color: var(--text-main, #334155);
}

/* Search Action Button */
.btn-search-action {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: var(--primary, #3b82f6);
  color: #ffffff;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  flex-shrink: 0;
  transition: all 0.2s ease;
}

.btn-search-action:hover {
  opacity: 0.92;
  transform: scale(1.05);
}

.btn-search-action.btn-ai-active {
  background: linear-gradient(135deg, var(--primary, #3b82f6), #8b5cf6);
}

/* Suggestions Row */
.search-actions-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 20px;
  flex-wrap: wrap;
  justify-content: center;
}

.action-pill-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border-radius: 20px;
  font-size: 13px;
  font-weight: 500;
  background: var(--bg-card, #ffffff);
  color: var(--text-main, #475569);
  border: 1px solid var(--border-color, #e2e8f0);
  cursor: pointer;
  transition: all 0.2s ease;
}

.action-pill-btn:hover {
  background: var(--bg-hover, #f8fafc);
  border-color: var(--primary, #3b82f6);
  color: var(--primary, #3b82f6);
}

/* AI Execution Panel */
.ai-result-panel {
  width: 100%;
  max-width: 740px;
  margin-top: 20px;
  background: var(--bg-card, #ffffff);
  border: 1px solid var(--border-color, #e2e8f0);
  border-radius: 16px;
  padding: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
}

.ai-panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.ai-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  font-weight: 600;
  color: #8b5cf6;
  background: rgba(139, 92, 246, 0.1);
  padding: 4px 10px;
  border-radius: 12px;
}

.btn-close-panel {
  background: transparent;
  border: none;
  color: var(--text-muted, #94a3b8);
  cursor: pointer;
  padding: 4px;
}

.ai-loading-state {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: var(--text-muted, #64748b);
}

.ai-message-text {
  font-size: 14px;
  line-height: 1.6;
  color: var(--text-main, #1e293b);
  white-space: pre-wrap;
}

/* Real-time Search Results Panel */
.search-results-panel {
  width: 100%;
  max-width: 740px;
  margin-top: 20px;
  background: var(--bg-card, #ffffff);
  border: 1px solid var(--border-color, #e2e8f0);
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
}

.results-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 18px;
  background: var(--bg-hover, #f8fafc);
  border-bottom: 1px solid var(--border-color, #e2e8f0);
}

.results-count {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-muted, #64748b);
}

.btn-add-as-todo {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--primary, #3b82f6);
  background: transparent;
  border: none;
  cursor: pointer;
  font-weight: 600;
}

.results-list {
  max-height: 280px;
  overflow-y: auto;
}

.result-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 18px;
  border-bottom: 1px solid var(--border-color, #f1f5f9);
  transition: background 0.15s ease;
}

.result-item:last-child {
  border-bottom: none;
}

.result-item:hover {
  background: var(--bg-hover, #f8fafc);
}

.item-left {
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
  flex: 1;
  min-width: 0;
}

.item-checkbox {
  width: 18px;
  height: 18px;
  border-radius: 5px;
  border: 1.5px solid var(--border-color, #cbd5e1);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: all 0.2s ease;
}

.item-checkbox.checked {
  background: #10b981;
  border-color: #10b981;
  color: #ffffff;
}

.item-title {
  font-size: 14px;
  color: var(--text-main, #1e293b);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.result-item.completed .item-title {
  text-decoration: line-through;
  color: var(--text-muted, #94a3b8);
}

.item-right {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.badge-cat {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 10px;
  background: var(--bg-hover, #f1f5f9);
  color: var(--text-muted, #64748b);
}

.badge-prio {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 10px;
  font-weight: 500;
}

.prio-high {
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
}

.prio-medium {
  background: rgba(245, 158, 11, 0.1);
  color: #f59e0b;
}

.prio-low {
  background: rgba(16, 185, 129, 0.1);
  color: #10b981;
}

.btn-item-del {
  background: transparent;
  border: none;
  color: var(--text-muted, #94a3b8);
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
  transition: color 0.15s ease;
}

.btn-item-del:hover {
  color: #ef4444;
}

/* Shortcuts Grid */
.shortcuts-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  width: 100%;
  max-width: 740px;
  margin-top: 36px;
}

.shortcut-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  background: var(--bg-card, #ffffff);
  border: 1px solid var(--border-color, #e2e8f0);
  border-radius: 16px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.shortcut-card:hover {
  transform: translateY(-2px);
  border-color: var(--primary, #3b82f6);
  box-shadow: 0 8px 20px -4px rgba(0, 0, 0, 0.06);
}

.shortcut-icon {
  width: 40px;
  height: 40px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.icon-todos {
  background: rgba(59, 130, 246, 0.1);
  color: #3b82f6;
}

.icon-calendar {
  background: rgba(16, 185, 129, 0.1);
  color: #10b981;
}

.icon-pomodoro {
  background: rgba(249, 115, 22, 0.1);
  color: #f97316;
}

.icon-countdown {
  background: rgba(139, 92, 246, 0.1);
  color: #8b5cf6;
}

.shortcut-text {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.shortcut-name {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-main, #1e293b);
}

.shortcut-desc {
  font-size: 11px;
  color: var(--text-muted, #64748b);
  margin-top: 2px;
}

@media (max-width: 640px) {
  .shortcuts-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  .brand-title {
    font-size: 32px;
  }
}
</style>

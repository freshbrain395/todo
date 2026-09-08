<template>
  <div class="search-home animate-fade-in">
    <header class="home-header">
      <div class="brand-mini">
        <div class="brand-mini-icon"><Sparkles :size="17" /></div>
        <span>Todo Agent</span>
      </div>
      <div class="header-date">
        <Calendar :size="14" />
        <span>{{ currentDateString }}</span>
      </div>
    </header>

    <main class="home-content">
      <section class="hero">
        <div class="hero-icon"><Sparkles :size="34" /></div>
        <h1><span>Todo</span> Agent</h1>
        <p>告诉我你想做什么，我来帮你安排、执行和管理。</p>

        <div class="command-box" :class="{ focused: isInputFocused, loading: aiLoading }">
          <div class="command-type">
            <select v-model="searchType" @change="onTypeChange" aria-label="输入模式">
              <option value="todo">📝 待办</option>
              <option value="ai">🤖 AI 执行</option>
              <option value="all">🔍 搜索</option>
              <option value="bing">🌐 必应</option>
              <option value="baidu">🇨🇳 百度</option>
              <option value="google">🌍 谷歌</option>
            </select>
            <ChevronDown :size="13" />
          </div>
          <div class="command-divider"></div>
          <input
            ref="inputRef"
            v-model="searchQuery"
            :placeholder="inputPlaceholder"
            @focus="isInputFocused = true"
            @blur="onInputBlur"
            @keyup.enter="handleSearch"
          />
          <button v-if="searchQuery" class="clear-btn" @click="clearQuery" title="清空"><X :size="14" /></button>
          <button class="send-btn" :disabled="aiLoading" @click="handleSearch" title="执行">
            <Loader2 v-if="aiLoading" :size="18" class="animate-spin" />
            <Send v-else-if="searchType === 'ai'" :size="18" />
            <Search v-else :size="18" />
          </button>
        </div>

        <div class="suggestions">
          <button @click="useSuggestion('今天有什么任务？')">今天有什么任务？</button>
          <button @click="useSuggestion('明天下午三点提醒我给客户打电话')">明天下午提醒我打电话</button>
          <button @click="useSuggestion('帮我安排 25 分钟专注时间')">安排 25 分钟专注</button>
        </div>
      </section>

      <section v-if="aiResultMessage || aiLoading" class="result-card ai-card animate-fade-in">
        <div class="result-card-title">
          <span><Sparkles :size="14" /> AI 执行结果</span>
          <button v-if="!aiLoading" @click="aiResultMessage = ''"><X :size="13" /></button>
        </div>
        <div v-if="aiLoading" class="loading-line"><Loader2 :size="16" class="animate-spin" /> 正在理解你的需求并执行……</div>
        <div v-else class="result-message">{{ aiResultMessage }}</div>
      </section>

      <section v-if="searchQuery.trim() && (searchType === 'todo' || searchType === 'all')" class="result-card animate-fade-in">
        <div class="result-card-title">
          <span><Search :size="14" /> 找到 {{ searchResults.length }} 项相关待办</span>
          <button v-if="searchResults.length === 0" class="link-btn" @click="quickAddCurrentQuery">+ 添加为待办</button>
        </div>
        <div v-if="searchResults.length" class="results-list">
          <div v-for="item in searchResults" :key="item.id" class="result-item" :class="{ completed: item.completed }">
            <button class="todo-check" @click="toggleTodoStatus(item)">
              <Check v-if="item.completed" :size="12" />
            </button>
            <span class="todo-title">{{ item.title }}</span>
            <span class="badge">{{ item.category }}</span>
            <span class="badge priority" :class="'priority-' + item.priority">{{ getPriorityLabel(item.priority) }}</span>
            <button class="delete-btn" @click="deleteItem(item.id)" title="删除"><Trash2 :size="13" /></button>
          </div>
        </div>
      </section>

      <section class="today-section">
        <div class="section-heading">
          <div>
            <span class="eyebrow">TODAY</span>
            <h2>今日概览</h2>
          </div>
          <span class="todo-count">{{ pendingCount }} 项待完成</span>
        </div>
        <div class="overview-grid">
          <button class="overview-card" @click="emit('openApp', 'todos')">
            <div class="overview-icon todo-icon"><CheckSquare :size="19" /></div>
            <div><strong>{{ pendingCount }}</strong><span>待办事项</span></div>
            <ChevronRight :size="15" />
          </button>
          <button class="overview-card" @click="emit('openApp', 'calendar')">
            <div class="overview-icon calendar-icon"><Calendar :size="19" /></div>
            <div><strong>日程</strong><span>查看任务安排</span></div>
            <ChevronRight :size="15" />
          </button>
          <button class="overview-card" @click="emit('openApp', 'pomodoro')">
            <div class="overview-icon focus-icon"><Flame :size="19" /></div>
            <div><strong>专注</strong><span>开始番茄时钟</span></div>
            <ChevronRight :size="15" />
          </button>
          <button class="overview-card" @click="emit('openApp', 'countdown')">
            <div class="overview-icon timer-icon"><Hourglass :size="19" /></div>
            <div><strong>计时</strong><span>倒计时与提醒</span></div>
            <ChevronRight :size="15" />
          </button>
        </div>
      </section>

      <div class="quick-links">
        <button @click="openQuickAdd"><Plus :size="14" /> 快速新建任务</button>
        <button @click="emit('openApp', 'alarm')"><Bell :size="14" /> 管理闹钟</button>
        <button @click="emit('openApp', 'settings')"><Settings :size="14" /> 设置</button>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import {
  Search, Sparkles, CheckSquare, Calendar, Flame, Hourglass, Bell, Settings,
  ChevronDown, ChevronRight, X, Send, Check, Trash2, Plus, Loader2
} from 'lucide-vue-next'
import type { Todo, LlmConfig } from '../../types'

const props = defineProps<{ todos: Todo[]; llmConfig: LlmConfig }>()
const emit = defineEmits<{
  (e: 'openApp', tab: string): void
  (e: 'openAddTodo'): void
  (e: 'addTodo', title: string): void
  (e: 'toggleStatus', todo: Todo): void
  (e: 'deleteTodo', id: number): void
  (e: 'executeAi', input: string): void
}>()

const searchType = ref<'todo' | 'ai' | 'all' | 'bing' | 'baidu' | 'google'>('ai')
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
const searchResults = computed(() => {
  const q = searchQuery.value.trim().toLowerCase()
  if (!q) return []
  return props.todos.filter(t => t.title.toLowerCase().includes(q) || t.category.toLowerCase().includes(q))
})
const inputPlaceholder = computed(() => {
  switch (searchType.value) {
    case 'ai': return '例如：明天下午 3 点提醒我给客户打电话'
    case 'todo': return '搜索待办，找不到时可以直接创建'
    case 'all': return '搜索你的待办事项'
    case 'bing': return '在必应搜索网页内容'
    case 'baidu': return '在百度搜索互联网信息'
    case 'google': return '在谷歌搜索网络内容'
  }
})

function onTypeChange() { inputRef.value?.focus() }
function onInputBlur() { setTimeout(() => { isInputFocused.value = false }, 200) }
function clearQuery() { searchQuery.value = ''; aiResultMessage.value = ''; inputRef.value?.focus() }
function useSuggestion(text: string) { searchType.value = 'ai'; searchQuery.value = text; inputRef.value?.focus(); handleSearch() }
function openQuickAdd() { emit('openAddTodo') }
function quickAddCurrentQuery() { if (!searchQuery.value.trim()) return; emit('addTodo', searchQuery.value.trim()); searchQuery.value = '' }
function handleSearch() {
  const q = searchQuery.value.trim()
  if (!q) return
  if (searchType.value === 'bing') { window.open(`https://www.bing.com/search?q=${encodeURIComponent(q)}`, '_blank'); return }
  if (searchType.value === 'baidu') { window.open(`https://www.baidu.com/s?wd=${encodeURIComponent(q)}`, '_blank'); return }
  if (searchType.value === 'google') { window.open(`https://www.google.com/search?q=${encodeURIComponent(q)}`, '_blank'); return }
  if (searchType.value === 'ai') { emit('executeAi', q); return }
  if (searchType.value === 'todo' && searchResults.value.length === 0) { emit('addTodo', q); searchQuery.value = '' }
}
function toggleTodoStatus(todo: Todo) { emit('toggleStatus', todo) }
function deleteItem(id: number) { emit('deleteTodo', id) }
function getPriorityLabel(prio: string) { return prio === 'high' ? '高优' : prio === 'medium' ? '中优' : prio === 'low' ? '低优' : prio }
</script>

<style scoped>
.search-home { min-height: 100vh; width: 100%; background: var(--bg-app); color: var(--text-main, #1e293b); overflow-y: auto; box-sizing: border-box; }
.home-header { height: 64px; padding: 0 32px; display: flex; align-items: center; justify-content: space-between; box-sizing: border-box; }
.brand-mini, .header-date { display: flex; align-items: center; gap: 8px; color: var(--text-muted, #64748b); font-size: 13px; }
.brand-mini { color: var(--text-main, #334155); font-weight: 700; font-size: 15px; }
.brand-mini-icon { width: 30px; height: 30px; border-radius: 9px; display: flex; align-items: center; justify-content: center; color: #fff; background: linear-gradient(135deg, var(--primary, #3b82f6), #8b5cf6); }
.home-content { width: min(860px, calc(100% - 40px)); margin: 0 auto; padding: 46px 0 70px; box-sizing: border-box; }
.hero { text-align: center; }
.hero-icon { width: 58px; height: 58px; margin: 0 auto 15px; border-radius: 18px; display: flex; align-items: center; justify-content: center; color: #fff; background: linear-gradient(135deg, var(--primary, #3b82f6), #8b5cf6); box-shadow: 0 12px 28px rgba(59,130,246,.18); }
.hero h1 { margin: 0; font-size: 38px; letter-spacing: -1px; font-weight: 800; }
.hero h1 span { color: var(--primary, #3b82f6); }
.hero p { margin: 9px 0 25px; color: var(--text-muted, #64748b); font-size: 14px; }
.command-box { width: min(760px, 100%); margin: 0 auto; min-height: 58px; display: flex; align-items: center; padding: 6px 9px 6px 17px; border: 1px solid var(--border-color, #dbe3ed); border-radius: 30px; background: var(--bg-card, #fff); box-shadow: 0 8px 30px rgba(15,23,42,.07); transition: .2s; box-sizing: border-box; }
.command-box.focused, .command-box:hover { border-color: var(--primary, #3b82f6); box-shadow: 0 12px 34px rgba(59,130,246,.14); }
.command-type { position: relative; display: flex; align-items: center; color: var(--text-muted, #64748b); flex-shrink: 0; }
.command-type select { appearance: none; border: 0; outline: 0; background: transparent; padding: 8px 23px 8px 0; color: var(--text-main, #334155); font-weight: 600; cursor: pointer; }
.command-type svg { position: absolute; right: 4px; pointer-events: none; }
.command-divider { width: 1px; height: 25px; background: var(--border-color, #e2e8f0); margin: 0 13px; }
.command-box input { flex: 1; min-width: 0; border: 0; outline: 0; background: transparent; font-size: 15px; color: var(--text-main, #0f172a); padding: 10px 30px 10px 0; }
.command-box input::placeholder { color: var(--text-muted, #94a3b8); }
.clear-btn { border: 0; background: transparent; color: #94a3b8; padding: 5px; cursor: pointer; }
.send-btn { width: 44px; height: 44px; flex-shrink: 0; border: 0; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: #fff; background: var(--primary, #3b82f6); cursor: pointer; transition: .2s; }
.send-btn:hover:not(:disabled) { transform: scale(1.05); }
.send-btn:disabled { opacity: .65; cursor: wait; }
.suggestions { margin-top: 14px; display: flex; gap: 8px; flex-wrap: wrap; justify-content: center; }
.suggestions button, .quick-links button { border: 1px solid var(--border-color, #e2e8f0); background: var(--bg-card, #fff); color: var(--text-muted, #64748b); border-radius: 18px; padding: 7px 12px; font-size: 12px; cursor: pointer; transition: .2s; }
.suggestions button:hover, .quick-links button:hover { color: var(--primary, #3b82f6); border-color: var(--primary, #3b82f6); }
.result-card { width: min(760px, 100%); margin: 24px auto 0; border: 1px solid var(--border-color, #e2e8f0); border-radius: 15px; background: var(--bg-card, #fff); box-shadow: 0 4px 18px rgba(15,23,42,.04); overflow: hidden; }
.result-card-title { min-height: 44px; padding: 0 15px; display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid var(--border-color, #eef2f7); font-size: 12px; font-weight: 600; color: var(--text-muted, #64748b); }
.result-card-title span { display: flex; align-items: center; gap: 7px; }
.result-card-title button { border: 0; background: transparent; color: #94a3b8; cursor: pointer; }
.link-btn { color: var(--primary, #3b82f6) !important; font-weight: 600; }
.loading-line { padding: 16px; display: flex; align-items: center; gap: 8px; color: var(--text-muted, #64748b); font-size: 13px; }
.result-message { padding: 15px 16px; white-space: pre-wrap; line-height: 1.6; font-size: 14px; }
.results-list { max-height: 280px; overflow-y: auto; }
.result-item { display: flex; align-items: center; gap: 9px; padding: 10px 15px; border-bottom: 1px solid var(--border-color, #f1f5f9); }
.result-item:last-child { border-bottom: 0; }
.todo-check { width: 18px; height: 18px; border-radius: 5px; border: 1px solid #cbd5e1; background: transparent; color: #fff; display: flex; align-items: center; justify-content: center; padding: 0; cursor: pointer; flex-shrink: 0; }
.result-item.completed .todo-check { background: #10b981; border-color: #10b981; }
.todo-title { flex: 1; min-width: 0; font-size: 13px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.result-item.completed .todo-title { text-decoration: line-through; color: #94a3b8; }
.badge { font-size: 10px; padding: 3px 7px; border-radius: 10px; background: #f1f5f9; color: #64748b; }
.priority-high { background: rgba(239,68,68,.1); color: #ef4444; }.priority-medium { background: rgba(245,158,11,.1); color: #f59e0b; }.priority-low { background: rgba(16,185,129,.1); color: #10b981; }
.delete-btn { border: 0; background: transparent; color: #94a3b8; cursor: pointer; padding: 4px; }.delete-btn:hover { color: #ef4444; }
.today-section { margin-top: 52px; }
.section-heading { display: flex; align-items: end; justify-content: space-between; margin-bottom: 14px; }
.eyebrow { font-size: 10px; letter-spacing: 1.4px; color: var(--primary, #3b82f6); font-weight: 800; }
.section-heading h2 { margin: 3px 0 0; font-size: 20px; }
.todo-count { font-size: 12px; color: var(--text-muted, #64748b); }
.overview-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 11px; }
.overview-card { min-height: 92px; padding: 14px; display: grid; grid-template-columns: auto 1fr auto; align-items: center; gap: 10px; text-align: left; border: 1px solid var(--border-color, #e2e8f0); border-radius: 14px; background: var(--bg-card, #fff); color: var(--text-main, #334155); cursor: pointer; transition: .2s; }
.overview-card:hover { transform: translateY(-2px); border-color: var(--primary, #3b82f6); box-shadow: 0 8px 20px rgba(15,23,42,.06); }
.overview-icon { width: 38px; height: 38px; border-radius: 11px; display: flex; align-items: center; justify-content: center; }
.todo-icon { background: rgba(59,130,246,.1); color: #3b82f6; }.calendar-icon { background: rgba(16,185,129,.1); color: #10b981; }.focus-icon { background: rgba(249,115,22,.1); color: #f97316; }.timer-icon { background: rgba(139,92,246,.1); color: #8b5cf6; }
.overview-card div:nth-child(2) { display: flex; flex-direction: column; min-width: 0; }.overview-card strong { font-size: 15px; }.overview-card span { margin-top: 3px; font-size: 10px; color: var(--text-muted, #64748b); }
.overview-card > svg { color: #cbd5e1; }
.quick-links { display: flex; justify-content: center; gap: 9px; margin-top: 25px; }
@media (max-width: 720px) { .home-header { padding: 0 18px; }.home-content { width: min(100% - 24px, 600px); padding-top: 30px; }.hero h1 { font-size: 32px; }.overview-grid { grid-template-columns: repeat(2, 1fr); } .header-date { display: none; } }
@media (max-width: 520px) { .command-type select { max-width: 75px; overflow: hidden; }.command-divider { margin: 0 7px; }.suggestions button:nth-child(3) { display: none; }.overview-grid { grid-template-columns: 1fr 1fr; }.overview-card { min-height: 80px; padding: 10px; }.badge { display: none; }.quick-links { flex-wrap: wrap; } }
</style>

<template>
  <div class="desktop-view-container animate-fade-in">
    <!-- Desktop Wallpaper Gradient Background Overlay -->
    <div class="desktop-bg-glow"></div>

    <!-- Desktop Workspace Canvas -->
    <div class="desktop-workspace">
      <!-- 1. Hero Widget: Live Clock & Date Banner -->
      <div class="desktop-hero-banner">
        <div class="hero-clock-block">
          <div class="hero-time-digits">
            <span class="digit-hours">{{ timeHours }}</span>
            <span class="time-colon">:</span>
            <span class="digit-minutes">{{ timeMinutes }}</span>
            <span class="digit-seconds">{{ timeSeconds }}</span>
          </div>
          <div class="hero-date-row">
            <span class="date-greeting">{{ greetingText }}</span>
            <span class="date-sep">·</span>
            <span class="date-full">{{ dateFullString }}</span>
            <span class="date-sep">·</span>
            <span class="date-lunar" v-if="lunarString">农历 {{ lunarString }}</span>
          </div>
        </div>

        <!-- Hero Right Actions (User Pill + Todo Counter) -->
        <div class="hero-actions-group">
          <div
            class="hero-user-pill"
            @click="emit('openLogin')"
            :title="currentUser ? `当前账号: ${currentUser.username} (点击切换)` : '点击登录/注册账号'"
          >
            <div class="user-avatar-dot" :class="{ 'is-logged-in': !!currentUser }">
              <User :size="14" />
            </div>
            <span class="user-name-text">{{ currentUser ? currentUser.username : '游客模式' }}</span>
          </div>

          <!-- Quick Todo Counter Badge -->
          <div class="hero-summary-card" @click="emit('openApp', 'todos')" title="查看待办列表">
            <div class="summary-icon-box">
              <CheckSquare :size="22" />
            </div>
            <div class="summary-text-box">
              <div class="summary-number-row">
                <span class="num-highlight">{{ pendingCount }}</span>
                <span class="num-total">/ {{ todos.length }} 项</span>
              </div>
              <span class="summary-label">待完成事项</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 2. Desktop App Icons Grid -->
      <div class="desktop-section-header">
        <span class="section-title-tag"><LayoutGrid :size="14" /> 桌面应用启动台</span>
        <span class="section-subtitle">点击直接打开对应功能模块</span>
      </div>

      <div class="desktop-apps-grid">
        <!-- 1. Todos -->
        <div class="app-icon-card card-todos" @click="emit('openApp', 'todos')">
          <div class="app-icon-wrapper theme-todos">
            <CheckSquare :size="32" class="app-svg" />
            <span v-if="pendingCount > 0" class="app-badge-pill">{{ pendingCount }}</span>
          </div>
          <div class="app-info">
            <div class="app-name">待办事项</div>
            <div class="app-desc">个人清单与任务规划</div>
          </div>
        </div>

        <!-- 2. Calendar -->
        <div class="app-icon-card card-calendar" @click="emit('openApp', 'calendar')">
          <div class="app-icon-wrapper theme-calendar">
            <Calendar :size="32" class="app-svg" />
          </div>
          <div class="app-info">
            <div class="app-name">任务日历</div>
            <div class="app-desc">月周日视图与节假日</div>
          </div>
        </div>

        <!-- 3. Local Clock -->
        <div class="app-icon-card card-clock" @click="emit('openApp', 'local-clock')">
          <div class="app-icon-wrapper theme-clock">
            <Clock :size="32" class="app-svg" />
          </div>
          <div class="app-info">
            <div class="app-name">本地时钟</div>
            <div class="app-desc">高精度表盘与世界时区</div>
          </div>
        </div>

        <!-- 4. Countdown -->
        <div class="app-icon-card card-countdown" @click="emit('openApp', 'countdown')">
          <div class="app-icon-wrapper theme-countdown">
            <Hourglass :size="32" class="app-svg" />
          </div>
          <div class="app-info">
            <div class="app-name">倒计时</div>
            <div class="app-desc">多任务定时提醒与声音</div>
          </div>
        </div>

        <!-- 5. Alarm -->
        <div class="app-icon-card card-alarm" @click="emit('openApp', 'alarm')">
          <div class="app-icon-wrapper theme-alarm">
            <Bell :size="32" class="app-svg" />
          </div>
          <div class="app-info">
            <div class="app-name">闹钟</div>
            <div class="app-desc">智能调休与多周期响铃</div>
          </div>
        </div>

        <!-- 6. Pomodoro -->
        <div class="app-icon-card card-pomodoro" @click="emit('openApp', 'pomodoro')">
          <div class="app-icon-wrapper theme-pomodoro">
            <Flame :size="32" class="app-svg" />
          </div>
          <div class="app-info">
            <div class="app-name">番茄时钟</div>
            <div class="app-desc">25+5 分钟高效专注流</div>
          </div>
        </div>

        <!-- 7. Settings -->
        <div class="app-icon-card card-settings" @click="emit('openApp', 'settings')">
          <div class="app-icon-wrapper theme-settings">
            <Settings :size="32" class="app-svg" />
          </div>
          <div class="app-info">
            <div class="app-name">系统设置</div>
            <div class="app-desc">主题外观、音效与账号</div>
          </div>
        </div>
      </div>

      <!-- 3. Desktop Glance Widgets -->
      <div class="desktop-widgets-row">
        <!-- Widget Left: Quick Todo Card -->
        <div class="glance-widget-card todo-glance-card">
          <div class="widget-header">
            <div class="widget-title">
              <CheckSquare :size="16" class="widget-icon" />
              <span>待办速览 ({{ pendingTodos.length }} 项未完成)</span>
            </div>
            <button class="btn-widget-action" @click="emit('openAddTodo')">
              <Plus :size="13" /> 新建任务
            </button>
          </div>

          <div class="widget-body">
            <div v-if="pendingTodos.length === 0" class="widget-empty">
              <Sparkles :size="24" class="empty-icon" />
              <p>今日任务均已完成，保持好心情！</p>
            </div>
            <div v-else class="widget-todo-list">
              <div
                v-for="item in pendingTodos.slice(0, 4)"
                :key="item.id"
                class="widget-todo-item"
                @click="emit('openApp', 'todos')"
              >
                <span class="todo-dot" :class="'prio-' + item.priority"></span>
                <span class="todo-title-text">{{ item.title }}</span>
                <span class="todo-cat-tag">{{ item.category }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Widget Right: Productivity Status -->
        <div class="glance-widget-card system-glance-card">
          <div class="widget-header">
            <div class="widget-title">
              <Flame :size="16" class="widget-icon flame" />
              <span>专注与效率概览</span>
            </div>
            <button class="btn-widget-action" @click="emit('openApp', 'pomodoro')">
              进入番茄钟 <ChevronRight :size="13" />
            </button>
          </div>

          <div class="widget-body productivity-body">
            <div class="prod-stat-box" @click="emit('openApp', 'pomodoro')">
              <span class="prod-val">{{ pomoCount }}</span>
              <span class="prod-lbl">今日番茄数</span>
            </div>
            <div class="prod-stat-box" @click="emit('openApp', 'calendar')">
              <span class="prod-val">{{ todayDateNum }}</span>
              <span class="prod-lbl">今日日期 ({{ todayWeekStr }})</span>
            </div>
            <div class="prod-stat-box" @click="emit('openApp', 'todos')">
              <span class="prod-val">{{ highPrioCount }}</span>
              <span class="prod-lbl">高优先级事项</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import {
  CheckSquare, Calendar, Clock, Flame, Settings,
  Hourglass, Bell, Plus, LayoutGrid, ChevronRight, Sparkles, User
} from 'lucide-vue-next'
import type { Todo, User as UserType } from '../../types'
import { getLunar } from '../../utils/lunar'

const props = defineProps<{
  todos?: Todo[]
  currentUser?: UserType | null
}>()

const emit = defineEmits<{
  (e: 'openApp', tab: 'todos' | 'calendar' | 'local-clock' | 'countdown' | 'alarm' | 'pomodoro' | 'settings'): void
  (e: 'openAddTodo'): void
  (e: 'openLogin'): void
}>()

const todos = computed(() => props.todos || [])
const pendingTodos = computed(() => todos.value.filter(t => !t.completed))
const pendingCount = computed(() => pendingTodos.value.length)
const highPrioCount = computed(() => todos.value.filter(t => !t.completed && t.priority === 'high').length)
const pomoCount = ref(Number(localStorage.getItem('pomo_completed_count') || '0'))

// Live Clock State
const now = ref(new Date())
let timer: any = null

onMounted(() => {
  timer = setInterval(() => {
    now.value = new Date()
  }, 1000)
})

onUnmounted(() => {
  if (timer) clearInterval(timer)
})

const timeHours = computed(() => String(now.value.getHours()).padStart(2, '0'))
const timeMinutes = computed(() => String(now.value.getMinutes()).padStart(2, '0'))
const timeSeconds = computed(() => String(now.value.getSeconds()).padStart(2, '0'))

const todayDateNum = computed(() => now.value.getDate())
const weekLabels = ['日', '一', '二', '三', '四', '五', '六']
const todayWeekStr = computed(() => '周' + weekLabels[now.value.getDay()])

const greetingText = computed(() => {
  const h = now.value.getHours()
  if (h >= 5 && h < 12) return '早上好'
  if (h >= 12 && h < 14) return '中午好'
  if (h >= 14 && h < 18) return '下午好'
  return '晚上好'
})

const dateFullString = computed(() => {
  const y = now.value.getFullYear()
  const m = now.value.getMonth() + 1
  const d = now.value.getDate()
  return `${y}年${m}月${d}日 ${todayWeekStr.value}`
})

const lunarString = computed(() => {
  try {
    const l = getLunar(now.value)
    return l.fullText || `${l.lunarMonthName}${l.lunarDayName}`
  } catch {
    return ''
  }
})
</script>

<style scoped>
.desktop-view-container {
  position: relative;
  width: 100%;
  height: 100%;
  min-height: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  overflow-y: auto;
  padding: 32px 24px;
  box-sizing: border-box;
}

.desktop-bg-glow {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 380px;
  background: radial-gradient(circle at 50% 10%, rgba(59, 130, 246, 0.12), transparent 70%);
  pointer-events: none;
  z-index: 0;
}

.desktop-workspace {
  position: relative;
  z-index: 1;
  width: 100%;
  max-width: 1060px;
  display: flex;
  flex-direction: column;
  gap: 28px;
}

/* 1. Hero Banner */
.desktop-hero-banner {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 20px;
  padding: 24px 32px;
  background: var(--bg-surface, #ffffff);
  border: 1px solid var(--border-color, #e2e8f0);
  border-radius: 20px;
  box-shadow: 0 10px 30px -5px rgba(0, 0, 0, 0.05);
}

.hero-clock-block {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.hero-time-digits {
  display: flex;
  align-items: baseline;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-weight: 800;
  letter-spacing: -1px;
}

.digit-hours, .digit-minutes {
  font-size: 48px;
  color: var(--text-main, #1e293b);
  line-height: 1;
}

.time-colon {
  font-size: 42px;
  color: var(--primary, #3b82f6);
  margin: 0 4px;
  animation: pulse-colon 1.5s infinite;
}

@keyframes pulse-colon {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}

.digit-seconds {
  font-size: 20px;
  color: var(--text-muted, #64748b);
  margin-left: 8px;
  font-weight: 600;
}

.hero-date-row {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: var(--text-muted, #64748b);
}

.date-greeting {
  font-weight: 600;
  color: var(--primary, #3b82f6);
}

.date-sep {
  opacity: 0.5;
}

.hero-actions-group {
  display: flex;
  align-items: center;
  gap: 12px;
}

.hero-user-pill {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 14px;
  background: var(--bg-app, #f8fafc);
  border: 1px solid var(--border-color, #e2e8f0);
  border-radius: 14px;
  cursor: pointer;
  transition: all 0.2s ease;
  user-select: none;
}

.hero-user-pill:hover {
  background: rgba(59, 130, 246, 0.08);
  border-color: var(--primary, #3b82f6);
  transform: translateY(-2px);
}

.user-avatar-dot {
  width: 26px;
  height: 26px;
  border-radius: 50%;
  background: rgba(100, 116, 139, 0.15);
  color: var(--text-muted, #64748b);
  display: flex;
  align-items: center;
  justify-content: center;
}

.user-avatar-dot.is-logged-in {
  background: rgba(16, 185, 129, 0.15);
  color: #059669;
}

.user-name-text {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-main, #1e293b);
  max-width: 100px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.hero-summary-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 12px 20px;
  background: rgba(59, 130, 246, 0.06);
  border: 1px solid rgba(59, 130, 246, 0.15);
  border-radius: 14px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.hero-summary-card:hover {
  background: rgba(59, 130, 246, 0.12);
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(59, 130, 246, 0.12);
}

.summary-icon-box {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  background: var(--primary, #3b82f6);
  color: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
}

.summary-text-box {
  display: flex;
  flex-direction: column;
}

.summary-number-row {
  display: flex;
  align-items: baseline;
  gap: 4px;
}

.num-highlight {
  font-size: 22px;
  font-weight: 700;
  color: var(--text-main, #1e293b);
}

.num-total {
  font-size: 13px;
  color: var(--text-muted, #64748b);
}

.summary-label {
  font-size: 12px;
  color: var(--text-muted, #64748b);
}

/* 2. Desktop Apps Launcher Grid */
.desktop-section-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: -12px;
}

.section-title-tag {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  font-weight: 700;
  color: var(--text-main, #1e293b);
}

.section-subtitle {
  font-size: 12px;
  color: var(--text-muted, #64748b);
}

.desktop-apps-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(130px, 1fr));
  gap: 20px;
}

.app-icon-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: 18px 12px;
  background: var(--bg-surface, #ffffff);
  border: 1px solid var(--border-color, #e2e8f0);
  border-radius: 18px;
  cursor: pointer;
  user-select: none;
  transition: all 0.25s cubic-bezier(0.34, 1.56, 0.64, 1);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.03);
}

.app-icon-card:hover {
  transform: translateY(-6px) scale(1.03);
  box-shadow: 0 14px 28px -6px rgba(0, 0, 0, 0.1);
  border-color: var(--primary, #3b82f6);
}

.app-icon-card:active {
  transform: scale(0.96);
}

.app-icon-wrapper {
  position: relative;
  width: 64px;
  height: 64px;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 12px;
  color: #ffffff;
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.12);
  transition: transform 0.2s ease;
}

.app-icon-card:hover .app-icon-wrapper {
  transform: scale(1.06);
}

/* Vibrant App Gradients */
.theme-todos { background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%); }
.theme-calendar { background: linear-gradient(135deg, #10b981 0%, #047857 100%); }
.theme-clock { background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); }
.theme-countdown { background: linear-gradient(135deg, #8b5cf6 0%, #6d28d9 100%); }
.theme-alarm { background: linear-gradient(135deg, #ec4899 0%, #be185d 100%); }
.theme-pomodoro { background: linear-gradient(135deg, #ef4444 0%, #b91c1c 100%); }
.theme-settings { background: linear-gradient(135deg, #64748b 0%, #334155 100%); }

.app-badge-pill {
  position: absolute;
  top: -4px;
  right: -4px;
  background: #ef4444;
  color: #ffffff;
  font-size: 11px;
  font-weight: 700;
  padding: 2px 6px;
  border-radius: 10px;
  border: 2px solid #ffffff;
  box-shadow: 0 2px 6px rgba(239, 68, 68, 0.4);
}

.app-info {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.app-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-main, #1e293b);
}

.app-desc {
  font-size: 11px;
  color: var(--text-muted, #64748b);
  line-height: 1.3;
}

/* 3. Desktop Glance Widgets */
.desktop-widgets-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

@media (max-width: 768px) {
  .desktop-widgets-row {
    grid-template-columns: 1fr;
  }
}

.glance-widget-card {
  background: var(--bg-surface, #ffffff);
  border: 1px solid var(--border-color, #e2e8f0);
  border-radius: 18px;
  padding: 18px 20px;
  display: flex;
  flex-direction: column;
  gap: 14px;
  box-shadow: 0 4px 14px rgba(0, 0, 0, 0.03);
}

.widget-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.widget-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 700;
  color: var(--text-main, #1e293b);
}

.widget-icon {
  color: var(--primary, #3b82f6);
}

.widget-icon.flame {
  color: #ef4444;
}

.btn-widget-action {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: var(--primary, #3b82f6);
  background: rgba(59, 130, 246, 0.08);
  border: none;
  border-radius: 8px;
  padding: 4px 10px;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.2s ease;
}

.btn-widget-action:hover {
  background: rgba(59, 130, 246, 0.16);
}

.widget-body {
  flex: 1;
}

.widget-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 24px 0;
  color: var(--text-muted, #64748b);
  font-size: 13px;
  gap: 8px;
}

.widget-empty .empty-icon {
  color: #10b981;
}

.widget-todo-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.widget-todo-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  background: var(--bg-app, #f8fafc);
  border-radius: 10px;
  cursor: pointer;
  transition: background 0.15s ease;
}

.widget-todo-item:hover {
  background: rgba(59, 130, 246, 0.08);
}

.todo-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.todo-dot.prio-high { background-color: #ef4444; }
.todo-dot.prio-medium { background-color: #f59e0b; }
.todo-dot.prio-low { background-color: #10b981; }

.todo-title-text {
  flex: 1;
  font-size: 13px;
  color: var(--text-main, #1e293b);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.todo-cat-tag {
  font-size: 11px;
  padding: 2px 8px;
  background: rgba(0, 0, 0, 0.05);
  color: var(--text-muted, #64748b);
  border-radius: 6px;
}

.productivity-body {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
}

.prod-stat-box {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 12px 8px;
  background: var(--bg-app, #f8fafc);
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
  text-align: center;
}

.prod-stat-box:hover {
  background: rgba(59, 130, 246, 0.08);
  transform: translateY(-2px);
}

.prod-val {
  font-size: 20px;
  font-weight: 800;
  color: var(--text-main, #1e293b);
}

.prod-lbl {
  font-size: 11px;
  color: var(--text-muted, #64748b);
  margin-top: 4px;
}
</style>

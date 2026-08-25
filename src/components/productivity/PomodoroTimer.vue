<template>
  <div class="pomodoro-container animate-fade-in">
    <div class="pure-list-workspace">
      <!-- Top Toolbar (Filters, Search, Stats, Actions) -->
      <div class="toolbar">
        <div class="filter-group">
          <button
            class="filter-btn"
            :class="{ active: currentFilter === 'all' }"
            @click="currentFilter = 'all'"
          >
            全部 ({{ pomodoroList.length }})
          </button>
          <button
            class="filter-btn"
            :class="{ active: currentFilter === 'running' }"
            @click="currentFilter = 'running'"
          >
            专注中 ({{ runningCount }})
          </button>
          <button
            class="filter-btn"
            :class="{ active: currentFilter === 'completed' }"
            @click="currentFilter = 'completed'"
          >
            已达标 ({{ completedCount }})
          </button>
        </div>

        <div class="toolbar-right">
          <div class="search-box">
            <Search :size="14" class="search-icon" />
            <input
              type="text"
              v-model="searchKeyword"
              placeholder="搜索番茄任务..."
            />
          </div>

          <button class="btn btn-outline" @click="showDurationModal = true" title="配置默认时长">
            <Sliders :size="14" /> 默认时长
          </button>

          <button class="btn btn-primary" @click="openAddModal">
            <Plus :size="14" /> 新建专注任务
          </button>
        </div>
      </div>

      <!-- Stats Summary Banner -->
      <div class="stats-banner-row">
        <div class="stats-pill">
          <Flame :size="14" class="icon-flame" />
          <span>今日已完成 <strong>{{ totalCompletedTomatoes }}</strong> 个番茄</span>
        </div>
        <div class="stats-pill">
          <Clock :size="14" class="icon-clock" />
          <span>累计高效专注 <strong>{{ totalFocusMinutes }}</strong> 分钟</span>
        </div>
        <button class="clear-stats-btn" @click="clearStats" title="重置今日统计数据">
          <Trash2 :size="12" /> 重置今日统计
        </button>
      </div>

      <!-- Pomodoro Task List Area -->
      <div class="list-scroll-area">
        <div v-if="filteredList.length === 0" class="empty-state">
          <div class="empty-icon"><Flame :size="42" :stroke-width="1.5" /></div>
          <p class="empty-text">暂无番茄专注任务，点击右上角 "+ 新建专注任务" 开启高效时刻！</p>
        </div>

        <div v-else class="items-grid">
          <div
            v-for="task in filteredList"
            :key="task.id"
            class="list-card-item animate-fade-in"
            :class="{ running: task.isRunning, completed: task.completedTomatoes >= task.targetTomatoes }"
          >
            <div class="card-left-indicator">
              <div class="mini-pomo-icon" :class="{ running: task.isRunning, done: task.completedTomatoes >= task.targetTomatoes }">
                <Flame :size="20" />
              </div>
            </div>

            <div class="card-body">
              <div class="card-title-row">
                <span class="card-title">{{ task.title }}</span>
                <span class="tag tag-cat"><Folder :size="11" /> {{ task.category || '专注' }}</span>
                <span class="mode-tag" :class="task.mode">
                  {{ task.mode === 'focus' ? '深度专注' : task.mode === 'shortBreak' ? '短休' : '长休' }}
                </span>
                <span class="status-tag" :class="{ running: task.isRunning, finished: task.completedTomatoes >= task.targetTomatoes }">
                  <span class="dot"></span>
                  {{ task.isRunning ? '专注计时中' : task.completedTomatoes >= task.targetTomatoes ? '目标达成' : '待开启' }}
                </span>
              </div>

              <div class="card-time-row">
                <span class="digits-time">{{ formatTime(task.remainingSeconds) }}</span>
                <span class="digits-sub">/ {{ task.focusMinutes }} 分钟</span>
                <div class="tomatoes-counter">
                  <span class="tomato-icons">
                    <span v-for="n in Math.min(8, task.completedTomatoes)" :key="'t'+n" class="tomato-icon">🍅</span>
                  </span>
                  <span class="tomato-text">进度 {{ task.completedTomatoes }}/{{ task.targetTomatoes }} 目标</span>
                </div>
              </div>

              <!-- Progress Track -->
              <div class="item-progress-track">
                <div
                  class="item-progress-bar"
                  :class="{ running: task.isRunning, done: task.completedTomatoes >= task.targetTomatoes }"
                  :style="{ width: `${((task.focusMinutes * 60 - task.remainingSeconds) / (task.focusMinutes * 60 || 1)) * 100}%` }"
                ></div>
              </div>
            </div>

            <div class="card-actions">
              <button
                class="btn-action-primary"
                :class="{ running: task.isRunning }"
                @click="toggleTask(task)"
                :title="task.isRunning ? '暂停专注' : '开启专注'"
              >
                <Pause v-if="task.isRunning" :size="14" />
                <Play v-else :size="14" />
                <span>{{ task.isRunning ? '暂停' : '开启' }}</span>
              </button>

              <button
                class="icon-btn-action plus-tomato"
                @click="manualAddTomato(task)"
                title="快速打卡 +1 个番茄"
              >
                +🍅
              </button>

              <button
                class="icon-btn-action reset"
                @click="resetTask(task)"
                title="重置当前计时"
              >
                <RotateCcw :size="14" />
              </button>

              <button
                class="icon-btn-action edit"
                @click="openEditModal(task)"
                title="编辑任务"
              >
                <Sliders :size="14" />
              </button>

              <button
                class="icon-btn-action delete"
                @click="deleteTask(task.id)"
                title="删除任务"
              >
                <Trash2 :size="14" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Modal: Add / Edit Pomodoro Task -->
    <div v-if="showTaskModal" class="modal-backdrop" @click.self="showTaskModal = false">
      <div class="modal-card animate-scale-up">
        <div class="modal-header">
          <h3><Flame :size="18" /> {{ editingTaskId ? '编辑番茄任务' : '新建番茄任务' }}</h3>
          <button class="icon-btn-close" @click="showTaskModal = false"><X :size="16" /></button>
        </div>

        <div class="modal-body">
          <div class="form-group">
            <label class="form-label">任务名称 *</label>
            <input
              type="text"
              v-model="taskForm.title"
              class="text-input"
              placeholder="例如: 编写核心功能模块 / 阅读技术白皮书"
            />
          </div>

          <div class="form-group">
            <label class="form-label">任务分类</label>
            <input
              type="text"
              v-model="taskForm.category"
              class="text-input"
              placeholder="例如: 工作 / 学习 / 研发"
            />
          </div>

          <div class="form-row-2">
            <div class="form-group flex-1">
              <label class="form-label">单次专注时长 (分钟)</label>
              <input type="number" v-model.number="taskForm.focusMinutes" min="1" max="180" class="text-input" />
            </div>

            <div class="form-group flex-1">
              <label class="form-label">目标番茄数 (个)</label>
              <input type="number" v-model.number="taskForm.targetTomatoes" min="1" max="50" class="text-input" />
            </div>
          </div>
        </div>

        <div class="modal-footer">
          <button class="btn btn-outline" @click="showTaskModal = false">取消</button>
          <button class="btn btn-primary" @click="saveTaskModal">
            <Check :size="14" /> 保存任务
          </button>
        </div>
      </div>
    </div>

    <!-- Modal: Default Duration Settings -->
    <div v-if="showDurationModal" class="modal-backdrop" @click.self="showDurationModal = false">
      <div class="modal-card animate-scale-up">
        <div class="modal-header">
          <h3><Sliders :size="18" /> 默认番茄时长配置</h3>
          <button class="icon-btn-close" @click="showDurationModal = false"><X :size="16" /></button>
        </div>

        <div class="modal-body">
          <div class="form-group">
            <label class="form-label"><Flame :size="14" /> 默认专注模式时长 (分钟)</label>
            <input type="number" v-model.number="tempModeMinutes.focus" min="1" max="180" class="text-input" />
          </div>

          <div class="form-group">
            <label class="form-label"><Coffee :size="14" /> 默认短休时长 (分钟)</label>
            <input type="number" v-model.number="tempModeMinutes.shortBreak" min="1" max="60" class="text-input" />
          </div>

          <div class="form-group">
            <label class="form-label"><Smile :size="14" /> 默认长休时长 (分钟)</label>
            <input type="number" v-model.number="tempModeMinutes.longBreak" min="1" max="120" class="text-input" />
          </div>
        </div>

        <div class="modal-footer">
          <button class="btn btn-outline" @click="showDurationModal = false">取消</button>
          <button class="btn btn-primary" @click="saveCustomDurations">
            <Check :size="14" /> 保存默认时长
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import {
  Play, Pause, RotateCcw, Flame, Coffee, Smile,
  Sliders, Trash2, Clock, Plus, Search, Check, X, Folder
} from 'lucide-vue-next'
import { soundPlayer, type SoundType } from '../../utils/audio'
import { showConfirm } from '../../utils/confirmState'

const props = defineProps<{
  soundType?: SoundType
  soundVolume?: number
}>()

export interface PomodoroItem {
  id: string
  title: string
  category: string
  focusMinutes: number
  remainingSeconds: number
  completedTomatoes: number
  targetTomatoes: number
  mode: 'focus' | 'shortBreak' | 'longBreak'
  isRunning: boolean
}

// Global default durations
const modeMinutes = ref<{ focus: number; shortBreak: number; longBreak: number }>({
  focus: Number(localStorage.getItem('pomo_min_focus') || '25'),
  shortBreak: Number(localStorage.getItem('pomo_min_short') || '5'),
  longBreak: Number(localStorage.getItem('pomo_min_long') || '15')
})

const defaultPomodoroTasks: PomodoroItem[] = [
  {
    id: 'pomo-1',
    title: '系统核心功能代码编写与重构',
    category: '工作',
    focusMinutes: 25,
    remainingSeconds: 25 * 60,
    completedTomatoes: 2,
    targetTomatoes: 4,
    mode: 'focus',
    isRunning: false
  },
  {
    id: 'pomo-2',
    title: '深度阅读与技术方案设计',
    category: '学习',
    focusMinutes: 30,
    remainingSeconds: 30 * 60,
    completedTomatoes: 1,
    targetTomatoes: 3,
    mode: 'focus',
    isRunning: false
  },
  {
    id: 'pomo-3',
    title: '团队沟通与每日任务梳理',
    category: '常规',
    focusMinutes: 15,
    remainingSeconds: 15 * 60,
    completedTomatoes: 2,
    targetTomatoes: 2,
    mode: 'focus',
    isRunning: false
  }
]

const pomodoroList = ref<PomodoroItem[]>(
  JSON.parse(localStorage.getItem('todo_pro_pomodoro_list') || 'null') || defaultPomodoroTasks
)

const currentFilter = ref<'all' | 'running' | 'completed'>('all')
const searchKeyword = ref('')
const totalCompletedTomatoes = ref(Number(localStorage.getItem('pomo_completed_count') || '5'))

const totalFocusMinutes = computed(() => {
  return totalCompletedTomatoes.value * modeMinutes.value.focus
})

const runningCount = computed(() => pomodoroList.value.filter(i => i.isRunning).length)
const completedCount = computed(() => pomodoroList.value.filter(i => i.completedTomatoes >= i.targetTomatoes).length)

watch(pomodoroList, (newVal) => {
  const serializable = newVal.map(item => ({
    id: item.id,
    title: item.title,
    category: item.category,
    focusMinutes: item.focusMinutes,
    remainingSeconds: item.remainingSeconds,
    completedTomatoes: item.completedTomatoes,
    targetTomatoes: item.targetTomatoes,
    mode: item.mode,
    isRunning: item.isRunning
  }))
  localStorage.setItem('todo_pro_pomodoro_list', JSON.stringify(serializable))
}, { deep: true })

const filteredList = computed(() => {
  return pomodoroList.value.filter(item => {
    if (currentFilter.value === 'running' && !item.isRunning) return false
    if (currentFilter.value === 'completed' && item.completedTomatoes < item.targetTomatoes) return false
    if (searchKeyword.value.trim()) {
      const q = searchKeyword.value.trim().toLowerCase()
      const matchTitle = item.title.toLowerCase().includes(q)
      const matchCat = (item.category || '').toLowerCase().includes(q)
      if (!matchTitle && !matchCat) return false
    }
    return true
  })
})

// Modal states
const showTaskModal = ref(false)
const editingTaskId = ref<string | null>(null)
const taskForm = ref({
  title: '',
  category: '工作',
  focusMinutes: 25,
  targetTomatoes: 4
})

const showDurationModal = ref(false)
const tempModeMinutes = ref({ ...modeMinutes.value })

let globalInterval: any = null

function updateGlobalTimer() {
  const hasRunning = pomodoroList.value.some(t => t.isRunning)
  if (hasRunning && !globalInterval) {
    globalInterval = setInterval(() => {
      let stillRunning = false
      pomodoroList.value.forEach(task => {
        if (task.isRunning) {
          if (task.remainingSeconds > 0) {
            task.remainingSeconds--
            stillRunning = true
          } else {
            task.isRunning = false
            onTaskTimerFinished(task)
          }
        }
      })
      if (!stillRunning && globalInterval) {
        clearInterval(globalInterval)
        globalInterval = null
      }
    }, 1000)
  } else if (!hasRunning && globalInterval) {
    clearInterval(globalInterval)
    globalInterval = null
  }
}

function onTaskTimerFinished(task: PomodoroItem) {
  task.completedTomatoes++
  totalCompletedTomatoes.value++
  localStorage.setItem('pomo_completed_count', String(totalCompletedTomatoes.value))

  soundPlayer.play((props.soundType as SoundType) || 'chime', props.soundVolume ?? 0.8)

  if (task.completedTomatoes % 4 === 0) {
    task.mode = 'longBreak'
    task.remainingSeconds = modeMinutes.value.longBreak * 60
  } else {
    task.mode = 'shortBreak'
    task.remainingSeconds = modeMinutes.value.shortBreak * 60
  }
}

function toggleTask(task: PomodoroItem) {
  if (task.remainingSeconds <= 0) {
    task.remainingSeconds = task.focusMinutes * 60
  }
  task.isRunning = !task.isRunning
  updateGlobalTimer()
}

function manualAddTomato(task: PomodoroItem) {
  task.completedTomatoes++
  totalCompletedTomatoes.value++
  localStorage.setItem('pomo_completed_count', String(totalCompletedTomatoes.value))
}

function resetTask(task: PomodoroItem) {
  const target = pomodoroList.value.find(t => t.id === task.id) || task
  target.isRunning = false
  target.mode = 'focus'
  const mins = Number(target.focusMinutes) || modeMinutes.value.focus || 25
  target.focusMinutes = mins
  target.remainingSeconds = mins * 60
  updateGlobalTimer()
}

function openAddModal() {
  editingTaskId.value = null
  taskForm.value = {
    title: '',
    category: '工作',
    focusMinutes: modeMinutes.value.focus,
    targetTomatoes: 4
  }
  showTaskModal.value = true
}

function openEditModal(task: PomodoroItem) {
  editingTaskId.value = task.id
  taskForm.value = {
    title: task.title,
    category: task.category || '工作',
    focusMinutes: task.focusMinutes,
    targetTomatoes: task.targetTomatoes
  }
  showTaskModal.value = true
}

function saveTaskModal() {
  const title = taskForm.value.title.trim()
  if (!title) return

  if (editingTaskId.value) {
    const idx = pomodoroList.value.findIndex(t => t.id === editingTaskId.value)
    if (idx !== -1) {
      pomodoroList.value[idx].title = title
      pomodoroList.value[idx].category = taskForm.value.category.trim()
      pomodoroList.value[idx].focusMinutes = taskForm.value.focusMinutes
      pomodoroList.value[idx].targetTomatoes = taskForm.value.targetTomatoes
    }
  } else {
    const newTask: PomodoroItem = {
      id: 'pomo_' + Date.now(),
      title,
      category: taskForm.value.category.trim() || '工作',
      focusMinutes: taskForm.value.focusMinutes,
      remainingSeconds: taskForm.value.focusMinutes * 60,
      completedTomatoes: 0,
      targetTomatoes: taskForm.value.targetTomatoes,
      mode: 'focus',
      isRunning: false
    }
    pomodoroList.value.unshift(newTask)
  }

  showTaskModal.value = false
}

async function deleteTask(id: string) {
  const confirmed = await showConfirm({
    title: '删除番茄任务',
    message: '确定要删除该番茄任务吗？',
    confirmText: '确认删除',
    type: 'danger'
  })
  if (!confirmed) return

  pomodoroList.value = pomodoroList.value.filter(t => t.id !== id)
  updateGlobalTimer()
}

function saveCustomDurations() {
  modeMinutes.value = { ...tempModeMinutes.value }
  localStorage.setItem('pomo_min_focus', String(modeMinutes.value.focus))
  localStorage.setItem('pomo_min_short', String(modeMinutes.value.shortBreak))
  localStorage.setItem('pomo_min_long', String(modeMinutes.value.longBreak))
  showDurationModal.value = false
}

async function clearStats() {
  const confirmed = await showConfirm({
    title: '清空统计数据',
    message: '确定要重置今日的番茄数与专注时长吗？',
    confirmText: '确认重置',
    type: 'danger'
  })
  if (!confirmed) return
  totalCompletedTomatoes.value = 0
  localStorage.setItem('pomo_completed_count', '0')
}

function formatTime(totalSec: number): string {
  const m = Math.floor(totalSec / 60)
  const s = totalSec % 60
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
}

onMounted(() => {
  updateGlobalTimer()
})

onUnmounted(() => {
  if (globalInterval) clearInterval(globalInterval)
})
</script>

<style scoped>
.pomodoro-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: 20px 24px;
  box-sizing: border-box;
  overflow-y: auto;
}

.pure-list-workspace {
  display: flex;
  flex-direction: column;
  height: 100%;
  width: 100%;
  max-width: 960px;
  margin: 0 auto;
  gap: 16px;
}

/* Toolbar */
.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}

.filter-group {
  display: flex;
  align-items: center;
  gap: 6px;
}

.filter-btn {
  font-size: 12.5px;
  padding: 6px 14px;
  border-radius: 8px;
  border: 1px solid var(--border-color, #e2e8f0);
  background-color: var(--bg-surface, #ffffff);
  color: var(--text-main, #0f172a);
  cursor: pointer;
  font-weight: 500;
  transition: all 0.2s ease;
}

.filter-btn:hover {
  border-color: var(--primary, #3b82f6);
  color: var(--primary, #3b82f6);
}

.filter-btn.active {
  background-color: var(--primary, #3b82f6);
  color: #ffffff;
  border-color: var(--primary, #3b82f6);
  font-weight: 600;
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.25);
}

.toolbar-right {
  display: flex;
  align-items: center;
  gap: 10px;
}

.search-box {
  position: relative;
  display: flex;
  align-items: center;
}

.search-icon {
  position: absolute;
  left: 10px;
  color: var(--text-muted, #94a3b8);
}

.search-box input {
  padding: 6px 12px 6px 32px;
  border-radius: 8px;
  border: 1px solid var(--border-color, #e2e8f0);
  background: var(--bg-surface, #ffffff);
  color: var(--text-main, #0f172a);
  font-size: 12.5px;
  outline: none;
  width: 180px;
  transition: all 0.2s ease;
}

.search-box input:focus {
  border-color: var(--primary, #3b82f6);
  width: 210px;
}

/* Stats Banner Row */
.stats-banner-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 16px;
  background: var(--bg-surface, #f8fafc);
  border: 1px solid var(--border-color, #e2e8f0);
  border-radius: 10px;
  flex-wrap: wrap;
}

.stats-pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 12.5px;
  color: var(--text-main, #1e293b);
}

.icon-flame {
  color: #ef4444;
}

.icon-clock {
  color: var(--primary, #3b82f6);
}

.clear-stats-btn {
  margin-left: auto;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 11.5px;
  color: var(--text-muted, #94a3b8);
  background: transparent;
  border: none;
  cursor: pointer;
  transition: color 0.2s;
}

.clear-stats-btn:hover {
  color: #ef4444;
}

/* List & Cards */
.list-scroll-area {
  flex: 1;
  overflow-y: auto;
  padding-right: 4px;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 320px;
  color: var(--text-muted, #94a3b8);
  gap: 12px;
}

.items-grid {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.list-card-item {
  position: relative;
  display: flex;
  align-items: center;
  padding: 14px 18px;
  background-color: var(--bg-card, #ffffff);
  border: 1px solid var(--border-color, #e2e8f0);
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.03);
  gap: 16px;
  transition: all 0.2s ease;
}

.list-card-item:hover {
  border-color: var(--primary, #3b82f6);
  box-shadow: 0 6px 16px rgba(59, 130, 246, 0.08);
  transform: translateY(-1px);
}

.list-card-item.running {
  border-color: #ef4444;
  background: linear-gradient(135deg, var(--bg-card, #ffffff) 0%, rgba(239, 68, 68, 0.03) 100%);
}

.list-card-item.completed {
  opacity: 0.85;
}

.card-left-indicator {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.mini-pomo-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background: var(--bg-surface, #f8fafc);
  border: 1px solid var(--border-color, #e2e8f0);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #ef4444;
  transition: all 0.2s ease;
}

.mini-pomo-icon.running {
  background: rgba(239, 68, 68, 0.12);
  border-color: rgba(239, 68, 68, 0.35);
  box-shadow: 0 0 12px rgba(239, 68, 68, 0.2);
  animation: pulse 1.5s infinite;
}

.mini-pomo-icon.done {
  background: rgba(16, 185, 129, 0.1);
  color: #10b981;
  border-color: rgba(16, 185, 129, 0.3);
}

.card-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 0;
}

.card-title-row {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.card-title {
  font-size: 14.5px;
  font-weight: 600;
  color: var(--text-main, #0f172a);
}

.tag-cat {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 6px;
  background: var(--bg-surface, #f8fafc);
  border: 1px solid var(--border-color, #e2e8f0);
  color: var(--text-muted, #64748b);
}

.mode-tag {
  font-size: 11px;
  font-weight: 600;
  padding: 2px 6px;
  border-radius: 4px;
  background: rgba(59, 130, 246, 0.1);
  color: var(--primary, #3b82f6);
}

.mode-tag.shortBreak,
.mode-tag.longBreak {
  background: rgba(16, 185, 129, 0.1);
  color: #10b981;
}

.status-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 10px;
  background: var(--bg-app, #f1f5f9);
  color: var(--text-muted, #64748b);
}

.status-tag .dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background-color: currentColor;
}

.status-tag.running {
  background: rgba(239, 68, 68, 0.12);
  color: #ef4444;
}

.status-tag.running .dot {
  animation: pulse 1.5s infinite;
}

.status-tag.finished {
  background: rgba(16, 185, 129, 0.12);
  color: #10b981;
}

.card-time-row {
  display: flex;
  align-items: baseline;
  gap: 8px;
  flex-wrap: wrap;
}

.digits-time {
  font-size: 17px;
  font-weight: 700;
  font-family: ui-monospace, SFMono-Regular, monospace;
  font-variant-numeric: tabular-nums;
  color: #ef4444;
}

.digits-sub {
  font-size: 12px;
  color: var(--text-muted, #94a3b8);
}

.tomatoes-counter {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-left: 8px;
}

.tomato-icons {
  font-size: 13px;
  letter-spacing: -1px;
}

.tomato-text {
  font-size: 11.5px;
  font-weight: 600;
  color: var(--text-muted, #64748b);
}

/* Progress bar inside card */
.item-progress-track {
  width: 100%;
  height: 4px;
  background: var(--border-color, #e2e8f0);
  border-radius: 4px;
  overflow: hidden;
  margin-top: 4px;
}

.item-progress-bar {
  height: 100%;
  background: linear-gradient(90deg, #ef4444, #f59e0b);
  transition: width 0.5s ease;
}

.item-progress-bar.done {
  background: #10b981;
}

/* Actions in Card */
.card-actions {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}

.btn-action-primary {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  border-radius: 8px;
  border: none;
  background: #ef4444;
  color: #ffffff;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-action-primary:hover {
  filter: brightness(1.1);
  transform: translateY(-1px);
}

.btn-action-primary.running {
  background: #f59e0b;
}

.icon-btn-action {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 8px;
  border: 1px solid var(--border-color, #e2e8f0);
  background: var(--bg-surface, #ffffff);
  color: var(--text-muted, #64748b);
  cursor: pointer;
  font-size: 12px;
  font-weight: 700;
  transition: all 0.2s ease;
}

.icon-btn-action:hover {
  border-color: var(--primary, #3b82f6);
  color: var(--primary, #3b82f6);
  background: var(--bg-hover, #f8fafc);
}

.icon-btn-action.plus-tomato:hover {
  border-color: #ef4444;
  color: #ef4444;
  background: rgba(239, 68, 68, 0.08);
}

.icon-btn-action.delete:hover {
  border-color: #ef4444;
  color: #ef4444;
  background: rgba(239, 68, 68, 0.08);
}

/* Modal Windows */
.modal-backdrop {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(15, 23, 42, 0.6);
  backdrop-filter: blur(6px);
  z-index: 10000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
}

.modal-card {
  width: 100%;
  max-width: 480px;
  background: var(--bg-card, #ffffff);
  border: 1px solid var(--border-color, #e2e8f0);
  border-radius: 20px;
  box-shadow: 0 24px 48px -12px rgba(0, 0, 0, 0.18);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 18px 22px;
  border-bottom: 1px solid var(--border-color, #e2e8f0);
}

.modal-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 700;
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--text-main, #0f172a);
}

.icon-btn-close {
  background: transparent;
  border: none;
  color: var(--text-muted, #64748b);
  cursor: pointer;
  padding: 4px;
  border-radius: 6px;
}

.modal-body {
  padding: 20px 22px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-row-2 {
  display: flex;
  gap: 12px;
}

.form-label {
  font-size: 12.5px;
  font-weight: 600;
  color: var(--text-main, #1e293b);
  display: flex;
  align-items: center;
  gap: 6px;
}

.text-input {
  width: 100%;
  padding: 9px 12px;
  border-radius: 8px;
  border: 1px solid var(--border-color, #e2e8f0);
  background: var(--bg-surface, #ffffff);
  color: var(--text-main, #0f172a);
  font-size: 13px;
  box-sizing: border-box;
  outline: none;
}

.text-input:focus {
  border-color: var(--primary, #3b82f6);
}

.modal-footer {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 10px;
  padding: 14px 22px;
  border-top: 1px solid var(--border-color, #e2e8f0);
}

@media (max-width: 640px) {
  .toolbar {
    flex-direction: column;
    align-items: stretch;
  }
  .toolbar-right {
    justify-content: space-between;
  }
  .search-box {
    flex: 1;
  }
  .search-box input {
    width: 100%;
  }
  .list-card-item {
    flex-direction: column;
    align-items: stretch;
  }
  .card-actions {
    justify-content: flex-end;
  }
}
</style>

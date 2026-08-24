<template>
  <div class="pomodoro-container animate-fade-in">
    <div class="pomodoro-workspace">
      <!-- Top Mode Tabs Switcher -->
      <div class="mode-tabs">
        <button
          class="mode-btn"
          :class="{ active: currentMode === 'focus' }"
          @click="switchMode('focus')"
        >
          <Flame :size="15" /> 专注模式 ({{ modeMinutes.focus }}m)
        </button>
        <button
          class="mode-btn"
          :class="{ active: currentMode === 'shortBreak' }"
          @click="switchMode('shortBreak')"
        >
          <Coffee :size="15" /> 短暂休息 ({{ modeMinutes.shortBreak }}m)
        </button>
        <button
          class="mode-btn"
          :class="{ active: currentMode === 'longBreak' }"
          @click="switchMode('longBreak')"
        >
          <Smile :size="15" /> 深度休息 ({{ modeMinutes.longBreak }}m)
        </button>
      </div>

      <!-- Main Focus Display Area -->
      <div class="focus-display-section">
        <!-- Time Quick Adjustment Left Buttons -->
        <div class="adjust-group left">
          <button class="btn-adjust" @click="adjustTime(-5)" title="减少5分钟" :disabled="timeLeft <= 300">
            -5m
          </button>
          <button class="btn-adjust" @click="adjustTime(-1)" title="减少1分钟" :disabled="timeLeft <= 60">
            -1m
          </button>
        </div>

        <!-- Circular Progress Ring & Grand Timer Display -->
        <div class="timer-circle-wrapper" :class="{ 'is-active': isRunning }">
          <svg class="progress-ring" width="280" height="280">
            <defs>
              <linearGradient id="focusGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stop-color="#3182CE" />
                <stop offset="100%" stop-color="#805AD5" />
              </linearGradient>
              <linearGradient id="breakGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stop-color="#38A169" />
                <stop offset="100%" stop-color="#319795" />
              </linearGradient>
            </defs>
            <circle
              class="progress-ring-bg"
              stroke-width="12"
              r="124"
              cx="140"
              cy="140"
            />
            <circle
              class="progress-ring-fill"
              stroke-width="12"
              r="124"
              cx="140"
              cy="140"
              :stroke="currentMode === 'focus' ? 'url(#focusGradient)' : 'url(#breakGradient)'"
              :style="progressRingStyle"
            />
          </svg>

          <div class="timer-center-text">
            <span class="time-number">{{ formattedTime }}</span>
            <span class="timer-status-badge" :class="{ running: isRunning }">
              <span class="status-dot"></span>
              {{ isRunning ? (currentMode === 'focus' ? '深度专注中' : '休息放松中') : '准备就绪' }}
            </span>
          </div>
        </div>

        <!-- Time Quick Adjustment Right Buttons -->
        <div class="adjust-group right">
          <button class="btn-adjust" @click="adjustTime(1)" title="增加1分钟">
            +1m
          </button>
          <button class="btn-adjust" @click="adjustTime(5)" title="增加5分钟">
            +5m
          </button>
        </div>
      </div>

      <!-- Control Action Buttons -->
      <div class="controls-row">
        <button class="btn btn-reset" @click="resetTimer" title="重置时间">
          <RotateCcw :size="16" /> 重置
        </button>

        <button
          class="btn btn-toggle-run"
          :class="{ 'is-running': isRunning, 'is-break': currentMode !== 'focus' }"
          @click="toggleTimer"
        >
          <Pause v-if="isRunning" :size="22" />
          <Play v-else :size="22" />
          <span>{{ isRunning ? '暂停计时' : '开启专注' }}</span>
        </button>

        <button class="btn btn-settings-toggle" @click="showDurationModal = true" title="自定义专注与休息时长">
          <Sliders :size="16" /> 自定义时长
        </button>
      </div>

      <!-- Today's Stats Banner -->
      <div class="stats-banner">
        <div class="stat-item">
          <span class="stat-icon"><Flame :size="18" class="icon-flame" /></span>
          <div class="stat-info">
            <span class="stat-val">{{ completedCount }}</span>
            <span class="stat-lbl">今日完成番茄数</span>
          </div>
        </div>

        <div class="stat-item">
          <span class="stat-icon"><Clock :size="18" class="icon-clock" /></span>
          <div class="stat-info">
            <span class="stat-val">{{ totalFocusMinutes }} 分钟</span>
            <span class="stat-lbl">累计专注时长</span>
          </div>
        </div>

        <button class="btn btn-sm btn-outline clear-stats-btn" @click="clearStats" title="清空统计数据">
          <Trash2 :size="12" /> 清空统计
        </button>
      </div>
    </div>

    <!-- Duration Customization Modal -->
    <div v-if="showDurationModal" class="modal-backdrop" @click.self="showDurationModal = false">
      <div class="modal-card animate-fade-in">
        <h3 class="modal-title"><Sliders :size="18" /> 自定义番茄钟时长 (分钟)</h3>

        <div class="form-group">
          <label><Flame :size="14" /> 专注模式时长 (分钟)</label>
          <input type="number" v-model.number="tempModeMinutes.focus" min="1" max="180" />
        </div>

        <div class="form-group">
          <label><Coffee :size="14" /> 短暂休息时长 (分钟)</label>
          <input type="number" v-model.number="tempModeMinutes.shortBreak" min="1" max="60" />
        </div>

        <div class="form-group">
          <label><Smile :size="14" /> 深度休息时长 (分钟)</label>
          <input type="number" v-model.number="tempModeMinutes.longBreak" min="1" max="120" />
        </div>

        <div class="modal-actions">
          <button class="btn" @click="showDurationModal = false">取消</button>
          <button class="btn btn-primary" @click="saveCustomDurations">保存时长配置</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onUnmounted } from 'vue'
import { Play, Pause, RotateCcw, Flame, Coffee, Smile, Sliders, Trash2, Clock } from 'lucide-vue-next'
import { soundPlayer, type SoundType } from '../../utils/audio'
import { showConfirm } from '../../utils/confirmState'

const props = defineProps<{
  soundType?: SoundType
  soundVolume?: number
}>()

type TimerMode = 'focus' | 'shortBreak' | 'longBreak'

// Persistent Mode Durations (in minutes)
const modeMinutes = ref<Record<TimerMode, number>>({
  focus: Number(localStorage.getItem('pomo_min_focus') || '25'),
  shortBreak: Number(localStorage.getItem('pomo_min_short') || '5'),
  longBreak: Number(localStorage.getItem('pomo_min_long') || '15')
})

const currentMode = ref<TimerMode>('focus')
const timeLeft = ref(modeMinutes.value.focus * 60)
const isRunning = ref(false)
const completedCount = ref(Number(localStorage.getItem('pomo_completed_count') || '0'))
const totalFocusMinutes = computed(() => completedCount.value * modeMinutes.value.focus)

let timerId: any = null

// Modal for customizing durations
const showDurationModal = ref(false)
const tempModeMinutes = ref({ ...modeMinutes.value })

const formattedTime = computed(() => {
  const m = Math.floor(timeLeft.value / 60)
  const s = timeLeft.value % 60
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
})

const progressPercent = computed(() => {
  const total = modeMinutes.value[currentMode.value] * 60
  return Math.min(100, Math.max(0, ((total - timeLeft.value) / total) * 100))
})

const progressRingStyle = computed(() => {
  const circumference = 2 * Math.PI * 124
  const strokeDashoffset = circumference - (progressPercent.value / 100) * circumference
  return {
    strokeDasharray: `${circumference} ${circumference}`,
    strokeDashoffset: `${strokeDashoffset}`
  }
})

function switchMode(mode: TimerMode) {
  if (isRunning.value) pauseTimer()
  currentMode.value = mode
  timeLeft.value = modeMinutes.value[mode] * 60
}

function adjustTime(deltaMinutes: number) {
  const newSeconds = timeLeft.value + deltaMinutes * 60
  if (newSeconds >= 10) {
    timeLeft.value = newSeconds
  }
}

function saveCustomDurations() {
  modeMinutes.value = {
    focus: Math.max(1, tempModeMinutes.value.focus || 25),
    shortBreak: Math.max(1, tempModeMinutes.value.shortBreak || 5),
    longBreak: Math.max(1, tempModeMinutes.value.longBreak || 15)
  }
  localStorage.setItem('pomo_min_focus', String(modeMinutes.value.focus))
  localStorage.setItem('pomo_min_short', String(modeMinutes.value.shortBreak))
  localStorage.setItem('pomo_min_long', String(modeMinutes.value.longBreak))

  if (!isRunning.value) {
    timeLeft.value = modeMinutes.value[currentMode.value] * 60
  }
  showDurationModal.value = false
}

function toggleTimer() {
  if (isRunning.value) {
    pauseTimer()
  } else {
    startTimer()
  }
}

function startTimer() {
  if (isRunning.value) return
  isRunning.value = true
  timerId = setInterval(() => {
    if (timeLeft.value > 0) {
      timeLeft.value--
    } else {
      onTimerFinished()
    }
  }, 1000)
}

function pauseTimer() {
  isRunning.value = false
  if (timerId) clearInterval(timerId)
  timerId = null
}

async function resetTimer() {
  if (isRunning.value || timeLeft.value < modeMinutes.value[currentMode.value] * 60) {
    const confirmed = await showConfirm({
      title: '重置番茄钟',
      message: '确定要重置当前的番茄钟倒计时吗？',
      confirmText: '重置计时',
      cancelText: '取消',
      type: 'warning'
    })
    if (!confirmed) return
  }
  pauseTimer()
  timeLeft.value = modeMinutes.value[currentMode.value] * 60
}

async function clearStats() {
  const confirmed = await showConfirm({
    title: '清空专注统计',
    message: '确定要清空累计的番茄钟完成数与专注时长吗？',
    detail: '数据清空后不可恢复。',
    confirmText: '清空统计',
    cancelText: '取消',
    type: 'danger'
  })
  if (!confirmed) return
  completedCount.value = 0
  localStorage.setItem('pomo_completed_count', '0')
}

function onTimerFinished() {
  pauseTimer()
  soundPlayer.play(props.soundType || 'chime', props.soundVolume ?? 0.8)

  if (currentMode.value === 'focus') {
    completedCount.value++
    localStorage.setItem('pomo_completed_count', String(completedCount.value))
    alert(`🎉 恭喜！您已成功完成一次 ${modeMinutes.value.focus} 分钟专注！休息一下吧。`)
    switchMode('shortBreak')
  } else {
    alert('☕ 休息结束！回到专注状态吧。')
    switchMode('focus')
  }
}

onUnmounted(() => {
  pauseTimer()
})
</script>

<style scoped>
.pomodoro-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100%;
  padding: 0;
  width: 100%;
  background: radial-gradient(circle at center, rgba(49, 130, 206, 0.06) 0%, transparent 70%);
}

.pomodoro-workspace {
  width: 100%;
  max-width: 760px;
  background-color: transparent;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 28px;
  padding: 24px;
}

.mode-tabs {
  display: flex;
  gap: 8px;
  background-color: var(--bg-surface);
  padding: 5px;
  border-radius: 20px;
  border: 1px solid var(--border-color);
  box-shadow: var(--shadow-sm);
}

.mode-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border-radius: 16px;
  border: none;
  background: transparent;
  color: var(--text-muted);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.25s ease;
}

.mode-btn.active {
  background-color: var(--primary);
  color: #ffffff;
  box-shadow: 0 4px 12px rgba(49, 130, 206, 0.3);
}

.focus-display-section {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 24px;
  width: 100%;
}

.adjust-group {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.btn-adjust {
  background-color: var(--bg-surface);
  border: 1px solid var(--border-color);
  color: var(--text-main);
  width: 48px;
  height: 48px;
  border-radius: 50%;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
  box-shadow: var(--shadow-sm);
}

.btn-adjust:hover:not(:disabled) {
  border-color: var(--primary);
  color: var(--primary);
  transform: scale(1.08);
  box-shadow: 0 4px 12px rgba(49, 130, 206, 0.2);
}

.btn-adjust:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

.timer-circle-wrapper {
  position: relative;
  width: 280px;
  height: 280px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: transform 0.3s ease;
}

.timer-circle-wrapper.is-active {
  animation: pulse-glow 3s infinite ease-in-out;
}

@keyframes pulse-glow {
  0%, 100% {
    filter: drop-shadow(0 0 10px rgba(49, 130, 206, 0.15));
  }
  50% {
    filter: drop-shadow(0 0 24px rgba(128, 90, 213, 0.35));
  }
}

.progress-ring {
  transform: rotate(-90deg);
}

.progress-ring-bg {
  fill: none;
  stroke: var(--border-color);
  opacity: 0.5;
}

.progress-ring-fill {
  fill: none;
  stroke-linecap: round;
  transition: stroke-dashoffset 0.4s ease;
}

.timer-center-text {
  position: absolute;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
}

.time-number {
  font-size: clamp(52px, 6.5vw, 72px);
  font-weight: 800;
  color: var(--text-main);
  font-family: 'Outfit', 'Inter', system-ui, sans-serif;
  font-variant-numeric: tabular-nums;
  letter-spacing: -2px;
  line-height: 1;
}

.timer-status-badge {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  font-weight: 600;
  color: var(--text-muted);
  background-color: var(--bg-surface);
  padding: 4px 12px;
  border-radius: 12px;
  border: 1px solid var(--border-color);
}

.timer-status-badge.running {
  color: var(--primary);
  border-color: rgba(49, 130, 206, 0.3);
}

.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background-color: var(--text-muted);
}

.timer-status-badge.running .status-dot {
  background-color: #38A169;
  box-shadow: 0 0 8px #38A169;
}

.controls-row {
  display: flex;
  align-items: center;
  gap: 14px;
}

.btn-reset, .btn-settings-toggle {
  background-color: var(--bg-surface);
  border: 1px solid var(--border-color);
  color: var(--text-main);
  padding: 10px 18px;
  border-radius: 20px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 600;
  transition: all 0.2s ease;
  box-shadow: var(--shadow-sm);
}

.btn-reset:hover, .btn-settings-toggle:hover {
  border-color: var(--primary);
  color: var(--primary);
  transform: translateY(-1px);
}

.btn-toggle-run {
  background: linear-gradient(135deg, var(--primary) 0%, var(--ai-purple) 100%);
  color: #ffffff;
  border: none;
  padding: 12px 32px;
  border-radius: 24px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 15px;
  font-weight: 700;
  box-shadow: 0 6px 18px rgba(49, 130, 206, 0.35);
  transition: all 0.2s ease;
}

.btn-toggle-run.is-running {
  background: linear-gradient(135deg, #DD6B20 0%, #E53E3E 100%);
  box-shadow: 0 6px 18px rgba(221, 107, 32, 0.35);
}

.btn-toggle-run:hover {
  transform: translateY(-2px);
  filter: brightness(1.05);
}

.stats-banner {
  display: flex;
  width: 100%;
  max-width: 500px;
  justify-content: space-around;
  padding-top: 20px;
  border-top: 1px solid var(--border-color);
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 12px;
}

.stat-icon {
  font-size: 26px;
}

.stat-info {
  display: flex;
  flex-direction: column;
}

.stat-val {
  font-size: 18px;
  font-weight: 800;
  color: var(--primary);
}

.stat-lbl {
  font-size: 11px;
  color: var(--text-muted);
}

/* Modal styles for Customizing Duration */
.modal-backdrop {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background-color: rgba(0, 0, 0, 0.45);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-card {
  background-color: var(--bg-surface);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  padding: 24px;
  width: 90%;
  max-width: 420px;
  box-shadow: var(--shadow-lg);
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.modal-title {
  font-size: 16px;
  font-weight: 700;
  color: var(--text-main);
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-group label {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-muted);
}

.form-group input {
  padding: 8px 12px;
  border-radius: 6px;
  border: 1px solid var(--border-color);
  background-color: var(--bg-app);
  color: var(--text-main);
  font-size: 14px;
  outline: none;
}

.form-group input:focus {
  border-color: var(--primary);
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 8px;
}

.btn {
  padding: 8px 16px;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  border: 1px solid var(--border-color);
  background-color: transparent;
  color: var(--text-main);
}

.btn-primary {
  background-color: var(--primary);
  color: #ffffff;
  border: none;
}
</style>

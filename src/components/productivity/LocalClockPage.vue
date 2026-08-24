<template>
  <div class="local-clock-container animate-fade-in" :class="{ 'zen-fullscreen': isZenMode }">
    <!-- Header Control Toolbar (Hidden in Zen Mode) -->
    <div v-if="!isZenMode" class="clock-toolbar">
      <div class="toolbar-left">
        <div class="page-title">
          <Clock :size="22" class="icon-primary" />
          <h2>本地高精度时钟</h2>
        </div>
        <span class="title-subtext">实时本地时间、时区与天文农历看板</span>
      </div>

      <!-- Feature Controls: Visual Mode, Seconds, Milliseconds, 12/24H, Zen Mode -->
      <div class="toolbar-right">
        <!-- Display Mode Toggle (Dual / Digital / Analog) -->
        <div class="mode-toggle-group">
          <button
            class="mode-btn"
            :class="{ active: displayMode === 'dual' }"
            @click="displayMode = 'dual'"
            title="双视图模式"
          >
            <Columns :size="13" />
            <span>双视角</span>
          </button>
          <button
            class="mode-btn"
            :class="{ active: displayMode === 'digital' }"
            @click="displayMode = 'digital'"
            title="纯数字大屏"
          >
            <Tv :size="13" />
            <span>数字</span>
          </button>
          <button
            class="mode-btn"
            :class="{ active: displayMode === 'analog' }"
            @click="displayMode = 'analog'"
            title="模拟表盘模式"
          >
            <Disc :size="13" />
            <span>表盘</span>
          </button>
        </div>

        <button
          class="control-btn"
          :class="{ active: showSeconds }"
          @click="toggleSeconds"
          title="切换是否显示秒"
        >
          <Zap :size="14" />
          <span>秒 ({{ showSeconds ? '开' : '关' }})</span>
        </button>

        <button
          class="control-btn"
          :class="{ active: showMilliseconds }"
          @click="toggleMilliseconds"
          title="切换是否显示毫秒"
        >
          <Activity :size="14" />
          <span>毫秒 ({{ showMilliseconds ? '开' : '关' }})</span>
        </button>

        <button
          class="control-btn"
          :class="{ active: use12Hour }"
          @click="toggle12Hour"
          title="切换12小时制/24小时制"
        >
          <Clock :size="14" />
          <span>{{ use12Hour ? '12小时制' : '24小时制' }}</span>
        </button>

        <!-- Zen Fullscreen Immersion Button -->
        <button class="control-btn btn-zen" @click="isZenMode = true" title="进入全屏沉浸大钟模式">
          <Maximize2 :size="14" />
          <span>沉浸模式</span>
        </button>
      </div>
    </div>

    <!-- Exit Zen Mode Floating Button -->
    <button v-if="isZenMode" class="btn-exit-zen" @click="isZenMode = false" title="退出沉浸模式 (ESC)">
      <Minimize2 :size="16" />
      <span>退出沉浸</span>
    </button>

    <!-- Main Clock Stage Area -->
    <div class="clock-stage-wrapper">
      <div class="clock-showcase-card" :class="displayMode">
        <!-- Ambient Breathing Glow -->
        <div class="clock-ambient-glow"></div>

        <div class="clock-main-stage">
          <!-- 1. Analog Clock Visual (Rendered if mode is analog or dual) -->
          <div v-if="displayMode === 'analog' || displayMode === 'dual'" class="analog-clock-wrapper">
            <svg class="analog-clock-svg" viewBox="0 0 240 240">
              <defs>
                <linearGradient id="bezelGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stop-color="rgba(255,255,255,0.25)" />
                  <stop offset="50%" stop-color="rgba(99,102,241,0.15)" />
                  <stop offset="100%" stop-color="rgba(0,0,0,0.15)" />
                </linearGradient>
                <filter id="handShadow" x="-20%" y="-20%" width="140%" height="140%">
                  <feDropShadow dx="0" dy="2" stdDeviation="2" flood-opacity="0.25" />
                </filter>
              </defs>

              <circle cx="120" cy="120" r="114" class="clock-outer-bezel" fill="url(#bezelGrad)" />
              <circle cx="120" cy="120" r="108" class="clock-dial-bg" />

              <g class="clock-ticks">
                <line
                  v-for="n in 60"
                  :key="'m' + n"
                  x1="120"
                  y1="18"
                  x2="120"
                  y2="22"
                  :transform="`rotate(${n * 6} 120 120)`"
                  class="minute-tick"
                />
                <line
                  v-for="n in 12"
                  :key="'h' + n"
                  x1="120"
                  y1="18"
                  x2="120"
                  y2="27"
                  :transform="`rotate(${n * 30} 120 120)`"
                  class="hour-tick"
                />
              </g>

              <text x="120" y="46" class="clock-number" text-anchor="middle">12</text>
              <text x="198" y="126" class="clock-number" text-anchor="middle">3</text>
              <text x="120" y="206" class="clock-number" text-anchor="middle">6</text>
              <text x="42" y="126" class="clock-number" text-anchor="middle">9</text>

              <line
                x1="120"
                y1="120"
                x2="120"
                y2="64"
                :transform="`rotate(${analogAngles.hour} 120 120)`"
                class="hand hour-hand"
                filter="url(#handShadow)"
              />
              <line
                x1="120"
                y1="120"
                x2="120"
                y2="42"
                :transform="`rotate(${analogAngles.minute} 120 120)`"
                class="hand minute-hand"
                filter="url(#handShadow)"
              />
              <line
                x1="120"
                y1="134"
                x2="120"
                y2="30"
                :transform="`rotate(${analogAngles.second} 120 120)`"
                class="hand second-hand"
                filter="url(#handShadow)"
              />
              <circle cx="120" cy="120" r="5" class="center-pin" />
              <circle cx="120" cy="120" r="2" class="center-jewel" />
            </svg>
          </div>

          <!-- 2. Digital Clock & Lunar Calendar Display -->
          <div v-if="displayMode === 'digital' || displayMode === 'dual'" class="digital-clock-wrapper">
            <div class="time-header-pill">
              <span class="pulse-indicator"></span>
              <span class="tz-label">{{ localTzName }}</span>
              <span class="tz-offset">{{ localOffsetStr }}</span>
            </div>

            <div class="hero-digital-time">
              <div class="digits-group">
                <span class="digit-hours">{{ formattedLocalTime.hours }}</span>
                <span class="digit-colon">:</span>
                <span class="digit-minutes">{{ formattedLocalTime.minutes }}</span>
                <span v-if="showSeconds" class="digit-colon">:</span>
                <span v-if="showSeconds" class="digit-seconds">{{ formattedLocalTime.seconds }}</span>
                <span v-if="showMilliseconds" class="digit-milliseconds">.{{ formattedLocalTime.milliseconds }}</span>
              </div>
              <span v-if="use12Hour" class="digit-ampm">{{ formattedLocalTime.ampm }}</span>
            </div>

            <div class="calendar-detail-row">
              <div class="detail-pill date-pill">
                <Calendar :size="15" class="icon-accent" />
                <span>{{ formattedLocalTime.fullDateStr }}</span>
                <span class="weekday-tag">{{ formattedLocalTime.weekday }}</span>
              </div>
              <div class="detail-pill lunar-pill">
                <Sparkles :size="14" class="icon-lunar" />
                <span>{{ lunarText }}</span>
              </div>
            </div>

            <div class="day-progress-section">
              <div class="progress-info-row">
                <span class="greeting-text">{{ greetingText }}</span>
                <span class="progress-percent">今日进度 {{ dayProgressPercent }}%</span>
              </div>
              <div class="day-progress-track">
                <div class="day-progress-bar" :style="{ width: `${dayProgressPercent}%` }"></div>
              </div>
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
  Clock,
  Zap,
  Activity,
  Calendar,
  Columns,
  Tv,
  Disc,
  Sparkles,
  Maximize2,
  Minimize2
} from 'lucide-vue-next'
import { getLunar } from '../../utils/lunar'

const now = ref<Date>(new Date())
const showSeconds = ref<boolean>(true)
const showMilliseconds = ref<boolean>(false)
const use12Hour = ref<boolean>(false)
const displayMode = ref<'dual' | 'digital' | 'analog'>('dual')
const isZenMode = ref<boolean>(false)

let animationFrameId: number | null = null
let intervalTimerId: any = null

function handleKeyDown(e: KeyboardEvent) {
  if (e.key === 'Escape' && isZenMode.value) isZenMode.value = false
}

function updateTime() {
  now.value = new Date()
  if (showMilliseconds.value || animationFrameId !== null) {
    animationFrameId = requestAnimationFrame(updateTime)
  }
}

function startClockLoop() {
  stopClockLoop()
  if (showMilliseconds.value || displayMode.value !== 'digital') {
    animationFrameId = requestAnimationFrame(updateTime)
  } else {
    intervalTimerId = setInterval(() => { now.value = new Date() }, 1000)
  }
}

function stopClockLoop() {
  if (animationFrameId !== null) { cancelAnimationFrame(animationFrameId); animationFrameId = null }
  if (intervalTimerId !== null) { clearInterval(intervalTimerId); intervalTimerId = null }
}

function toggleSeconds() { showSeconds.value = !showSeconds.value }
function toggleMilliseconds() { showMilliseconds.value = !showMilliseconds.value; startClockLoop() }
function toggle12Hour() { use12Hour.value = !use12Hour.value }

const localTzName = computed(() => Intl.DateTimeFormat().resolvedOptions().timeZone || 'Asia/Shanghai')
const localOffsetStr = computed(() => {
  const offset = -now.value.getTimezoneOffset()
  const sign = offset >= 0 ? '+' : '-'
  const abs = Math.abs(offset)
  return `UTC${sign}${String(Math.floor(abs/60)).padStart(2,'0')}:${String(abs%60).padStart(2,'0')}`
})

const formattedLocalTime = computed(() => {
  const d = now.value
  let h = d.getHours(), ampm = ''
  if (use12Hour.value) { ampm = h >= 12 ? 'PM' : 'AM'; h = h % 12 || 12 }
  return {
    hours: String(h).padStart(2, '0'),
    minutes: String(d.getMinutes()).padStart(2, '0'),
    seconds: String(d.getSeconds()).padStart(2, '0'),
    milliseconds: String(Math.floor(d.getMilliseconds() / 10)).padStart(2, '0'),
    ampm,
    weekday: ['星期日', '星期一', '星期二', '星期三', '星期四', '星期五', '星期六'][d.getDay()],
    fullDateStr: `${d.getFullYear()}年${String(d.getMonth() + 1).padStart(2, '0')}月${String(d.getDate()).padStart(2, '0')}日`
  }
})

const analogAngles = computed(() => {
  const d = now.value
  const ms = d.getMilliseconds(), sec = d.getSeconds() + ms / 1000
  return { second: sec * 6, minute: (d.getMinutes() + sec / 60) * 6, hour: ((d.getHours() % 12) + (d.getMinutes() + sec / 60) / 60) * 30 }
})

const lunarText = computed(() => {
  try {
    const l = getLunar(now.value)
    return l ? `农历 ${l.fullText}${l.solarTerm ? ' · ' + l.solarTerm : ''}` : '农历吉祥 · 岁月静好'
  } catch { return '农历吉祥 · 岁月静好' }
})

const greetingText = computed(() => {
  const h = now.value.getHours()
  if (h < 5) return '✨ 夜深了 · 早点休息'
  if (h < 9) return '🌅 晨光破晓 · 新的一天开启'
  if (h < 12) return '☀️ 早上好 · 保持专注与高效'
  if (h < 14) return '🍲 中午好 · 记得享用午餐'
  if (h < 18) return '☕ 下午好 · 专注投入收获满满'
  return '🌙 晚上好 · 享受惬意时光'
})

const dayProgressPercent = computed(() => (((now.value.getHours() * 3600 + now.value.getMinutes() * 60 + now.value.getSeconds()) / 86400) * 100).toFixed(1))

onMounted(() => { startClockLoop(); window.addEventListener('keydown', handleKeyDown) })
onUnmounted(() => { stopClockLoop(); window.removeEventListener('keydown', handleKeyDown) })
</script>

<style scoped>
.local-clock-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: 20px 24px;
  gap: 20px;
  box-sizing: border-box;
  overflow-y: auto;
}

/* Zen Fullscreen Mode */
.local-clock-container.zen-fullscreen {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  padding: 0;
  z-index: 99999;
  background: var(--bg-app, #0f172a);
  display: flex;
  align-items: center;
  justify-content: center;
}

.btn-exit-zen {
  position: fixed;
  top: 24px;
  right: 24px;
  z-index: 100000;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: rgba(15, 23, 42, 0.75);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 20px;
  color: #ffffff;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
}

.btn-exit-zen:hover {
  background: var(--primary, #3b82f6);
  transform: translateY(-2px);
}

/* Header Control Toolbar */
.clock-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
}

.toolbar-left {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.page-title {
  display: flex;
  align-items: center;
  gap: 8px;
}

.page-title h2 {
  font-size: 20px;
  font-weight: 700;
  color: var(--text-main, #0f172a);
  margin: 0;
}

.icon-primary {
  color: var(--primary, #3b82f6);
}

.title-subtext {
  font-size: 12.5px;
  color: var(--text-muted, #64748b);
}

.toolbar-right {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.mode-toggle-group {
  display: flex;
  background: var(--bg-surface, #ffffff);
  border: 1px solid var(--border-color, #e2e8f0);
  border-radius: 10px;
  padding: 2px;
  gap: 2px;
}

.mode-btn {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 5px 10px;
  border-radius: 8px;
  border: none;
  background: transparent;
  color: var(--text-muted, #64748b);
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.mode-btn:hover {
  color: var(--text-main, #0f172a);
}

.mode-btn.active {
  background: var(--primary, #3b82f6);
  color: #ffffff;
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.3);
}

.control-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: var(--bg-surface, #ffffff);
  border: 1px solid var(--border-color, #e2e8f0);
  border-radius: 10px;
  color: var(--text-muted, #64748b);
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.control-btn:hover {
  border-color: var(--primary, #3b82f6);
  color: var(--primary, #3b82f6);
}

.control-btn.active {
  background: rgba(59, 130, 246, 0.08);
  border-color: var(--primary, #3b82f6);
  color: var(--primary, #3b82f6);
}

.btn-zen {
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.1), rgba(168, 85, 247, 0.1));
  border-color: rgba(99, 102, 241, 0.3);
  color: #6366f1;
}

.btn-zen:hover {
  background: linear-gradient(135deg, #6366f1, #a855f7);
  color: #ffffff;
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.35);
}

/* Main Clock Showcase Stage */
.clock-stage-wrapper {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 480px;
}

.zen-fullscreen .clock-stage-wrapper {
  width: 100%;
  height: 100%;
}

.clock-showcase-card {
  position: relative;
  width: 100%;
  max-width: 960px;
  background: var(--bg-card, #ffffff);
  border: 1px solid var(--border-color, #e2e8f0);
  border-radius: 28px;
  padding: 48px 40px;
  box-shadow: 0 20px 48px -12px rgba(0, 0, 0, 0.06), 0 0 1px 1px rgba(255, 255, 255, 0.6) inset;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  box-sizing: border-box;
}

.zen-fullscreen .clock-showcase-card {
  max-width: 1100px;
  border: none;
  background: transparent;
  box-shadow: none;
}

.clock-ambient-glow {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 480px;
  height: 480px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(99, 102, 241, 0.12) 0%, rgba(236, 72, 153, 0.05) 50%, transparent 70%);
  pointer-events: none;
  animation: pulse-glow 6s infinite ease-in-out;
}

@keyframes pulse-glow {
  0%, 100% { transform: translate(-50%, -50%) scale(1); opacity: 0.8; }
  50% { transform: translate(-50%, -50%) scale(1.18); opacity: 1; }
}

.clock-main-stage {
  position: relative;
  z-index: 1;
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 48px;
}

/* Analog Clock SVG Styles */
.analog-clock-wrapper {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.analog-clock-svg {
  width: 240px;
  height: 240px;
  filter: drop-shadow(0 12px 28px rgba(0, 0, 0, 0.08));
}

.clock-outer-bezel {
  stroke: var(--border-color, #cbd5e1);
  stroke-width: 2;
}

.clock-dial-bg {
  fill: var(--bg-surface, #ffffff);
  stroke: rgba(0, 0, 0, 0.04);
  stroke-width: 1;
}

.minute-tick {
  stroke: var(--text-muted, #94a3b8);
  stroke-width: 1.5;
  stroke-linecap: round;
  opacity: 0.45;
}

.hour-tick {
  stroke: var(--text-main, #0f172a);
  stroke-width: 3;
  stroke-linecap: round;
  opacity: 0.85;
}

.clock-number {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, sans-serif;
  font-size: 15px;
  font-weight: 800;
  fill: var(--text-main, #1e293b);
}

.hand {
  stroke-linecap: round;
  transform-origin: 120px 120px;
  transition: transform 0.05s linear;
}

.hour-hand {
  stroke: var(--primary, #3b82f6);
  stroke-width: 5;
}

.minute-hand {
  stroke: var(--text-main, #0f172a);
  stroke-width: 3.5;
}

.second-hand {
  stroke: #ec4899;
  stroke-width: 2;
}

.center-pin {
  fill: #0f172a;
}

.center-jewel {
  fill: #ec4899;
}

/* Digital Clock Wrapper Styles */
.digital-clock-wrapper {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 20px;
}

.clock-showcase-card.digital .digital-clock-wrapper {
  align-items: center;
}

.time-header-pill {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 5px 14px;
  background: var(--bg-surface, #f8fafc);
  border: 1px solid var(--border-color, #e2e8f0);
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
  color: var(--text-muted, #64748b);
}

.pulse-indicator {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background-color: #10b981;
  box-shadow: 0 0 8px #10b981;
  animation: blink 2s infinite;
}

@keyframes blink {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.4; transform: scale(0.85); }
}

.tz-offset {
  color: var(--primary, #3b82f6);
  font-weight: 700;
}

/* Huge Digital Numbers with Tabular Anti-Shake */
.hero-digital-time {
  display: flex;
  align-items: baseline;
  gap: 12px;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-variant-numeric: tabular-nums;
  font-feature-settings: "tnum";
  line-height: 1;
}

.digits-group {
  display: flex;
  align-items: baseline;
  font-size: clamp(48px, 6vw, 76px);
  font-weight: 800;
  color: var(--text-main, #0f172a);
  letter-spacing: -2px;
  text-shadow: 0 4px 20px rgba(99, 102, 241, 0.15);
}

.digit-colon {
  margin: 0 2px;
  color: var(--primary, #6366f1);
  opacity: 0.85;
}

.digit-seconds {
  color: #6366f1;
}

.digit-milliseconds {
  font-size: 0.48em;
  color: #a855f7;
  font-weight: 700;
  margin-left: 2px;
}

.digit-ampm {
  font-size: 20px;
  font-weight: 700;
  color: var(--text-muted, #64748b);
}

/* Calendar and Lunar Badges */
.calendar-detail-row {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.detail-pill {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: var(--bg-surface, #f8fafc);
  border: 1px solid var(--border-color, #e2e8f0);
  border-radius: 12px;
  font-size: 13.5px;
  font-weight: 600;
  color: var(--text-main, #1e293b);
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.02);
}

.icon-accent {
  color: var(--primary, #3b82f6);
}

.icon-lunar {
  color: #f59e0b;
}

.weekday-tag {
  background: rgba(59, 130, 246, 0.12);
  color: var(--primary, #3b82f6);
  padding: 2px 8px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 700;
}

/* Greeting and Day Progress Section */
.day-progress-section {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 4px;
}

.progress-info-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 12.5px;
  font-weight: 600;
}

.greeting-text {
  color: var(--text-muted, #64748b);
}

.progress-percent {
  color: var(--primary, #6366f1);
  font-family: ui-monospace, monospace;
}

.day-progress-track {
  width: 100%;
  height: 6px;
  background: var(--border-color, #e2e8f0);
  border-radius: 6px;
  overflow: hidden;
}

.day-progress-bar {
  height: 100%;
  background: linear-gradient(90deg, #3b82f6 0%, #8b5cf6 50%, #ec4899 100%);
  border-radius: 6px;
  transition: width 1s linear;
}

/* Responsive Breakpoints */
@media (max-width: 768px) {
  .clock-main-stage {
    flex-direction: column;
    gap: 32px;
  }
  .digital-clock-wrapper {
    align-items: center;
  }
  .clock-showcase-card {
    padding: 32px 20px;
  }
  .digits-group {
    font-size: 42px;
  }
}
</style>

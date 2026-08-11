<template>
  <div class="navbar-clock-container" ref="clockContainerRef">
    <!-- Clock Display Card -->
    <div class="clock-display-card" title="点击查看世界时钟列表" @click.stop="toggleWorldMenu">
      <div class="clock-icon-zone">
        <component :is="currentZoneInfo.zone === 'local' ? Clock : Globe" :size="14" class="clock-icon" />
        <span class="zone-badge">
          <span class="zone-flag">{{ currentZoneInfo.flag }}</span>
          <span class="zone-name">{{ currentZoneInfo.name }}</span>
        </span>
      </div>

      <!-- Time Text Area -->
      <div class="clock-time-text">
        <span class="time-main">{{ formattedTime.hours }}:{{ formattedTime.minutes }}</span>
        <span v-if="showSeconds" class="time-seconds">:{{ formattedTime.seconds }}</span>
        <span v-if="showMilliseconds" class="time-ms">.{{ formattedTime.milliseconds }}</span>
      </div>

      <!-- Arrow Indicator for dropdown -->
      <ChevronDown :size="12" class="dropdown-arrow" :class="{ open: isWorldMenuOpen }" />
    </div>

    <!-- Toggle Controls (Seconds / Milliseconds Buttons) -->
    <div class="clock-controls-group">
      <button
        class="clock-toggle-btn"
        :class="{ active: showSeconds }"
        @click.stop="toggleSeconds"
        title="开启/关闭秒显示"
      >
        <Zap :size="11" class="btn-icon" />
        <span>秒</span>
      </button>

      <button
        class="clock-toggle-btn"
        :class="{ active: showMilliseconds }"
        @click.stop="toggleMilliseconds"
        title="开启/关闭毫秒显示"
      >
        <Activity :size="11" class="btn-icon" />
        <span>毫秒</span>
      </button>
    </div>

    <!-- World Clock Dropdown Panel -->
    <Transition name="fade-slide">
      <div v-if="isWorldMenuOpen" class="world-clock-dropdown" @click.stop>
        <div class="dropdown-header">
          <div class="header-title">
            <Globe :size="14" class="icon-primary" />
            <span>世界时钟与时区选择</span>
          </div>
          <span class="current-date-str">{{ formattedTime.dateStr }}</span>
        </div>

        <div class="zone-list">
          <button
            v-for="item in ZONES_LIST"
            :key="item.zone"
            class="zone-item-btn"
            :class="{ active: selectedZone === item.zone }"
            @click="selectZone(item.zone)"
          >
            <div class="zone-item-left">
              <span class="zone-flag-lg">{{ item.flag }}</span>
              <div class="zone-item-info">
                <span class="zone-item-name">{{ item.name }}</span>
                <span class="zone-item-offset">{{ item.offsetLabel }}</span>
              </div>
            </div>

            <div class="zone-item-time">
              {{ getZoneTimeString(item.zone) }}
            </div>
          </button>
        </div>

        <div class="dropdown-footer">
          <div class="footer-hint">
            <span>数据更新频率: {{ showMilliseconds ? '高精度 (~16ms)' : showSeconds ? '1秒' : '1分' }}</span>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { Clock, Globe, Zap, Activity, ChevronDown } from 'lucide-vue-next'

interface ZoneItem {
  name: string
  zone: string
  flag: string
  offsetLabel: string
}

const ZONES_LIST: ZoneItem[] = [
  { name: '本地时间', zone: 'local', flag: '🏠', offsetLabel: '系统默认' },
  { name: '北京 / 上海', zone: 'Asia/Shanghai', flag: '🇨🇳', offsetLabel: 'UTC+8' },
  { name: '东京 / 大阪', zone: 'Asia/Tokyo', flag: '🇯🇵', offsetLabel: 'UTC+9' },
  { name: '伦敦 / 剑桥', zone: 'Europe/London', flag: '🇬🇧', offsetLabel: 'UTC+0/+1' },
  { name: '纽约 / 华盛顿', zone: 'America/New_York', flag: '🇺🇸', offsetLabel: 'UTC-5/-4' },
  { name: '巴黎 / 柏林', zone: 'Europe/Paris', flag: '🇫🇷', offsetLabel: 'UTC+1/+2' },
  { name: '悉尼 / 墨尔本', zone: 'Australia/Sydney', flag: '🇦🇺', offsetLabel: 'UTC+10/+11' },
  { name: '协调世界时', zone: 'UTC', flag: '🌐', offsetLabel: 'UTC+0' }
]

// State
const selectedZone = ref<string>(localStorage.getItem('navbar_clock_zone') || 'local')
const showSeconds = ref<boolean>(localStorage.getItem('navbar_clock_show_sec') !== 'false') // 默认开启
const showMilliseconds = ref<boolean>(localStorage.getItem('navbar_clock_show_ms') === 'true') // 默认关闭
const isWorldMenuOpen = ref<boolean>(false)
const clockContainerRef = ref<HTMLElement | null>(null)

const now = ref<Date>(new Date())
let timerId: number | null = null
let animationFrameId: number | null = null

// Current zone info
const currentZoneInfo = computed(() => {
  return ZONES_LIST.find(z => z.zone === selectedZone.value) || ZONES_LIST[0]
})

// Formatting Time for Header Display
const formattedTime = computed(() => {
  const d = now.value
  const zone = selectedZone.value

  let options: Intl.DateTimeFormatOptions = {
    hour12: false,
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    weekday: 'short'
  }

  if (zone !== 'local') {
    options.timeZone = zone
  }

  const formatter = new Intl.DateTimeFormat('zh-CN', options)
  const parts = formatter.formatToParts(d)

  const getPart = (type: string) => parts.find(p => p.type === type)?.value || '00'

  const hours = getPart('hour')
  const minutes = getPart('minute')
  const seconds = getPart('second')

  // Date String
  const year = getPart('year')
  const month = getPart('month')
  const day = getPart('day')
  const weekday = getPart('weekday')
  const dateStr = `${year}-${month}-${day} ${weekday}`

  // Milliseconds
  const msNum = d.getMilliseconds()
  const milliseconds = String(msNum).padStart(3, '0')

  return {
    hours,
    minutes,
    seconds,
    milliseconds,
    dateStr
  }
})

// Calculate live time for any zone in dropdown list
function getZoneTimeString(zone: string): string {
  const d = now.value
  const options: Intl.DateTimeFormatOptions = {
    hour12: false,
    hour: '2-digit',
    minute: '2-digit'
  }
  if (showSeconds.value) {
    options.second = '2-digit'
  }
  if (zone !== 'local') {
    options.timeZone = zone
  }

  try {
    const timeStr = new Intl.DateTimeFormat('zh-CN', options).format(d)
    if (showMilliseconds.value) {
      const ms = String(d.getMilliseconds()).padStart(3, '0')
      return `${timeStr}.${ms}`
    }
    return timeStr
  } catch (e) {
    return '--:--'
  }
}

// Timer Management
function updateClock() {
  now.value = new Date()
  if (showMilliseconds.value) {
    animationFrameId = requestAnimationFrame(updateClock)
  }
}

function startTimer() {
  stopTimer()
  if (showMilliseconds.value) {
    // High-resolution updates with requestAnimationFrame
    animationFrameId = requestAnimationFrame(updateClock)
  } else {
    // Normal interval update
    const intervalMs = showSeconds.value ? 200 : 1000
    timerId = window.setInterval(() => {
      now.value = new Date()
    }, intervalMs)
  }
}

function stopTimer() {
  if (timerId !== null) {
    clearInterval(timerId)
    timerId = null
  }
  if (animationFrameId !== null) {
    cancelAnimationFrame(animationFrameId)
    animationFrameId = null
  }
}

// Controls
function toggleSeconds() {
  showSeconds.value = !showSeconds.value
  localStorage.setItem('navbar_clock_show_sec', String(showSeconds.value))
  startTimer()
}

function toggleMilliseconds() {
  showMilliseconds.value = !showMilliseconds.value
  // If milliseconds turned on, seconds must be on
  if (showMilliseconds.value && !showSeconds.value) {
    showSeconds.value = true
    localStorage.setItem('navbar_clock_show_sec', 'true')
  }
  localStorage.setItem('navbar_clock_show_ms', String(showMilliseconds.value))
  startTimer()
}

function toggleWorldMenu() {
  isWorldMenuOpen.value = !isWorldMenuOpen.value
}

function selectZone(zone: string) {
  selectedZone.value = zone
  localStorage.setItem('navbar_clock_zone', zone)
  isWorldMenuOpen.value = false
}

// Click outside handler
function handleOutsideClick(e: MouseEvent) {
  if (clockContainerRef.value && !clockContainerRef.value.contains(e.target as Node)) {
    isWorldMenuOpen.value = false
  }
}

watch([showSeconds, showMilliseconds], () => {
  startTimer()
})

onMounted(() => {
  startTimer()
  document.addEventListener('click', handleOutsideClick)
})

onUnmounted(() => {
  stopTimer()
  document.removeEventListener('click', handleOutsideClick)
})
</script>

<style scoped>
.navbar-clock-container {
  position: relative;
  display: flex;
  align-items: center;
  gap: 6px;
  user-select: none;
}

/* Clock Display Card */
.clock-display-card {
  display: flex;
  align-items: center;
  gap: 8px;
  background-color: var(--bg-app);
  padding: 4px 10px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--border-color);
  cursor: pointer;
  transition: all 0.2s ease;
  height: 28px;
  box-sizing: border-box;
}

.clock-display-card:hover {
  border-color: var(--primary);
  background-color: var(--bg-card-hover);
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05);
}

.clock-icon-zone {
  display: flex;
  align-items: center;
  gap: 4px;
}

.clock-icon {
  color: var(--primary);
}

.zone-badge {
  display: flex;
  align-items: center;
  gap: 3px;
  font-size: 11px;
  font-weight: 600;
  color: var(--text-muted);
}

.zone-flag {
  font-size: 12px;
}

.clock-time-text {
  font-family: 'JetBrains Mono', 'Fira Code', 'Courier New', monospace;
  font-size: 13px;
  font-weight: 700;
  color: var(--text-main);
  letter-spacing: 0.5px;
  display: flex;
  align-items: baseline;
}

.time-seconds {
  color: var(--primary);
  font-weight: 600;
}

.time-ms {
  font-size: 10px;
  color: var(--ai-purple);
  font-weight: 500;
  margin-left: 1px;
  min-width: 22px;
}

.dropdown-arrow {
  color: var(--text-muted);
  transition: transform 0.2s ease;
}

.dropdown-arrow.open {
  transform: rotate(180deg);
}

/* Controls Group (Seconds / MS Buttons) */
.clock-controls-group {
  display: flex;
  align-items: center;
  gap: 3px;
  background-color: var(--bg-app);
  padding: 2px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--border-color);
  height: 28px;
  box-sizing: border-box;
}

.clock-toggle-btn {
  display: flex;
  align-items: center;
  gap: 3px;
  font-size: 11px;
  font-weight: 600;
  padding: 2px 7px;
  height: 22px;
  border-radius: 4px;
  border: none;
  background: transparent;
  color: var(--text-muted);
  cursor: pointer;
  transition: all 0.2s ease;
  line-height: 1;
}

.clock-toggle-btn:hover {
  color: var(--text-main);
  background-color: rgba(0, 0, 0, 0.04);
}

.clock-toggle-btn.active {
  background-color: var(--bg-surface);
  color: var(--primary);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.clock-toggle-btn.active .btn-icon {
  color: var(--primary);
}

.btn-icon {
  opacity: 0.8;
}

/* Dropdown Panel */
.world-clock-dropdown {
  position: absolute;
  top: calc(100% + 6px);
  right: 0;
  width: 280px;
  background-color: var(--bg-surface);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-lg);
  z-index: 1000;
  overflow: hidden;
  padding: 10px;
}

.dropdown-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-bottom: 8px;
  margin-bottom: 8px;
  border-bottom: 1px solid var(--border-color);
}

.header-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  font-weight: 700;
  color: var(--text-main);
}

.icon-primary {
  color: var(--primary);
}

.current-date-str {
  font-size: 11px;
  color: var(--text-muted);
  font-weight: 500;
}

.zone-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
  max-height: 260px;
  overflow-y: auto;
}

.zone-item-btn {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 10px;
  border-radius: var(--radius-sm);
  border: 1px solid transparent;
  background: transparent;
  cursor: pointer;
  transition: all 0.15s ease;
  text-align: left;
}

.zone-item-btn:hover {
  background-color: var(--bg-card-hover);
  border-color: var(--border-color);
}

.zone-item-btn.active {
  background-color: rgba(49, 130, 206, 0.08);
  border-color: var(--primary);
}

.zone-item-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.zone-flag-lg {
  font-size: 14px;
}

.zone-item-info {
  display: flex;
  flex-direction: column;
}

.zone-item-name {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-main);
}

.zone-item-offset {
  font-size: 10px;
  color: var(--text-muted);
}

.zone-item-time {
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
  font-size: 12px;
  font-weight: 700;
  color: var(--primary);
}

.dropdown-footer {
  margin-top: 8px;
  padding-top: 6px;
  border-top: 1px solid var(--border-color);
  font-size: 10px;
  color: var(--text-muted);
  text-align: center;
}

/* Animations */
.fade-slide-enter-active,
.fade-slide-leave-active {
  transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
}

.fade-slide-enter-from,
.fade-slide-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}

/* Responsive Rules */
@media (max-width: 820px) {
  .clock-controls-group {
    display: none;
  }
}

@media (max-width: 680px) {
  .zone-name {
    display: none;
  }
  
  .clock-display-card {
    padding: 4px 6px;
    gap: 4px;
  }
}
</style>

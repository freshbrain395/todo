<template>
  <div class="local-clock-container animate-fade-in">
    <!-- Header Control Toolbar -->
    <div class="clock-toolbar">
      <div class="toolbar-left">
        <div class="page-title">
          <Clock :size="22" class="icon-primary" />
          <h2>本地高精度时钟</h2>
        </div>
        <span class="title-subtext">显示本地精确时间、时区以及全球多城市时钟</span>
      </div>

      <!-- Feature Controls: Visual Mode, Seconds, Milliseconds, 12/24H, Add City -->
      <div class="toolbar-right">
        <!-- Display Mode Toggle (Dual / Digital / Analog) -->
        <div class="mode-toggle-group">
          <button
            class="mode-btn"
            :class="{ active: displayMode === 'dual' }"
            @click="setDisplayMode('dual')"
            title="双视图模式"
          >
            <Columns :size="13" />
            <span>双视角</span>
          </button>
          <button
            class="mode-btn"
            :class="{ active: displayMode === 'digital' }"
            @click="setDisplayMode('digital')"
            title="纯数字大屏"
          >
            <Tv :size="13" />
            <span>数字</span>
          </button>
          <button
            class="mode-btn"
            :class="{ active: displayMode === 'analog' }"
            @click="setDisplayMode('analog')"
            title="模拟表盘模式"
          >
            <Disc :size="13" />
            <span>表盘</span>
          </button>
        </div>

        <!-- Toggle Seconds -->
        <button
          class="control-btn"
          :class="{ active: showSeconds }"
          @click="toggleSeconds"
          title="切换是否显示秒"
        >
          <Zap :size="14" />
          <span>秒 ({{ showSeconds ? '开' : '关' }})</span>
        </button>

        <!-- Toggle Milliseconds -->
        <button
          class="control-btn"
          :class="{ active: showMilliseconds }"
          @click="toggleMilliseconds"
          title="切换是否显示毫秒"
        >
          <Activity :size="14" />
          <span>毫秒 ({{ showMilliseconds ? '开' : '关' }})</span>
        </button>

        <!-- 12/24 Hour Format -->
        <button
          class="control-btn"
          :class="{ active: use12Hour }"
          @click="toggle12Hour"
          title="切换12小时制/24小时制"
        >
          <Clock :size="14" />
          <span>{{ use12Hour ? '12小时制' : '24小时制' }}</span>
        </button>

        <!-- Add City Button -->
        <button class="btn-primary-sm" @click="showAddCityModal = true">
          <Plus :size="14" />
          <span>添加城市</span>
        </button>
      </div>
    </div>

    <!-- Main Scroll Content Area -->
    <div class="clock-content-scroll">
      <!-- 1. Hero Main Clock Display Card -->
      <div class="hero-clock-card" :class="displayMode">
        <div class="hero-card-badge">
          <span class="badge-flag">🏠</span>
          <span class="badge-text">本地时间 (Local Time)</span>
          <span class="badge-offset">{{ localOffsetStr }}</span>
        </div>

        <div class="hero-main-content">
          <!-- Analog Clock Visual (Rendered if mode is analog or dual) -->
          <div v-if="displayMode === 'analog' || displayMode === 'dual'" class="analog-clock-wrapper">
            <svg class="analog-clock-svg" viewBox="0 0 200 200">
              <!-- Outer Ring -->
              <circle cx="100" cy="100" r="95" class="clock-outer-circle" />
              <circle cx="100" cy="100" r="88" class="clock-inner-circle" />

              <!-- Ticks -->
              <g class="clock-ticks">
                <line
                  v-for="n in 12"
                  :key="n"
                  x1="100"
                  y1="12"
                  x2="100"
                  y2="20"
                  :transform="`rotate(${n * 30} 100 100)`"
                  class="hour-tick"
                />
                <line
                  v-for="n in 60"
                  :key="'m' + n"
                  x1="100"
                  y1="12"
                  x2="100"
                  y2="15"
                  :transform="`rotate(${n * 6} 100 100)`"
                  class="minute-tick"
                />
              </g>

              <!-- Numbers 12, 3, 6, 9 -->
              <text x="100" y="36" class="clock-number" text-anchor="middle">12</text>
              <text x="168" y="105" class="clock-number" text-anchor="middle">3</text>
              <text x="100" y="174" class="clock-number" text-anchor="middle">6</text>
              <text x="32" y="105" class="clock-number" text-anchor="middle">9</text>

              <!-- Hour Hand -->
              <line
                x1="100"
                y1="100"
                x2="100"
                y2="52"
                :transform="`rotate(${analogAngles.hour} 100 100)`"
                class="hand hour-hand"
              />

              <!-- Minute Hand -->
              <line
                x1="100"
                y1="100"
                x2="100"
                y2="32"
                :transform="`rotate(${analogAngles.minute} 100 100)`"
                class="hand minute-hand"
              />

              <!-- Second Hand -->
              <line
                x1="100"
                y1="108"
                x2="100"
                y2="24"
                :transform="`rotate(${analogAngles.second} 100 100)`"
                class="hand second-hand"
              />

              <!-- Center Pin -->
              <circle cx="100" cy="100" r="4" class="center-pin" />
              <circle cx="100" cy="100" r="1.5" class="center-dot" />
            </svg>
          </div>

          <!-- Digital Clock Display (Rendered if mode is digital or dual) -->
          <div v-if="displayMode === 'digital' || displayMode === 'dual'" class="digital-clock-wrapper">
            <div class="hero-time-display">
              <span class="time-main">{{ formattedLocalTime.hours }}:{{ formattedLocalTime.minutes }}</span>
              <span v-if="showSeconds" class="time-seconds">:{{ formattedLocalTime.seconds }}</span>
              <span v-if="showMilliseconds" class="time-milliseconds">.{{ formattedLocalTime.milliseconds }}</span>
              <span v-if="use12Hour" class="time-ampm">{{ formattedLocalTime.ampm }}</span>
            </div>

            <div class="hero-date-info">
              <Calendar :size="16" class="icon-muted" />
              <span>{{ formattedLocalTime.fullDateStr }}</span>
              <span class="week-pill">{{ formattedLocalTime.weekday }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 2. World Cities Section -->
      <div class="section-header">
        <div class="section-title">
          <Globe :size="18" class="icon-primary" />
          <h3>关注的世界城市时钟</h3>
          <span class="city-count-badge">{{ activeCities.length }} 个城市</span>
        </div>
        <button class="text-btn" @click="resetDefaultCities">重置默认城市</button>
      </div>

      <!-- 3. World Cities Grid Cards -->
      <div class="world-cities-grid">
        <div
          v-for="city in activeCities"
          :key="city.id"
          class="city-clock-card animate-scale-up"
        >
          <button
            class="remove-city-btn"
            @click="removeCity(city.id)"
            title="移除此城市"
          >
            <X :size="14" />
          </button>

          <div class="city-header">
            <span class="city-flag">{{ city.flag }}</span>
            <div class="city-name-box">
              <h4 class="city-name">{{ city.name }}</h4>
              <span class="city-tz">{{ city.timeZone }}</span>
            </div>
          </div>

          <div class="city-time-display">
            <span class="city-time-text">{{ getCityTimeString(city.timeZone) }}</span>
          </div>

          <div class="city-footer">
            <span class="city-offset-tag">{{ getCityOffsetString(city.timeZone) }}</span>
            <span class="city-date-tag">{{ getCityDateString(city.timeZone) }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 4. Add City Modal -->
    <Transition name="fade">
      <div v-if="showAddCityModal" class="modal-backdrop" @click.self="showAddCityModal = false">
        <div class="modal-card">
          <div class="modal-header">
            <div class="modal-title">
              <Globe :size="18" class="icon-primary" />
              <h3>添加关注城市时钟</h3>
            </div>
            <button class="close-btn" @click="showAddCityModal = false">
              <X :size="16" />
            </button>
          </div>

          <div class="modal-body">
            <div class="search-input-wrapper">
              <Search :size="15" class="search-icon" />
              <input
                type="text"
                v-model="citySearchQuery"
                placeholder="搜索城市名称或英文名 (如: 伦敦, New York)..."
                class="search-input"
              />
            </div>

            <div class="available-cities-list">
              <div
                v-for="city in filteredAvailableCities"
                :key="city.id"
                class="available-city-item"
              >
                <div class="city-info-left">
                  <span class="flag-lg">{{ city.flag }}</span>
                  <div class="name-meta">
                    <span class="c-name">{{ city.name }}</span>
                    <span class="c-tz">{{ city.timeZone }}</span>
                  </div>
                </div>

                <div class="city-action-right">
                  <span class="live-preview-time">{{ getCityTimeString(city.timeZone) }}</span>
                  <button
                    class="btn-add-action"
                    :disabled="isCityAdded(city.id)"
                    @click="addCity(city.id)"
                  >
                    {{ isCityAdded(city.id) ? '已添加' : '+ 添加' }}
                  </button>
                </div>
              </div>

              <div v-if="filteredAvailableCities.length === 0" class="empty-search">
                未找到匹配的城市
              </div>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import {
  Clock,
  Globe,
  Zap,
  Activity,
  Plus,
  X,
  Calendar,
  Search,
  Columns,
  Tv,
  Disc
} from 'lucide-vue-next'
import { invoke } from '@tauri-apps/api/core'

interface CityItem {
  id: string
  name: string
  flag: string
  timeZone: string
}

const ALL_CITIES: CityItem[] = [
  { id: 'beijing', name: '北京 (Beijing)', flag: '🇨🇳', timeZone: 'Asia/Shanghai' },
  { id: 'tokyo', name: '东京 (Tokyo)', flag: '🇯🇵', timeZone: 'Asia/Tokyo' },
  { id: 'london', name: '伦敦 (London)', flag: '🇬🇧', timeZone: 'Europe/London' },
  { id: 'newyork', name: '纽约 (New York)', flag: '🇺🇸', timeZone: 'America/New_York' },
  { id: 'paris', name: '巴黎 (Paris)', flag: '🇫🇷', timeZone: 'Europe/Paris' },
  { id: 'sydney', name: '悉尼 (Sydney)', flag: '🇦🇺', timeZone: 'Australia/Sydney' },
  { id: 'dubai', name: '迪拜 (Dubai)', flag: '🇦🇪', timeZone: 'Asia/Dubai' },
  { id: 'singapore', name: '新加坡 (Singapore)', flag: '🇸🇬', timeZone: 'Asia/Singapore' },
  { id: 'moscow', name: '莫斯科 (Moscow)', flag: '🇷🇺', timeZone: 'Europe/Moscow' },
  { id: 'losangeles', name: '洛杉矶 (Los Angeles)', flag: '🇺🇸', timeZone: 'America/Los_Angeles' },
  { id: 'bangkok', name: '曼谷 (Bangkok)', flag: '🇹🇭', timeZone: 'Asia/Bangkok' },
  { id: 'berlin', name: '柏林 (Berlin)', flag: '🇩🇪', timeZone: 'Europe/Berlin' }
]

const DEFAULT_CITY_IDS = ['tokyo', 'london', 'newyork', 'paris', 'sydney']

// Reactive States
const now = ref<Date>(new Date())
const showSeconds = ref<boolean>(true)
const showMilliseconds = ref<boolean>(false)
const use12Hour = ref<boolean>(false)
const displayMode = ref<'dual' | 'digital' | 'analog'>('dual')
const activeCityIds = ref<string[]>([...DEFAULT_CITY_IDS])

const showAddCityModal = ref<boolean>(false)
const citySearchQuery = ref<string>('')

let animationFrameId: number | null = null
let intervalTimerId: any = null

// Calculations & Formatting
const localOffsetStr = computed(() => {
  const offsetMinutes = -now.value.getTimezoneOffset()
  const sign = offsetMinutes >= 0 ? '+' : '-'
  const abs = Math.abs(offsetMinutes)
  const h = String(Math.floor(abs / 60)).padStart(2, '0')
  const m = String(abs % 60).padStart(2, '0')
  return `UTC${sign}${h}:${m}`
})

const formattedLocalTime = computed(() => {
  const d = now.value
  let hoursNum = d.getHours()
  let ampm = ''

  if (use12Hour.value) {
    ampm = hoursNum >= 12 ? 'PM' : 'AM'
    hoursNum = hoursNum % 12 || 12
  }

  const hours = String(hoursNum).padStart(2, '0')
  const minutes = String(d.getMinutes()).padStart(2, '0')
  const seconds = String(d.getSeconds()).padStart(2, '0')
  const milliseconds = String(d.getMilliseconds()).padStart(3, '0')

  const weekdays = ['星期日', '星期一', '星期二', '星期三', '星期四', '星期五', '星期六']
  const weekday = weekdays[d.getDay()]

  const year = d.getFullYear()
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')

  return {
    hours,
    minutes,
    seconds,
    milliseconds,
    ampm,
    weekday,
    fullDateStr: `${year}年${month}月${day}日`
  }
})

const analogAngles = computed(() => {
  const d = now.value
  const ms = d.getMilliseconds()
  const sec = d.getSeconds() + (showMilliseconds.value ? ms / 1000 : 0)
  const min = d.getMinutes() + sec / 60
  const hour = (d.getHours() % 12) + min / 60

  return {
    second: sec * 6,
    minute: min * 6,
    hour: hour * 30
  }
})

const activeCities = computed(() => {
  return ALL_CITIES.filter((c) => activeCityIds.value.includes(c.id))
})

const filteredAvailableCities = computed(() => {
  const q = citySearchQuery.value.trim().toLowerCase()
  if (!q) return ALL_CITIES
  return ALL_CITIES.filter(
    (c) => c.name.toLowerCase().includes(q) || c.timeZone.toLowerCase().includes(q)
  )
})

// World City Helper Functions
function getCityTimeString(timeZone: string): string {
  try {
    const options: Intl.DateTimeFormatOptions = {
      timeZone,
      hour: '2-digit',
      minute: '2-digit',
      second: showSeconds.value ? '2-digit' : undefined,
      hour12: use12Hour.value
    }
    return new Intl.DateTimeFormat('zh-CN', options).format(now.value)
  } catch (e) {
    return '--:--'
  }
}

function getCityDateString(timeZone: string): string {
  try {
    const options: Intl.DateTimeFormatOptions = {
      timeZone,
      month: '2-digit',
      day: '2-digit',
      weekday: 'short'
    }
    return new Intl.DateTimeFormat('zh-CN', options).format(now.value)
  } catch (e) {
    return ''
  }
}

function getCityOffsetString(timeZone: string): string {
  try {
    const nowLocal = new Date()
    const cityDateStr = nowLocal.toLocaleString('en-US', { timeZone })
    const cityDate = new Date(cityDateStr)
    const diffHours = (cityDate.getTime() - nowLocal.getTime()) / (1000 * 60 * 60)
    const rounded = Math.round(diffHours * 10) / 10
    if (rounded === 0) return '与本地相同'
    return rounded > 0 ? `比本地快 ${rounded} 小时` : `比本地慢 ${Math.abs(rounded)} 小时`
  } catch (e) {
    return ''
  }
}

function isCityAdded(cityId: string): boolean {
  return activeCityIds.value.includes(cityId)
}

function addCity(cityId: string) {
  if (!activeCityIds.value.includes(cityId)) {
    activeCityIds.value.push(cityId)
    persistConfig()
  }
}

function removeCity(cityId: string) {
  activeCityIds.value = activeCityIds.value.filter((id) => id !== cityId)
  persistConfig()
}

function resetDefaultCities() {
  activeCityIds.value = [...DEFAULT_CITY_IDS]
  persistConfig()
}

// User Actions
function toggleSeconds() {
  showSeconds.value = !showSeconds.value
  persistConfig()
}

function toggleMilliseconds() {
  showMilliseconds.value = !showMilliseconds.value
  restartTimerLoop()
  persistConfig()
}

function toggle12Hour() {
  use12Hour.value = !use12Hour.value
  persistConfig()
}

function setDisplayMode(mode: 'dual' | 'digital' | 'analog') {
  displayMode.value = mode
  persistConfig()
}

// Persistence (Rust Backend + LocalStorage fallback)
async function loadConfig() {
  try {
    const res = await invoke<string | null>('get_clock_config')
    if (res) {
      const parsed = JSON.parse(res)
      if (typeof parsed.showSeconds === 'boolean') showSeconds.value = parsed.showSeconds
      if (typeof parsed.showMilliseconds === 'boolean') showMilliseconds.value = parsed.showMilliseconds
      if (typeof parsed.use12Hour === 'boolean') use12Hour.value = parsed.use12Hour
      if (['dual', 'digital', 'analog'].includes(parsed.displayMode)) displayMode.value = parsed.displayMode
      if (Array.isArray(parsed.activeCityIds)) activeCityIds.value = parsed.activeCityIds
      return
    }
  } catch (err) {
    // Web fallback
  }

  // LocalStorage fallback
  const localMs = localStorage.getItem('local_clock_ms') === 'true'
  const localSec = localStorage.getItem('local_clock_sec') !== 'false'
  const local12h = localStorage.getItem('local_clock_12h') === 'true'
  const localMode = localStorage.getItem('local_clock_mode') as 'dual' | 'digital' | 'analog'
  const localCitiesStr = localStorage.getItem('local_clock_cities')

  showMilliseconds.value = localMs
  showSeconds.value = localSec
  use12Hour.value = local12h
  if (['dual', 'digital', 'analog'].includes(localMode)) displayMode.value = localMode
  if (localCitiesStr) {
    try {
      activeCityIds.value = JSON.parse(localCitiesStr)
    } catch (_) {}
  }
}

async function persistConfig() {
  const config = {
    showSeconds: showSeconds.value,
    showMilliseconds: showMilliseconds.value,
    use12Hour: use12Hour.value,
    displayMode: displayMode.value,
    activeCityIds: activeCityIds.value
  }

  const jsonStr = JSON.stringify(config)

  // LocalStorage fallback update
  localStorage.setItem('local_clock_ms', String(showMilliseconds.value))
  localStorage.setItem('local_clock_sec', String(showSeconds.value))
  localStorage.setItem('local_clock_12h', String(use12Hour.value))
  localStorage.setItem('local_clock_mode', displayMode.value)
  localStorage.setItem('local_clock_cities', JSON.stringify(activeCityIds.value))

  try {
    await invoke('save_clock_config', { configJson: jsonStr })
  } catch (err) {
    // Ignore web fallback errors
  }
}

// High Precision Animation Loop
function updateTime() {
  now.value = new Date()
  if (showMilliseconds.value || displayMode.value === 'analog' || displayMode.value === 'dual') {
    animationFrameId = requestAnimationFrame(updateTime)
  }
}

function restartTimerLoop() {
  if (animationFrameId) {
    cancelAnimationFrame(animationFrameId)
    animationFrameId = null
  }
  if (intervalTimerId) {
    clearInterval(intervalTimerId)
    intervalTimerId = null
  }

  if (showMilliseconds.value || displayMode.value === 'analog' || displayMode.value === 'dual') {
    animationFrameId = requestAnimationFrame(updateTime)
  } else {
    intervalTimerId = setInterval(() => {
      now.value = new Date()
    }, 1000)
  }
}

onMounted(async () => {
  await loadConfig()
  restartTimerLoop()
})

onUnmounted(() => {
  if (animationFrameId) cancelAnimationFrame(animationFrameId)
  if (intervalTimerId) clearInterval(intervalTimerId)
})
</script>

<style scoped>
.local-clock-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: 24px;
  box-sizing: border-box;
  background: var(--bg-app);
  color: var(--text-main);
  overflow: hidden;
}

.clock-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  flex-wrap: wrap;
  gap: 16px;
}

.toolbar-left {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.page-title {
  display: flex;
  align-items: center;
  gap: 10px;
}

.page-title h2 {
  margin: 0;
  font-size: 1.4rem;
  font-weight: 700;
  letter-spacing: -0.02em;
}

.icon-primary {
  color: var(--primary);
}

.title-subtext {
  font-size: 0.85rem;
  color: var(--text-muted);
}

.toolbar-right {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.mode-toggle-group {
  display: flex;
  background: var(--bg-surface);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 3px;
  gap: 2px;
}

.mode-btn {
  display: flex;
  align-items: center;
  gap: 5px;
  background: transparent;
  border: none;
  color: var(--text-muted);
  padding: 5px 10px;
  border-radius: 6px;
  font-size: 0.8rem;
  cursor: pointer;
  transition: all 0.2s ease;
}

.mode-btn:hover {
  color: var(--text-main);
  background: var(--bg-hover);
}

.mode-btn.active {
  background: var(--primary);
  color: #ffffff;
  font-weight: 600;
}

.control-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  background: var(--bg-surface);
  border: 1px solid var(--border-color);
  color: var(--text-main);
  padding: 6px 12px;
  border-radius: 8px;
  font-size: 0.82rem;
  cursor: pointer;
  transition: all 0.2s ease;
}

.control-btn:hover {
  background: var(--bg-hover);
  border-color: var(--border-color-focus);
}

.control-btn.active {
  border-color: var(--primary);
  color: var(--primary);
  background: rgba(var(--primary-rgb), 0.1);
}

.btn-primary-sm {
  display: flex;
  align-items: center;
  gap: 6px;
  background: var(--primary);
  color: #fff;
  border: none;
  padding: 7px 14px;
  border-radius: 8px;
  font-size: 0.83rem;
  font-weight: 600;
  cursor: pointer;
  box-shadow: var(--shadow-sm);
  transition: all 0.2s ease;
}

.btn-primary-sm:hover {
  background: var(--primary-hover);
  transform: translateY(-1px);
  box-shadow: var(--shadow-md);
}

.clock-content-scroll {
  flex: 1;
  overflow-y: auto;
  padding-right: 4px;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

/* Hero Clock Card */
.hero-clock-card {
  position: relative;
  background: var(--bg-surface);
  border: 1px solid var(--border-color);
  border-radius: 20px;
  padding: 28px 32px;
  box-shadow: var(--shadow-md);
  overflow: hidden;
}

.hero-card-badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background: rgba(var(--primary-rgb), 0.1);
  border: 1px solid rgba(var(--primary-rgb), 0.2);
  padding: 6px 14px;
  border-radius: 20px;
  font-size: 0.85rem;
  margin-bottom: 20px;
}

.badge-text {
  font-weight: 600;
  color: var(--text-main);
}

.badge-offset {
  color: var(--primary);
  font-family: monospace;
}

.hero-main-content {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 48px;
}

/* Analog Clock SVG */
.analog-clock-wrapper {
  width: 180px;
  height: 180px;
  flex-shrink: 0;
}

.analog-clock-svg {
  width: 100%;
  height: 100%;
}

.clock-outer-circle {
  fill: var(--bg-card);
  stroke: var(--border-color);
  stroke-width: 4;
}

.clock-inner-circle {
  fill: var(--bg-app);
  stroke: rgba(var(--primary-rgb), 0.3);
  stroke-width: 1;
}

.hour-tick {
  stroke: var(--text-main);
  stroke-width: 2.5;
}

.minute-tick {
  stroke: var(--text-muted);
  stroke-width: 1;
}

.clock-number {
  fill: var(--text-main);
  font-size: 14px;
  font-weight: 700;
  font-family: system-ui, sans-serif;
}

.hand {
  stroke-linecap: round;
}

.hour-hand {
  stroke: var(--text-main);
  stroke-width: 4.5;
}

.minute-hand {
  stroke: var(--primary);
  stroke-width: 3;
}

.second-hand {
  stroke: #f43f5e;
  stroke-width: 1.5;
}

.center-pin {
  fill: #f43f5e;
}

.center-dot {
  fill: #fff;
}

/* Digital Clock */
.digital-clock-wrapper {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  justify-content: center;
}

.hero-time-display {
  display: flex;
  align-items: baseline;
  font-family: 'JetBrains Mono', 'Fira Code', ui-monospace, monospace;
  font-weight: 800;
  line-height: 1;
  margin-bottom: 12px;
}

.time-main {
  font-size: 4.2rem;
  letter-spacing: -0.04em;
  color: var(--text-main);
}

.time-seconds {
  font-size: 2.8rem;
  color: var(--primary);
}

.time-milliseconds {
  font-size: 1.8rem;
  color: var(--text-muted);
  width: 3.2ch;
}

.time-ampm {
  font-size: 1.4rem;
  margin-left: 12px;
  color: #d97706;
  font-weight: 700;
}

.hero-date-info {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 1.05rem;
  color: var(--text-muted);
}

.icon-muted {
  color: var(--text-muted);
}

.week-pill {
  background: var(--bg-hover);
  color: var(--text-main);
  padding: 3px 10px;
  border-radius: 6px;
  font-size: 0.85rem;
}

/* World Cities Section */
.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 10px;
}

.section-title h3 {
  margin: 0;
  font-size: 1.15rem;
  font-weight: 600;
}

.city-count-badge {
  background: rgba(var(--primary-rgb), 0.15);
  color: var(--primary);
  font-size: 0.75rem;
  padding: 2px 8px;
  border-radius: 12px;
  font-weight: 600;
}

.text-btn {
  background: none;
  border: none;
  color: var(--text-muted);
  font-size: 0.82rem;
  cursor: pointer;
  transition: color 0.2s ease;
}

.text-btn:hover {
  color: var(--primary);
}

.world-cities-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 16px;
}

.city-clock-card {
  position: relative;
  background: var(--bg-surface);
  border: 1px solid var(--border-color);
  border-radius: 14px;
  padding: 16px 18px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  transition: all 0.25s ease;
  box-shadow: var(--shadow-sm);
}

.city-clock-card:hover {
  transform: translateY(-2px);
  background: var(--bg-card-hover);
  border-color: var(--border-color-focus);
  box-shadow: var(--shadow-md);
}

.remove-city-btn {
  position: absolute;
  top: 12px;
  right: 12px;
  background: transparent;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  opacity: 0;
  transition: all 0.2s ease;
}

.city-clock-card:hover .remove-city-btn {
  opacity: 1;
}

.remove-city-btn:hover {
  color: #ef4444;
}

.city-header {
  display: flex;
  align-items: center;
  gap: 10px;
}

.city-flag {
  font-size: 1.6rem;
}

.city-name-box {
  display: flex;
  flex-direction: column;
}

.city-name {
  margin: 0;
  font-size: 0.95rem;
  font-weight: 600;
}

.city-tz {
  font-size: 0.75rem;
  color: var(--text-muted);
}

.city-time-display {
  font-family: 'JetBrains Mono', monospace;
  font-size: 1.7rem;
  font-weight: 700;
  color: var(--primary);
}

.city-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.78rem;
  color: var(--text-muted);
}

.city-offset-tag {
  color: var(--text-main);
}

.city-date-tag {
  color: var(--text-muted);
}

/* Modal */
.modal-backdrop {
  position: fixed;
  inset: 0;
  background: var(--bg-overlay);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-card {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 16px;
  width: 90%;
  max-width: 480px;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
  box-shadow: var(--shadow-lg);
  overflow: hidden;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border-color);
}

.modal-title {
  display: flex;
  align-items: center;
  gap: 8px;
}

.modal-title h3 {
  margin: 0;
  font-size: 1.1rem;
}

.close-btn {
  background: none;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
}

.close-btn:hover {
  color: var(--text-main);
}

.modal-body {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  overflow-y: auto;
}

.search-input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.search-icon {
  position: absolute;
  left: 12px;
  color: var(--text-muted);
}

.search-input {
  width: 100%;
  background: var(--bg-app);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 10px 12px 10px 36px;
  color: var(--text-main);
  font-size: 0.9rem;
  outline: none;
}

.search-input:focus {
  border-color: var(--primary);
}

.available-cities-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 320px;
  overflow-y: auto;
}

.available-city-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: var(--bg-app);
  border: 1px solid var(--border-color);
  padding: 10px 14px;
  border-radius: 10px;
}

.city-info-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.flag-lg {
  font-size: 1.4rem;
}

.name-meta {
  display: flex;
  flex-direction: column;
}

.c-name {
  font-size: 0.9rem;
  font-weight: 600;
}

.c-tz {
  font-size: 0.75rem;
  color: var(--text-muted);
}

.city-action-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.live-preview-time {
  font-family: monospace;
  font-size: 0.9rem;
  color: var(--primary);
}

.btn-add-action {
  background: rgba(var(--primary-rgb), 0.15);
  color: var(--primary);
  border: 1px solid rgba(var(--primary-rgb), 0.3);
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 0.8rem;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-add-action:hover:not(:disabled) {
  background: var(--primary);
  color: #ffffff;
}

.btn-add-action:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  border-color: transparent;
}

.empty-search {
  text-align: center;
  color: var(--text-muted);
  padding: 20px;
  font-size: 0.85rem;
}

/* Animations */
.animate-fade-in {
  animation: fadeIn 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}

.animate-scale-up {
  animation: scaleUp 0.25s cubic-bezier(0.16, 1, 0.3, 1);
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(6px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes scaleUp {
  from { opacity: 0; transform: scale(0.95); }
  to { opacity: 1; transform: scale(1); }
}
</style>

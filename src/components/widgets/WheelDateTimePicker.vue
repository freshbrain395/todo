<template>
  <div class="wheel-datetime-picker">
    <!-- Quick Selection Preset Tags -->
    <div class="quick-presets">
      <span class="preset-label"><Clock :size="12" /> 快捷设置:</span>
      <button type="button" class="preset-btn" @click="applyPreset(10, 'minute')">+10分钟</button>
      <button type="button" class="preset-btn" @click="applyPreset(30, 'minute')">+30分钟</button>
      <button type="button" class="preset-btn" @click="applyPreset(1, 'hour')">+1小时</button>
      <button type="button" class="preset-btn" @click="setTomorrowMorning()">明天 09:00</button>
    </div>

    <!-- 3D Wheel Container -->
    <div class="wheels-container">
      <!-- Highlighting Center Line Bar -->
      <div class="wheel-selection-indicator"></div>

      <!-- Mask Shadows for 3D Curve Feel -->
      <div class="wheel-mask top-mask"></div>
      <div class="wheel-mask bottom-mask"></div>

      <!-- Column 1: Year -->
      <div
        class="wheel-column"
        @wheel.prevent="onWheel($event, 'year')"
        @pointerdown="onPointerDown($event, 'year')"
        @pointermove="onPointerMove($event)"
        @pointerup="onPointerUp()"
        @pointercancel="onPointerUp()"
      >
        <div class="column-title">年</div>
        <div class="wheel-scroll-list" :style="getScrollStyle('year')">
          <div
            v-for="y in years"
            :key="'y-' + y"
            class="wheel-item"
            :class="{ active: selectedYear === y }"
            @click="selectValue('year', y)"
          >
            {{ y }}年
          </div>
        </div>
      </div>

      <!-- Column 2: Month -->
      <div
        class="wheel-column"
        @wheel.prevent="onWheel($event, 'month')"
        @pointerdown="onPointerDown($event, 'month')"
        @pointermove="onPointerMove($event)"
        @pointerup="onPointerUp()"
        @pointercancel="onPointerUp()"
      >
        <div class="column-title">月</div>
        <div class="wheel-scroll-list" :style="getScrollStyle('month')">
          <div
            v-for="m in months"
            :key="'m-' + m"
            class="wheel-item"
            :class="{ active: selectedMonth === m }"
            @click="selectValue('month', m)"
          >
            {{ formatNum(m) }}月
          </div>
        </div>
      </div>

      <!-- Column 3: Day -->
      <div
        class="wheel-column"
        @wheel.prevent="onWheel($event, 'day')"
        @pointerdown="onPointerDown($event, 'day')"
        @pointermove="onPointerMove($event)"
        @pointerup="onPointerUp()"
        @pointercancel="onPointerUp()"
      >
        <div class="column-title">日</div>
        <div class="wheel-scroll-list" :style="getScrollStyle('day')">
          <div
            v-for="d in days"
            :key="'d-' + d"
            class="wheel-item"
            :class="{ active: selectedDay === d }"
            @click="selectValue('day', d)"
          >
            {{ formatNum(d) }}日
          </div>
        </div>
      </div>

      <!-- Column 4: Hour -->
      <div
        class="wheel-column"
        @wheel.prevent="onWheel($event, 'hour')"
        @pointerdown="onPointerDown($event, 'hour')"
        @pointermove="onPointerMove($event)"
        @pointerup="onPointerUp()"
        @pointercancel="onPointerUp()"
      >
        <div class="column-title">时</div>
        <div class="wheel-scroll-list" :style="getScrollStyle('hour')">
          <div
            v-for="h in hours"
            :key="'h-' + h"
            class="wheel-item"
            :class="{ active: selectedHour === h }"
            @click="selectValue('hour', h)"
          >
            {{ formatNum(h) }}时
          </div>
        </div>
      </div>

      <!-- Column 5: Minute -->
      <div
        class="wheel-column"
        @wheel.prevent="onWheel($event, 'minute')"
        @pointerdown="onPointerDown($event, 'minute')"
        @pointermove="onPointerMove($event)"
        @pointerup="onPointerUp()"
        @pointercancel="onPointerUp()"
      >
        <div class="column-title">分</div>
        <div class="wheel-scroll-list" :style="getScrollStyle('minute')">
          <div
            v-for="min in minutes"
            :key="'min-' + min"
            class="wheel-item"
            :class="{ active: selectedMinute === min }"
            @click="selectValue('minute', min)"
          >
            {{ formatNum(min) }}分
          </div>
        </div>
      </div>
    </div>

    <!-- Current Formatted Time Preview Display -->
    <div class="formatted-preview">
      <Calendar :size="13" class="inline-icon" /> 选中提醒时间: <strong>{{ formattedDisplay }}</strong>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { Clock, Calendar } from 'lucide-vue-next'

const props = defineProps<{
  modelValue?: string
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: string): void
}>()

// Item height in pixels
const ITEM_HEIGHT = 36

// Date state
const currentYear = new Date().getFullYear()
const years = computed(() => [currentYear, currentYear + 1, currentYear + 2])
const months = Array.from({ length: 12 }, (_, i) => i + 1)
const hours = Array.from({ length: 24 }, (_, i) => i)
const minutes = Array.from({ length: 60 }, (_, i) => i)

const selectedYear = ref(currentYear)
const selectedMonth = ref(new Date().getMonth() + 1)
const selectedDay = ref(new Date().getDate())
const selectedHour = ref(new Date().getHours())
const selectedMinute = ref(new Date().getMinutes())

// Drag & Wheel Interaction State
type ColType = 'year' | 'month' | 'day' | 'hour' | 'minute'
const isDragging = ref(false)
const dragCol = ref<ColType | null>(null)
const startY = ref(0)
const dragOffset = ref(0)
const wheelAccumulators: Record<ColType, number> = {
  year: 0,
  month: 0,
  day: 0,
  hour: 0,
  minute: 0
}

// Calculate max days in selected year & month
const daysInMonth = computed(() => {
  return new Date(selectedYear.value, selectedMonth.value, 0).getDate()
})

const days = computed(() => {
  return Array.from({ length: daysInMonth.value }, (_, i) => i + 1)
})

// Keep day within valid range when month/year changes
watch(daysInMonth, (maxDays) => {
  if (selectedDay.value > maxDays) {
    selectedDay.value = maxDays
  }
})

// Parse incoming v-model string ("YYYY-MM-DDTHH:mm" or "YYYY-MM-DD HH:mm:ss")
function parseModelValue(val?: string) {
  if (!val) {
    const now = new Date()
    now.setMinutes(now.getMinutes() + 30) // Default 30 mins later
    selectedYear.value = now.getFullYear()
    selectedMonth.value = now.getMonth() + 1
    selectedDay.value = now.getDate()
    selectedHour.value = now.getHours()
    selectedMinute.value = now.getMinutes()
    return
  }

  const d = new Date(val.replace(' ', 'T'))
  if (!isNaN(d.getTime())) {
    selectedYear.value = d.getFullYear()
    selectedMonth.value = d.getMonth() + 1
    selectedDay.value = d.getDate()
    selectedHour.value = d.getHours()
    selectedMinute.value = d.getMinutes()
  }
}

// Compute Output Value in ISO datetime-local format ("YYYY-MM-DDTHH:mm")
const formattedIsoValue = computed(() => {
  const y = selectedYear.value
  const m = String(selectedMonth.value).padStart(2, '0')
  const d = String(selectedDay.value).padStart(2, '0')
  const h = String(selectedHour.value).padStart(2, '0')
  const min = String(selectedMinute.value).padStart(2, '0')
  return `${y}-${m}-${d}T${h}:${min}`
})

const formattedDisplay = computed(() => {
  const y = selectedYear.value
  const m = String(selectedMonth.value).padStart(2, '0')
  const d = String(selectedDay.value).padStart(2, '0')
  const h = String(selectedHour.value).padStart(2, '0')
  const min = String(selectedMinute.value).padStart(2, '0')
  return `${y}年${m}月${d}日 ${h}:${min}`
})

watch(formattedIsoValue, (newVal) => {
  emit('update:modelValue', newVal)
})

watch(
  () => props.modelValue,
  (newVal) => {
    if (newVal !== formattedIsoValue.value) {
      parseModelValue(newVal)
    }
  },
  { immediate: true }
)

onMounted(() => {
  parseModelValue(props.modelValue)
})

function formatNum(num: number): string {
  return String(num).padStart(2, '0')
}

// Compute wheel scroll offset for center alignment
function getScrollStyle(col: ColType) {
  let index = 0
  if (col === 'year') {
    index = years.value.indexOf(selectedYear.value)
  } else if (col === 'month') {
    index = months.indexOf(selectedMonth.value)
  } else if (col === 'day') {
    index = days.value.indexOf(selectedDay.value)
  } else if (col === 'hour') {
    index = hours.indexOf(selectedHour.value)
  } else if (col === 'minute') {
    index = minutes.indexOf(selectedMinute.value)
  }

  if (index < 0) index = 0
  let offsetY = -index * ITEM_HEIGHT

  if (isDragging.value && dragCol.value === col) {
    offsetY += dragOffset.value
  }

  return {
    transform: `translate3d(0, ${offsetY}px, 0)`,
    transition: isDragging.value && dragCol.value === col ? 'none' : 'transform 0.2s cubic-bezier(0.1, 0.9, 0.2, 1)'
  }
}

function stepValue(col: ColType, delta: number) {
  if (col === 'year') {
    const idx = years.value.indexOf(selectedYear.value)
    const nextIdx = Math.max(0, Math.min(years.value.length - 1, idx + delta))
    selectedYear.value = years.value[nextIdx]
  } else if (col === 'month') {
    const idx = months.indexOf(selectedMonth.value)
    const nextIdx = Math.max(0, Math.min(months.length - 1, idx + delta))
    selectedMonth.value = months[nextIdx]
  } else if (col === 'day') {
    const idx = days.value.indexOf(selectedDay.value)
    const nextIdx = Math.max(0, Math.min(days.value.length - 1, idx + delta))
    selectedDay.value = days.value[nextIdx]
  } else if (col === 'hour') {
    const idx = hours.indexOf(selectedHour.value)
    const nextIdx = Math.max(0, Math.min(hours.length - 1, idx + delta))
    selectedHour.value = hours[nextIdx]
  } else if (col === 'minute') {
    const idx = minutes.indexOf(selectedMinute.value)
    const nextIdx = Math.max(0, Math.min(minutes.length - 1, idx + delta))
    selectedMinute.value = minutes[nextIdx]
  }
}

// Handle Mouse Wheel Event with smoothing accumulator
function onWheel(event: WheelEvent, col: ColType) {
  wheelAccumulators[col] += event.deltaY
  const THRESHOLD = 35

  if (Math.abs(wheelAccumulators[col]) >= THRESHOLD) {
    const delta = wheelAccumulators[col] > 0 ? 1 : -1
    wheelAccumulators[col] = 0
    stepValue(col, delta)
  }
}

// Dragging Pointer Events
function onPointerDown(e: PointerEvent, col: ColType) {
  isDragging.value = true
  dragCol.value = col
  startY.value = e.clientY
  dragOffset.value = 0
  try {
    ;(e.currentTarget as HTMLElement).setPointerCapture(e.pointerId)
  } catch {}
}

function onPointerMove(e: PointerEvent) {
  if (!isDragging.value || !dragCol.value) return
  dragOffset.value = e.clientY - startY.value
}

function onPointerUp() {
  if (!isDragging.value || !dragCol.value) return
  const col = dragCol.value
  const offset = dragOffset.value
  isDragging.value = false
  dragCol.value = null
  dragOffset.value = 0

  const steps = -Math.round(offset / ITEM_HEIGHT)
  if (steps !== 0) {
    stepValue(col, steps)
  }
}

function selectValue(col: ColType, val: number) {
  if (col === 'year') selectedYear.value = val
  if (col === 'month') selectedMonth.value = val
  if (col === 'day') selectedDay.value = val
  if (col === 'hour') selectedHour.value = val
  if (col === 'minute') selectedMinute.value = val
}

// Apply Quick Presets
function applyPreset(amount: number, unit: 'minute' | 'hour') {
  const now = new Date()
  if (unit === 'minute') {
    now.setMinutes(now.getMinutes() + amount)
  } else if (unit === 'hour') {
    now.setHours(now.getHours() + amount)
  }
  selectedYear.value = now.getFullYear()
  selectedMonth.value = now.getMonth() + 1
  selectedDay.value = now.getDate()
  selectedHour.value = now.getHours()
  selectedMinute.value = now.getMinutes()
}

function setTomorrowMorning() {
  const tomorrow = new Date()
  tomorrow.setDate(tomorrow.getDate() + 1)
  tomorrow.setHours(9, 0, 0, 0)
  selectedYear.value = tomorrow.getFullYear()
  selectedMonth.value = tomorrow.getMonth() + 1
  selectedDay.value = tomorrow.getDate()
  selectedHour.value = 9
  selectedMinute.value = 0
}
</script>

<style scoped>
.wheel-datetime-picker {
  display: flex;
  flex-direction: column;
  gap: 10px;
  background-color: var(--bg-app);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  padding: 12px;
  user-select: none;
}

.quick-presets {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}

.preset-label {
  font-size: 11px;
  color: var(--text-muted);
  font-weight: 600;
}

.preset-btn {
  background-color: var(--bg-surface);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 2px 8px;
  font-size: 11px;
  color: var(--primary);
  cursor: pointer;
  transition: all 0.2s;
}

.preset-btn:hover {
  background-color: var(--primary);
  color: #ffffff;
  border-color: var(--primary);
}

.wheels-container {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: space-around;
  height: 180px;
  overflow: hidden;
  background-color: var(--bg-surface);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  touch-action: none;
}

.wheel-selection-indicator {
  position: absolute;
  top: 50%;
  left: 6px;
  right: 6px;
  height: 36px;
  transform: translateY(-50%);
  background-color: rgba(66, 153, 225, 0.12);
  border-top: 1.5px solid var(--primary);
  border-bottom: 1.5px solid var(--primary);
  border-radius: 6px;
  pointer-events: none;
  z-index: 2;
}

.wheel-mask {
  position: absolute;
  left: 0;
  right: 0;
  height: 70px;
  pointer-events: none;
  z-index: 3;
}

.top-mask {
  top: 0;
  background: linear-gradient(to bottom, var(--bg-surface) 10%, transparent 100%);
}

.bottom-mask {
  bottom: 0;
  background: linear-gradient(to top, var(--bg-surface) 10%, transparent 100%);
}

.wheel-column {
  position: relative;
  flex: 1;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  cursor: grab;
  touch-action: none;
}

.wheel-column:active {
  cursor: grabbing;
}

.column-title {
  position: absolute;
  top: 4px;
  font-size: 10px;
  color: var(--text-muted);
  font-weight: 700;
  z-index: 4;
}

.wheel-scroll-list {
  position: absolute;
  top: 50%;
  margin-top: -18px; /* Offset by half item height */
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  will-change: transform;
}

.wheel-item {
  height: 36px;
  line-height: 36px;
  font-size: 13px;
  color: var(--text-muted);
  cursor: pointer;
  transition: all 0.2s;
  opacity: 0.45;
  transform: scale(0.9);
}

.wheel-item.active {
  color: var(--primary);
  font-weight: 700;
  font-size: 14px;
  opacity: 1;
  transform: scale(1.1);
}

.wheel-divider {
  font-size: 16px;
  font-weight: 800;
  color: var(--primary);
  z-index: 4;
  margin-top: 10px;
}

.formatted-preview {
  font-size: 12px;
  color: var(--text-main);
  text-align: center;
  padding: 4px 8px;
  background-color: var(--bg-surface);
  border-radius: 4px;
  border: 1px dashed var(--border-color);
}
</style>

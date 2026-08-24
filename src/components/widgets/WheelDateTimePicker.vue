<template>
  <div class="wheel-datetime-picker">
    <!-- Header: Quick Presets & 12h/24h Mode Switch -->
    <div class="picker-top-bar">
      <div class="quick-presets">
        <span class="preset-label"><Clock :size="12" /> 快捷:</span>
        <button type="button" class="preset-btn" @click="applyPreset(10, 'minute')">+10分钟</button>
        <button type="button" class="preset-btn" @click="applyPreset(30, 'minute')">+30分钟</button>
        <button type="button" class="preset-btn" @click="applyPreset(1, 'hour')">+1小时</button>
        <button type="button" class="preset-btn" @click="setTime(9, 0, 0)">09:00</button>
        <button type="button" class="preset-btn" @click="setTime(18, 0, 0)">18:00</button>
        <button type="button" class="preset-btn" @click="setTime(20, 0, 0)">20:00</button>
      </div>

      <!-- 12h / 24h Toggle Pill -->
      <button
        type="button"
        class="time-format-toggle"
        @click="use12Hour = !use12Hour"
        :title="use12Hour ? '切换为24小时制' : '切换为12小时制'"
      >
        <span>{{ use12Hour ? '12小时制' : '24小时制' }}</span>
      </button>
    </div>

    <!-- 3D Wheel Container: Hour, Minute, Second -->
    <div class="wheels-container">
      <!-- Highlighting Center Line Bar -->
      <div class="wheel-selection-indicator"></div>

      <!-- Mask Shadows for 3D Curve Feel -->
      <div class="wheel-mask top-mask"></div>
      <div class="wheel-mask bottom-mask"></div>

      <!-- Column 1 (Optional in 12h mode): AM / PM -->
      <div
        v-if="use12Hour"
        class="wheel-column col-ampm"
        @wheel.prevent="onWheel($event, 'ampm')"
        @pointerdown="onPointerDown($event, 'ampm')"
        @pointermove="onPointerMove($event)"
        @pointerup="onPointerUp()"
        @pointercancel="onPointerUp()"
      >
        <div class="column-title">时段</div>
        <div class="wheel-scroll-list" :style="getScrollStyle('ampm')">
          <div
            v-for="p in ['AM', 'PM']"
            :key="'p-' + p"
            class="wheel-item"
            :class="{ active: ampm === p }"
            @click="ampm = (p as 'AM' | 'PM')"
          >
            {{ p === 'AM' ? '上午' : '下午' }}
          </div>
        </div>
      </div>

      <!-- Column 2: Hour -->
      <div
        class="wheel-column col-hour"
        @wheel.prevent="onWheel($event, 'hour')"
        @pointerdown="onPointerDown($event, 'hour')"
        @pointermove="onPointerMove($event)"
        @pointerup="onPointerUp()"
        @pointercancel="onPointerUp()"
      >
        <div class="column-title">时</div>
        <div class="wheel-scroll-list" :style="getScrollStyle('hour')">
          <div
            v-for="h in displayHours"
            :key="'h-' + h"
            class="wheel-item"
            :class="{ active: currentDisplayHour === h }"
            @click="selectHourValue(h)"
          >
            {{ formatNum(h) }}时
          </div>
        </div>
      </div>

      <!-- Column 3: Minute -->
      <div
        class="wheel-column col-minute"
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
            @click="selectedMinute = min"
          >
            {{ formatNum(min) }}分
          </div>
        </div>
      </div>

      <!-- Column 4: Second -->
      <div
        class="wheel-column col-second"
        @wheel.prevent="onWheel($event, 'second')"
        @pointerdown="onPointerDown($event, 'second')"
        @pointermove="onPointerMove($event)"
        @pointerup="onPointerUp()"
        @pointercancel="onPointerUp()"
      >
        <div class="column-title">秒</div>
        <div class="wheel-scroll-list" :style="getScrollStyle('second')">
          <div
            v-for="sec in seconds"
            :key="'sec-' + sec"
            class="wheel-item"
            :class="{ active: selectedSecond === sec }"
            @click="selectedSecond = sec"
          >
            {{ formatNum(sec) }}秒
          </div>
        </div>
      </div>
    </div>

    <!-- Current Formatted Time Preview Display -->
    <div class="formatted-preview">
      <Clock :size="13" class="inline-icon" /> 提醒时刻: <strong>{{ formattedDisplay }}</strong>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { Clock } from 'lucide-vue-next'

const props = defineProps<{
  modelValue?: string
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: string): void
}>()

// Item height in pixels
const ITEM_HEIGHT = 36

const hours24 = Array.from({ length: 24 }, (_, i) => i)
const hours12 = Array.from({ length: 12 }, (_, i) => i === 0 ? 12 : i)
const minutes = Array.from({ length: 60 }, (_, i) => i)
const seconds = Array.from({ length: 60 }, (_, i) => i)

// Detect system 12h vs 24h format
function detectSystem12Hour(): boolean {
  try {
    const d = new Date(2026, 0, 1, 13, 0, 0)
    const formatted = new Intl.DateTimeFormat(undefined, { hour: 'numeric' }).format(d)
    return !formatted.includes('13')
  } catch {
    return false
  }
}

const use12Hour = ref(detectSystem12Hour())
const ampm = ref<'AM' | 'PM'>('AM')

// Internal Base Date (defaults to today)
const baseYear = ref(new Date().getFullYear())
const baseMonth = ref(new Date().getMonth() + 1)
const baseDay = ref(new Date().getDate())

const selectedHour = ref(new Date().getHours())
const selectedMinute = ref(new Date().getMinutes())
const selectedSecond = ref(0)

// Sync ampm with selectedHour
watch(selectedHour, (h) => {
  ampm.value = h >= 12 ? 'PM' : 'AM'
}, { immediate: true })

// Display hours depending on 12h vs 24h mode
const displayHours = computed(() => use12Hour.value ? hours12 : hours24)
const currentDisplayHour = computed(() => {
  if (!use12Hour.value) return selectedHour.value
  const h = selectedHour.value % 12
  return h === 0 ? 12 : h
})

function selectHourValue(h: number) {
  if (!use12Hour.value) {
    selectedHour.value = h
    return
  }
  // 12-hour calculation
  if (ampm.value === 'AM') {
    selectedHour.value = h === 12 ? 0 : h
  } else {
    selectedHour.value = h === 12 ? 12 : h + 12
  }
}

watch(ampm, (newAmpm) => {
  if (!use12Hour.value) return
  const current12 = currentDisplayHour.value
  if (newAmpm === 'AM') {
    selectedHour.value = current12 === 12 ? 0 : current12
  } else {
    selectedHour.value = current12 === 12 ? 12 : current12 + 12
  }
})

// Drag & Wheel Interaction State
type ColType = 'hour' | 'minute' | 'second' | 'ampm'
const isDragging = ref(false)
const dragCol = ref<ColType | null>(null)
const startY = ref(0)
const dragOffset = ref(0)
const wheelAccumulators: Record<ColType, number> = {
  hour: 0,
  minute: 0,
  second: 0,
  ampm: 0
}

function parseModelValue(val?: string) {
  if (!val) {
    const now = new Date()
    now.setMinutes(now.getMinutes() + 30)
    baseYear.value = now.getFullYear()
    baseMonth.value = now.getMonth() + 1
    baseDay.value = now.getDate()
    selectedHour.value = now.getHours()
    selectedMinute.value = now.getMinutes()
    selectedSecond.value = 0
    return
  }

  // Handle both "HH:mm" / "HH:mm:ss" and "YYYY-MM-DDTHH:mm:ss"
  if (val.includes(':') && !val.includes('-')) {
    const parts = val.split(':')
    selectedHour.value = parseInt(parts[0], 10) || 0
    selectedMinute.value = parseInt(parts[1], 10) || 0
    selectedSecond.value = parseInt(parts[2], 10) || 0
    return
  }

  const d = new Date(val.replace(' ', 'T'))
  if (!isNaN(d.getTime())) {
    baseYear.value = d.getFullYear()
    baseMonth.value = d.getMonth() + 1
    baseDay.value = d.getDate()
    selectedHour.value = d.getHours()
    selectedMinute.value = d.getMinutes()
    selectedSecond.value = d.getSeconds()
  }
}

const formattedIsoValue = computed(() => {
  const y = baseYear.value
  const m = String(baseMonth.value).padStart(2, '0')
  const d = String(baseDay.value).padStart(2, '0')
  const h = String(selectedHour.value).padStart(2, '0')
  const min = String(selectedMinute.value).padStart(2, '0')
  const sec = String(selectedSecond.value).padStart(2, '0')
  return `${y}-${m}-${d}T${h}:${min}:${sec}`
})

const formattedDisplay = computed(() => {
  const min = String(selectedMinute.value).padStart(2, '0')
  const sec = String(selectedSecond.value).padStart(2, '0')

  if (use12Hour.value) {
    const period = ampm.value === 'AM' ? '上午' : '下午'
    const h12 = String(currentDisplayHour.value).padStart(2, '0')
    return `${period} ${h12}:${min}:${sec}`
  }
  const h24 = String(selectedHour.value).padStart(2, '0')
  return `${h24}:${min}:${sec}`
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

function getScrollStyle(col: ColType) {
  let index = 0
  if (col === 'ampm') {
    index = ampm.value === 'AM' ? 0 : 1
  } else if (col === 'hour') {
    index = displayHours.value.indexOf(currentDisplayHour.value)
  } else if (col === 'minute') {
    index = minutes.indexOf(selectedMinute.value)
  } else if (col === 'second') {
    index = seconds.indexOf(selectedSecond.value)
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
  if (col === 'ampm') {
    ampm.value = ampm.value === 'AM' ? 'PM' : 'AM'
  } else if (col === 'hour') {
    const list = displayHours.value
    const idx = list.indexOf(currentDisplayHour.value)
    const nextIdx = Math.max(0, Math.min(list.length - 1, idx + delta))
    selectHourValue(list[nextIdx])
  } else if (col === 'minute') {
    const idx = minutes.indexOf(selectedMinute.value)
    const nextIdx = Math.max(0, Math.min(minutes.length - 1, idx + delta))
    selectedMinute.value = minutes[nextIdx]
  } else if (col === 'second') {
    const idx = seconds.indexOf(selectedSecond.value)
    const nextIdx = Math.max(0, Math.min(seconds.length - 1, idx + delta))
    selectedSecond.value = seconds[nextIdx]
  }
}

function onWheel(event: WheelEvent, col: ColType) {
  wheelAccumulators[col] += event.deltaY
  const THRESHOLD = 35

  if (Math.abs(wheelAccumulators[col]) >= THRESHOLD) {
    const delta = wheelAccumulators[col] > 0 ? 1 : -1
    wheelAccumulators[col] = 0
    stepValue(col, delta)
  }
}

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

function applyPreset(amount: number, unit: 'minute' | 'hour') {
  const now = new Date()
  if (unit === 'minute') {
    now.setMinutes(now.getMinutes() + amount)
  } else if (unit === 'hour') {
    now.setHours(now.getHours() + amount)
  }
  selectedHour.value = now.getHours()
  selectedMinute.value = now.getMinutes()
  selectedSecond.value = 0
}

function setTime(h: number, m: number, s: number) {
  selectedHour.value = h
  selectedMinute.value = m
  selectedSecond.value = s
}
</script>

<style scoped>
.wheel-datetime-picker {
  display: flex;
  flex-direction: column;
  gap: 12px;
  background-color: var(--bg-surface, #ffffff);
  border: 1px solid var(--border-color, #e2e8f0);
  border-radius: 16px;
  padding: 16px;
  user-select: none;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.04);
}

.picker-top-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  flex-wrap: wrap;
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
  font-weight: 700;
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.preset-btn {
  background-color: var(--bg-app, #f8fafc);
  border: 1px solid var(--border-color, #e2e8f0);
  border-radius: 20px;
  padding: 3px 10px;
  font-size: 11px;
  font-weight: 600;
  color: var(--primary, #3b82f6);
  cursor: pointer;
  transition: all 0.2s ease;
}

.preset-btn:hover {
  background-color: var(--primary, #3b82f6);
  color: #ffffff;
  border-color: var(--primary, #3b82f6);
  transform: translateY(-1px);
}

.time-format-toggle {
  background: var(--bg-app, #f1f5f9);
  border: 1px solid var(--border-color, #e2e8f0);
  border-radius: 20px;
  padding: 3px 10px;
  font-size: 11px;
  font-weight: 700;
  color: var(--text-main, #334155);
  cursor: pointer;
  transition: all 0.2s ease;
}

.time-format-toggle:hover {
  border-color: var(--primary, #3b82f6);
  color: var(--primary, #3b82f6);
}

.wheels-container {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: space-around;
  height: 190px;
  overflow: hidden;
  background-color: var(--bg-app, #f8fafc);
  border: 1px solid var(--border-color, #e2e8f0);
  border-radius: 12px;
  touch-action: none;
}

.wheel-selection-indicator {
  position: absolute;
  top: 50%;
  left: 6px;
  right: 6px;
  height: 36px;
  transform: translateY(-50%);
  background-color: rgba(59, 130, 246, 0.1);
  border-top: 1.5px solid var(--primary, #3b82f6);
  border-bottom: 1.5px solid var(--primary, #3b82f6);
  border-radius: 8px;
  pointer-events: none;
  z-index: 2;
}

.wheel-mask {
  position: absolute;
  left: 0;
  right: 0;
  height: 75px;
  pointer-events: none;
  z-index: 3;
}

.top-mask {
  top: 0;
  background: linear-gradient(to bottom, var(--bg-app, #f8fafc) 20%, transparent 100%);
}

.bottom-mask {
  bottom: 0;
  background: linear-gradient(to top, var(--bg-app, #f8fafc) 20%, transparent 100%);
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

.wheel-column.col-ampm {
  flex: 1;
}

.wheel-column.col-hour {
  flex: 1.2;
}

.wheel-column.col-minute {
  flex: 1.2;
}

.wheel-column.col-second {
  flex: 1.2;
}

.wheel-column:active {
  cursor: grabbing;
}

.column-title {
  position: absolute;
  top: 4px;
  font-size: 10px;
  color: var(--text-muted);
  font-weight: 800;
  z-index: 4;
}

.wheel-scroll-list {
  position: absolute;
  top: 50%;
  margin-top: -18px;
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  will-change: transform;
}

.wheel-item {
  height: 36px;
  line-height: 36px;
  font-size: 13.5px;
  color: var(--text-muted, #64748b);
  cursor: pointer;
  transition: all 0.2s;
  opacity: 0.45;
  transform: scale(0.9);
  white-space: nowrap;
}

.wheel-item.active {
  color: var(--primary, #3b82f6);
  font-weight: 800;
  font-size: 15px;
  opacity: 1;
  transform: scale(1.1);
}

.formatted-preview {
  font-size: 12.5px;
  color: var(--text-main, #0f172a);
  text-align: center;
  padding: 8px 12px;
  background-color: var(--bg-app, #f8fafc);
  border-radius: 8px;
  border: 1px dashed var(--border-color, #e2e8f0);
}
</style>

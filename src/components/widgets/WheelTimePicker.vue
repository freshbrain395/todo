<template>
  <div class="wheel-time-picker">
    <!-- Quick Time Preset Chips -->
    <div class="quick-presets">
      <span class="preset-label"><Clock :size="12" /> 常用时刻:</span>
      <button type="button" class="preset-btn" @click="setTimePreset('07', '00')">07:00</button>
      <button type="button" class="preset-btn" @click="setTimePreset('08', '30')">08:30</button>
      <button type="button" class="preset-btn" @click="setTimePreset('12', '00')">12:00</button>
      <button type="button" class="preset-btn" @click="setTimePreset('18', '00')">18:00</button>
      <button type="button" class="preset-btn" @click="setTimePreset('22', '30')">22:30</button>
    </div>

    <!-- 3D Wheel Container -->
    <div class="wheels-container">
      <!-- Highlighting Center Selection Indicator -->
      <div class="wheel-selection-indicator"></div>

      <!-- Mask Shadows for 3D Curve Feel -->
      <div class="wheel-mask top-mask"></div>
      <div class="wheel-mask bottom-mask"></div>

      <!-- Column 1: Hour (00 - 23) -->
      <div
        class="wheel-column"
        @wheel.prevent="onWheel($event, 'hour')"
        @pointerdown="onPointerDown($event, 'hour')"
        @pointermove="onPointerMove($event)"
        @pointerup="onPointerUp()"
        @pointercancel="onPointerUp()"
      >
        <div class="column-title">时 (Hour)</div>
        <div class="wheel-scroll-list" :style="getScrollStyle('hour')">
          <div
            v-for="h in hours"
            :key="'h-' + h"
            class="wheel-item"
            :class="{ active: selectedHour === h }"
            @click="selectValue('hour', h)"
          >
            {{ formatNum(h) }}
          </div>
        </div>
      </div>



      <!-- Column 2: Minute (00 - 59) -->
      <div
        class="wheel-column"
        @wheel.prevent="onWheel($event, 'minute')"
        @pointerdown="onPointerDown($event, 'minute')"
        @pointermove="onPointerMove($event)"
        @pointerup="onPointerUp()"
        @pointercancel="onPointerUp()"
      >
        <div class="column-title">分 (Minute)</div>
        <div class="wheel-scroll-list" :style="getScrollStyle('minute')">
          <div
            v-for="m in minutes"
            :key="'m-' + m"
            class="wheel-item"
            :class="{ active: selectedMinute === m }"
            @click="selectValue('minute', m)"
          >
            {{ formatNum(m) }}
          </div>
        </div>
      </div>
    </div>

    <!-- Display Badge -->
    <div class="time-display-badge">
      <span class="badge-label">设定响铃时间：</span>
      <span class="badge-value">{{ formattedDisplay }}</span>
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

const ITEM_HEIGHT = 40

const hours = Array.from({ length: 24 }, (_, i) => i)
const minutes = Array.from({ length: 60 }, (_, i) => i)

const selectedHour = ref(8)
const selectedMinute = ref(0)

// Drag & Wheel Interaction
type ColType = 'hour' | 'minute'
const isDragging = ref(false)
const dragCol = ref<ColType | null>(null)
const startY = ref(0)
const dragOffset = ref(0)
const wheelAccumulators: Record<ColType, number> = {
  hour: 0,
  minute: 0
}

function parseModelValue(val?: string) {
  if (!val) {
    selectedHour.value = 8
    selectedMinute.value = 0
    return
  }
  const parts = val.split(':')
  if (parts.length >= 2) {
    const h = parseInt(parts[0], 10)
    const m = parseInt(parts[1], 10)
    if (!isNaN(h) && h >= 0 && h < 24) selectedHour.value = h
    if (!isNaN(m) && m >= 0 && m < 60) selectedMinute.value = m
  }
}

const formattedDisplay = computed(() => {
  return `${formatNum(selectedHour.value)}:${formatNum(selectedMinute.value)}`
})

watch(formattedDisplay, (newVal) => {
  emit('update:modelValue', newVal)
})

watch(
  () => props.modelValue,
  (newVal) => {
    if (newVal && newVal !== formattedDisplay.value) {
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
  if (col === 'hour') {
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
  if (col === 'hour') {
    const idx = hours.indexOf(selectedHour.value)
    const nextIdx = (idx + delta + 24) % 24
    selectedHour.value = hours[nextIdx]
  } else if (col === 'minute') {
    const idx = minutes.indexOf(selectedMinute.value)
    const nextIdx = (idx + delta + 60) % 60
    selectedMinute.value = minutes[nextIdx]
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

function selectValue(col: ColType, val: number) {
  if (col === 'hour') selectedHour.value = val
  if (col === 'minute') selectedMinute.value = val
}

function setTimePreset(hStr: string, mStr: string) {
  selectedHour.value = parseInt(hStr, 10)
  selectedMinute.value = parseInt(mStr, 10)
}
</script>

<style scoped>
.wheel-time-picker {
  display: flex;
  flex-direction: column;
  gap: 12px;
  width: 100%;
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
  display: flex;
  align-items: center;
  gap: 4px;
  margin-right: 2px;
}

.preset-btn {
  background-color: var(--bg-surface);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 3px 8px;
  font-size: 11px;
  color: var(--text-main);
  cursor: pointer;
  transition: all 0.2s ease;
}

.preset-btn:hover {
  border-color: var(--primary);
  color: var(--primary);
}

.wheels-container {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  height: 180px;
  background-color: var(--bg-app);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  overflow: hidden;
}

.wheel-selection-indicator {
  position: absolute;
  top: 50%;
  left: 10%;
  right: 10%;
  height: 40px;
  transform: translateY(-50%);
  background-color: rgba(49, 130, 206, 0.08);
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
  height: 65px;
  pointer-events: none;
  z-index: 3;
}

.top-mask {
  top: 0;
  background: linear-gradient(to bottom, var(--bg-app) 10%, rgba(0,0,0,0) 100%);
}

.bottom-mask {
  bottom: 0;
  background: linear-gradient(to top, var(--bg-app) 10%, rgba(0,0,0,0) 100%);
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
  top: 6px;
  font-size: 10px;
  font-weight: 700;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  z-index: 4;
}

.wheel-scroll-list {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding-top: 70px; /* Center item offset */
  will-change: transform;
}

.wheel-item {
  height: 40px;
  line-height: 40px;
  font-size: 18px;
  font-weight: 600;
  color: var(--text-muted);
  opacity: 0.45;
  transition: opacity 0.2s, color 0.2s, transform 0.2s;
  cursor: pointer;
}

.wheel-item.active {
  color: var(--primary);
  font-weight: 800;
  font-size: 22px;
  opacity: 1;
  transform: scale(1.15);
}

.wheel-divider {
  font-size: 24px;
  font-weight: 800;
  color: var(--primary);
  padding: 0 4px;
  z-index: 4;
  margin-top: 10px;
}

.time-display-badge {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  background-color: var(--bg-surface);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  font-size: 12px;
}

.badge-label {
  color: var(--text-muted);
}

.badge-value {
  font-size: 16px;
  font-weight: 800;
  color: var(--primary);
  font-family: 'Outfit', 'Inter', monospace;
}
</style>

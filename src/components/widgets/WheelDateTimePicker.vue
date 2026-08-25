<template>
  <div class="manual-datetime-picker">
    <!-- Quick Preset Buttons -->
    <div class="quick-presets">
      <span class="preset-label"><Clock :size="12" /> 快捷选择:</span>
      <button type="button" class="preset-btn" @click="addMinutes(10)">+10分钟</button>
      <button type="button" class="preset-btn" @click="addMinutes(30)">+30分钟</button>
      <button type="button" class="preset-btn" @click="addHours(1)">+1小时</button>
      <button type="button" class="preset-btn" @click="setTonight()">今晚 20:00</button>
      <button type="button" class="preset-btn" @click="setTomorrowMorning()">明天 09:00</button>
    </div>

    <!-- Manual Input Fields Group -->
    <div class="manual-input-group">
      <label class="field-label">手动输入或选择提醒时间</label>
      <div class="input-with-icon">
        <Calendar :size="16" class="input-icon" />
        <input
          type="datetime-local"
          v-model="internalValue"
          class="manual-input"
          step="1"
        />
      </div>
    </div>

    <!-- Formatted Display -->
    <div v-if="internalValue" class="formatted-preview">
      <Clock :size="13" class="inline-icon" /> 设定提醒时间: <strong>{{ formatDisplay(internalValue) }}</strong>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import { Clock, Calendar } from 'lucide-vue-next'

const props = defineProps<{
  modelValue?: string
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: string): void
}>()

const internalValue = ref('')

function formatToInputString(date: Date): string {
  const y = date.getFullYear()
  const m = String(date.getMonth() + 1).padStart(2, '0')
  const d = String(date.getDate()).padStart(2, '0')
  const h = String(date.getHours()).padStart(2, '0')
  const min = String(date.getMinutes()).padStart(2, '0')
  const sec = String(date.getSeconds()).padStart(2, '0')
  return `${y}-${m}-${d}T${h}:${min}:${sec}`
}

function parseValue(val?: string) {
  if (!val) {
    const d = new Date()
    d.setMinutes(d.getMinutes() + 30)
    internalValue.value = formatToInputString(d)
    return
  }
  const clean = val.replace(' ', 'T')
  if (clean.length === 16) {
    internalValue.value = clean + ':00'
  } else {
    internalValue.value = clean
  }
}

watch(
  () => props.modelValue,
  (newVal) => {
    if (newVal !== internalValue.value) {
      parseValue(newVal)
    }
  },
  { immediate: true }
)

watch(internalValue, (newVal) => {
  emit('update:modelValue', newVal)
})

onMounted(() => {
  if (!props.modelValue) {
    parseValue()
  }
})

function addMinutes(mins: number) {
  const d = new Date(internalValue.value ? internalValue.value.replace(' ', 'T') : Date.now())
  if (isNaN(d.getTime())) {
    const now = new Date()
    now.setMinutes(now.getMinutes() + mins)
    internalValue.value = formatToInputString(now)
  } else {
    d.setMinutes(d.getMinutes() + mins)
    internalValue.value = formatToInputString(d)
  }
}

function addHours(hrs: number) {
  const d = new Date(internalValue.value ? internalValue.value.replace(' ', 'T') : Date.now())
  if (isNaN(d.getTime())) {
    const now = new Date()
    now.setHours(now.getHours() + hrs)
    internalValue.value = formatToInputString(now)
  } else {
    d.setHours(d.getHours() + hrs)
    internalValue.value = formatToInputString(d)
  }
}

function setTonight() {
  const now = new Date()
  now.setHours(20, 0, 0, 0)
  if (now.getTime() < Date.now()) {
    now.setDate(now.getDate() + 1)
  }
  internalValue.value = formatToInputString(now)
}

function setTomorrowMorning() {
  const tomorrow = new Date()
  tomorrow.setDate(tomorrow.getDate() + 1)
  tomorrow.setHours(9, 0, 0, 0)
  internalValue.value = formatToInputString(tomorrow)
}

function formatDisplay(val: string): string {
  try {
    const d = new Date(val.replace(' ', 'T'))
    if (isNaN(d.getTime())) return val
    const y = d.getFullYear()
    const m = String(d.getMonth() + 1).padStart(2, '0')
    const date = String(d.getDate()).padStart(2, '0')
    const h = String(d.getHours()).padStart(2, '0')
    const min = String(d.getMinutes()).padStart(2, '0')
    const sec = String(d.getSeconds()).padStart(2, '0')
    return `${y}年${m}月${date}日 ${h}:${min}:${sec}`
  } catch {
    return val
  }
}
</script>

<style scoped>
.manual-datetime-picker {
  display: flex;
  flex-direction: column;
  gap: 12px;
  background-color: var(--bg-surface, #ffffff);
  border: 1px solid var(--border-color, #e2e8f0);
  border-radius: 14px;
  padding: 16px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.03);
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
  padding: 4px 10px;
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

.manual-input-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.field-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-muted, #64748b);
}

.input-with-icon {
  position: relative;
  display: flex;
  align-items: center;
}

.input-icon {
  position: absolute;
  left: 12px;
  color: var(--primary, #3b82f6);
  pointer-events: none;
}

.manual-input {
  width: 100%;
  padding: 10px 14px 10px 38px;
  font-size: 14px;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-weight: 600;
  border: 1px solid var(--border-color, #e2e8f0);
  border-radius: 10px;
  background-color: var(--bg-app, #f8fafc);
  color: var(--text-main, #0f172a);
  outline: none;
  transition: all 0.2s ease;
  box-sizing: border-box;
}

.manual-input:focus {
  border-color: var(--primary, #3b82f6);
  background-color: var(--bg-surface, #ffffff);
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.12);
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

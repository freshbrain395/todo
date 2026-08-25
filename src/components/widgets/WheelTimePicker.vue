<template>
  <div class="manual-time-picker">
    <!-- Quick Time Preset Chips -->
    <div class="quick-presets">
      <span class="preset-label"><Clock :size="12" /> 常用时刻:</span>
      <button type="button" class="preset-btn" @click="setTimePreset('07', '00')">07:00</button>
      <button type="button" class="preset-btn" @click="setTimePreset('08', '30')">08:30</button>
      <button type="button" class="preset-btn" @click="setTimePreset('12', '00')">12:00</button>
      <button type="button" class="preset-btn" @click="setTimePreset('18', '00')">18:00</button>
      <button type="button" class="preset-btn" @click="setTimePreset('22', '30')">22:30</button>
    </div>

    <!-- Manual Time Input -->
    <div class="manual-time-input-wrap">
      <label class="field-label">输入响铃时间 (时:分)</label>
      <div class="input-with-icon">
        <Clock :size="16" class="input-icon" />
        <input
          type="time"
          v-model="internalTime"
          class="manual-input"
        />
      </div>
    </div>

    <!-- Display Badge -->
    <div class="time-display-badge">
      <span class="badge-label">设定响铃时间：</span>
      <span class="badge-value">{{ internalTime || '08:00' }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import { Clock } from 'lucide-vue-next'

const props = defineProps<{
  modelValue?: string
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: string): void
}>()

const internalTime = ref('08:00')

function parseModelValue(val?: string) {
  if (!val) {
    internalTime.value = '08:00'
    return
  }
  const parts = val.split(':')
  if (parts.length >= 2) {
    const h = String(parseInt(parts[0], 10) || 0).padStart(2, '0')
    const m = String(parseInt(parts[1], 10) || 0).padStart(2, '0')
    internalTime.value = `${h}:${m}`
  } else {
    internalTime.value = val
  }
}

watch(internalTime, (newVal) => {
  emit('update:modelValue', newVal)
})

watch(
  () => props.modelValue,
  (newVal) => {
    if (newVal && newVal !== internalTime.value) {
      parseModelValue(newVal)
    }
  },
  { immediate: true }
)

onMounted(() => {
  parseModelValue(props.modelValue)
})

function setTimePreset(hStr: string, mStr: string) {
  internalTime.value = `${hStr}:${mStr}`
}
</script>

<style scoped>
.manual-time-picker {
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

.manual-time-input-wrap {
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
  font-size: 15px;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-weight: 700;
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

.time-display-badge {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  background-color: var(--bg-surface, #f8fafc);
  border: 1px solid var(--border-color, #e2e8f0);
  border-radius: 8px;
  font-size: 12px;
}

.badge-label {
  color: var(--text-muted, #64748b);
}

.badge-value {
  font-size: 16px;
  font-weight: 800;
  color: var(--primary, #3b82f6);
  font-family: ui-monospace, SFMono-Regular, monospace;
}
</style>

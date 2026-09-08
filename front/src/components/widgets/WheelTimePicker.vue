<template>
  <div class="manual-time-picker">
    <!-- Quick Time Preset Chips -->
    <div class="quick-presets">
      <span class="preset-label"><Clock :size="12" /> 常用时刻:</span>
      <button type="button" class="preset-btn" @click="setTimePreset(7, 0)">07:00</button>
      <button type="button" class="preset-btn" @click="setTimePreset(8, 30)">08:30</button>
      <button type="button" class="preset-btn" @click="setTimePreset(12, 0)">12:00</button>
      <button type="button" class="preset-btn" @click="setTimePreset(18, 0)">18:00</button>
      <button type="button" class="preset-btn" @click="setTimePreset(22, 30)">22:30</button>
    </div>

    <!-- VueDatePicker Time Picker -->
    <div class="time-picker-wrapper">
      <label class="field-label">输入或选择响铃时刻</label>
      <VueDatePicker
        v-model="timeObj"
        time-picker
        :is-24="true"
        :locale="zhCN"
        select-text="确定"
        cancel-text="取消"
        now-button-label="当前时刻"
        :show-now-button="true"
        auto-apply
        placeholder="选择响铃时间 (时:分)"
        class="custom-time-picker"
      />
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
import { VueDatePicker } from '@vuepic/vue-datepicker'
import '@vuepic/vue-datepicker/dist/main.css'
import { zhCN } from 'date-fns/locale'

const props = defineProps<{
  modelValue?: string
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: string): void
}>()

const timeObj = ref<{ hours: number; minutes: number; seconds?: number }>({
  hours: 8,
  minutes: 0
})

const formattedDisplay = computed(() => {
  const h = String(timeObj.value.hours || 0).padStart(2, '0')
  const m = String(timeObj.value.minutes || 0).padStart(2, '0')
  return `${h}:${m}`
})

watch(formattedDisplay, (newVal) => {
  emit('update:modelValue', newVal)
})

function parseModelValue(val?: string) {
  if (!val) {
    timeObj.value = { hours: 8, minutes: 0 }
    return
  }
  const parts = val.split(':')
  if (parts.length >= 2) {
    const h = parseInt(parts[0], 10) || 0
    const m = parseInt(parts[1], 10) || 0
    timeObj.value = { hours: h, minutes: m }
  }
}

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

function setTimePreset(hours: number, minutes: number) {
  timeObj.value = { hours, minutes }
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

.time-picker-wrapper {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.field-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-muted, #64748b);
}

.custom-time-picker {
  --dp-font-family: inherit;
  --dp-border-radius: 10px;
  --dp-primary-color: var(--primary, #3b82f6);
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

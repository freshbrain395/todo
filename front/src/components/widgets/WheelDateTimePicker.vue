<template>
  <div class="reminder-multi-row-config">
    <!-- Header Information -->
    <div class="config-header">
      <span class="config-title">
        <Clock :size="15" class="icon-primary" />
        待办提醒时间与重复规则
      </span>
      <span class="config-subtitle">请在下方三行中选择一种重复模式进行配置</span>
    </div>

    <div class="repeat-rows-container">
      <!-- ROW 1: 每小时重复 -->
      <div
        class="repeat-row-card"
        :class="{ active: currentMode === 'hourly' }"
        @click="currentMode = 'hourly'"
      >
        <div class="row-header">
          <div class="radio-indicator">
            <span class="dot" v-if="currentMode === 'hourly'"></span>
          </div>
          <span class="row-title">1. 每小时重复</span>
          <span class="row-badge">每小时触发</span>
        </div>

        <div class="row-body" @click.stop>
          <div class="control-line">
            <span class="label">具体分钟：</span>
            <div class="minute-presets">
              <button
                v-for="m in [0, 15, 30, 45]"
                :key="'min-' + m"
                type="button"
                class="pill-btn"
                :class="{ selected: currentMode === 'hourly' && hourlyMinute === m }"
                @click="setHourlyMinute(m)"
              >
                {{ String(m).padStart(2, '0') }}分 {{ m === 0 ? '(整点)' : m === 30 ? '(半点)' : '' }}
              </button>
            </div>
            <div class="custom-minute-input">
              <input
                type="number"
                min="0"
                max="59"
                v-model.number="hourlyMinute"
                class="num-input"
                placeholder="0-59"
                @focus="currentMode = 'hourly'"
              />
              <span class="unit">分</span>
            </div>
          </div>
        </div>
      </div>

      <!-- ROW 2: 每周重复 -->
      <div
        class="repeat-row-card"
        :class="{ active: currentMode === 'weekly' }"
        @click="currentMode = 'weekly'"
      >
        <div class="row-header">
          <div class="radio-indicator">
            <span class="dot" v-if="currentMode === 'weekly'"></span>
          </div>
          <span class="row-title">2. 每周重复</span>
          <span class="row-badge">每周固定日触发</span>
        </div>

        <div class="row-body" @click.stop>
          <div class="control-line weekday-line">
            <span class="label">选择星期：</span>
            <div class="weekday-chips">
              <button
                v-for="(wName, wIdx) in weekdays"
                :key="'wk-' + wIdx"
                type="button"
                class="weekday-chip"
                :class="{ selected: currentMode === 'weekly' && selectedWeekdays.includes(wIdx) }"
                @click="toggleWeekday(wIdx)"
              >
                {{ wName }}
              </button>
            </div>
            <div class="quick-preset-sub">
              <button type="button" class="text-link-btn" @click="setWorkdays">工作日</button>
              <button type="button" class="text-link-btn" @click="setWeekends">周末</button>
              <button type="button" class="text-link-btn" @click="setEveryday">每天</button>
            </div>
          </div>

          <div class="control-line time-line">
            <span class="label">提醒时刻：</span>
            <input
              type="time"
              v-model="weeklyTime"
              class="time-input"
              @focus="currentMode = 'weekly'"
            />
          </div>
        </div>
      </div>

      <!-- ROW 3: 每月重复 -->
      <div
        class="repeat-row-card"
        :class="{ active: currentMode === 'monthly' }"
        @click="currentMode = 'monthly'"
      >
        <div class="row-header">
          <div class="radio-indicator">
            <span class="dot" v-if="currentMode === 'monthly'"></span>
          </div>
          <span class="row-title">3. 每月重复</span>
          <span class="row-badge">每月固定日触发</span>
        </div>

        <div class="row-body" @click.stop>
          <div class="control-line monthday-line">
            <span class="label">选择每月哪一天：</span>
            <div class="monthday-quick">
              <button
                v-for="d in [1, 15, 28]"
                :key="'mday-' + d"
                type="button"
                class="pill-btn"
                :class="{ selected: currentMode === 'monthly' && monthlyDay === d }"
                @click="setMonthlyDay(d)"
              >
                每月 {{ d }}日 {{ d === 1 ? '(月初)' : d === 15 ? '(月中)' : '(月末)' }}
              </button>
            </div>
            <div class="custom-day-select">
              <select v-model.number="monthlyDay" class="day-select" @focus="currentMode = 'monthly'">
                <option v-for="n in 31" :key="'opt-d-' + n" :value="n">
                  每月 {{ n }} 日
                </option>
              </select>
            </div>
          </div>

          <div class="control-line time-line">
            <span class="label">提醒时刻：</span>
            <input
              type="time"
              v-model="monthlyTime"
              class="time-input"
              @focus="currentMode = 'monthly'"
            />
          </div>
        </div>
      </div>
    </div>

    <!-- Active Reminder Rule Preview Summary -->
    <div class="rule-preview-badge">
      <Sparkles :size="14" class="icon-sparkle" />
      <span class="preview-label">当前选定规则:</span>
      <strong class="preview-value">{{ generatedRuleSummary }}</strong>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { Clock, Sparkles } from 'lucide-vue-next'

const props = defineProps<{
  modelValue?: string
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: string): void
}>()

type RepeatMode = 'hourly' | 'weekly' | 'monthly'

const currentMode = ref<RepeatMode>('hourly')
const hourlyMinute = ref<number>(0)

const weekdays = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
const selectedWeekdays = ref<number[]>([0, 1, 2, 3, 4]) // Mon-Fri
const weeklyTime = ref<string>('09:00')

const monthlyDay = ref<number>(1)
const monthlyTime = ref<string>('10:00')

function setHourlyMinute(m: number) {
  currentMode.value = 'hourly'
  hourlyMinute.value = m
}

function toggleWeekday(wIdx: number) {
  currentMode.value = 'weekly'
  const pos = selectedWeekdays.value.indexOf(wIdx)
  if (pos >= 0) {
    if (selectedWeekdays.value.length > 1) {
      selectedWeekdays.value.splice(pos, 1)
    }
  } else {
    selectedWeekdays.value.push(wIdx)
    selectedWeekdays.value.sort((a, b) => a - b)
  }
}

function setWorkdays() {
  currentMode.value = 'weekly'
  selectedWeekdays.value = [0, 1, 2, 3, 4]
}

function setWeekends() {
  currentMode.value = 'weekly'
  selectedWeekdays.value = [5, 6]
}

function setEveryday() {
  currentMode.value = 'weekly'
  selectedWeekdays.value = [0, 1, 2, 3, 4, 5, 6]
}

function setMonthlyDay(d: number) {
  currentMode.value = 'monthly'
  monthlyDay.value = d
}

const generatedRuleSummary = computed(() => {
  if (currentMode.value === 'hourly') {
    const minStr = String(hourlyMinute.value || 0).padStart(2, '0')
    return `每小时 ${minStr}分 重复提醒`
  }
  if (currentMode.value === 'weekly') {
    if (selectedWeekdays.value.length === 0) return `每周 [未选日期] ${weeklyTime.value}`
    if (selectedWeekdays.value.length === 7) return `每天 ${weeklyTime.value} 重复提醒`
    if (selectedWeekdays.value.length === 5 && selectedWeekdays.value.every(d => d < 5)) {
      return `每个工作日 (周一至周五) ${weeklyTime.value} 重复提醒`
    }
    const daysStr = selectedWeekdays.value.map(i => weekdays[i]).join('、')
    return `每${daysStr} ${weeklyTime.value} 重复提醒`
  }
  if (currentMode.value === 'monthly') {
    return `每月 ${monthlyDay.value}日 ${monthlyTime.value} 重复提醒`
  }
  return ''
})

watch(generatedRuleSummary, (newVal) => {
  emit('update:modelValue', newVal)
})

function parseModelValue(val?: string) {
  if (!val) {
    currentMode.value = 'hourly'
    hourlyMinute.value = 0
    return
  }

  if (val.includes('每小时')) {
    currentMode.value = 'hourly'
    const match = val.match(/(\d+)\s*分/)
    if (match) hourlyMinute.value = parseInt(match[1], 10) || 0
    return
  }

  if (val.includes('每周') || val.includes('工作日') || val.includes('每天') || val.includes('周末')) {
    currentMode.value = 'weekly'
    if (val.includes('工作日')) {
      selectedWeekdays.value = [0, 1, 2, 3, 4]
    } else if (val.includes('周末')) {
      selectedWeekdays.value = [5, 6]
    } else if (val.includes('每天')) {
      selectedWeekdays.value = [0, 1, 2, 3, 4, 5, 6]
    } else {
      const days: number[] = []
      weekdays.forEach((w, idx) => {
        if (val.includes(w)) days.push(idx)
      })
      if (days.length > 0) selectedWeekdays.value = days
    }

    const timeMatch = val.match(/(\d{1,2}:\d{2})/)
    if (timeMatch) weeklyTime.value = timeMatch[1]
    return
  }

  if (val.includes('每月')) {
    currentMode.value = 'monthly'
    const dayMatch = val.match(/(\d{1,2})\s*日/)
    if (dayMatch) monthlyDay.value = parseInt(dayMatch[1], 10) || 1
    const timeMatch = val.match(/(\d{1,2}:\d{2})/)
    if (timeMatch) monthlyTime.value = timeMatch[1]
    return
  }

  // If passed an ISO datetime string, set reasonable defaults
  const d = new Date(val.replace(' ', 'T'))
  if (!isNaN(d.getTime())) {
    currentMode.value = 'weekly'
    const dayOfWeek = (d.getDay() + 6) % 7 // 0 = Mon
    selectedWeekdays.value = [dayOfWeek]
    weeklyTime.value = `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
  }
}

watch(
  () => props.modelValue,
  (newVal) => {
    if (newVal && newVal !== generatedRuleSummary.value) {
      parseModelValue(newVal)
    }
  },
  { immediate: true }
)

onMounted(() => {
  if (props.modelValue) {
    parseModelValue(props.modelValue)
  }
})
</script>

<style scoped>
.reminder-multi-row-config {
  display: flex;
  flex-direction: column;
  gap: 14px;
  background-color: var(--bg-surface, #ffffff);
  border: 1px solid var(--border-color, #e2e8f0);
  border-radius: 16px;
  padding: 18px;
  box-shadow: 0 4px 18px rgba(0, 0, 0, 0.04);
}

.config-header {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.config-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  font-weight: 700;
  color: var(--text-main, #0f172a);
}

.icon-primary {
  color: var(--primary, #3b82f6);
}

.config-subtitle {
  font-size: 11.5px;
  color: var(--text-muted, #64748b);
}

.repeat-rows-container {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.repeat-row-card {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 12px 14px;
  background-color: var(--bg-app, #f8fafc);
  border: 1.5px solid var(--border-color, #e2e8f0);
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.repeat-row-card:hover {
  border-color: var(--primary, #3b82f6);
  background-color: var(--bg-surface, #ffffff);
}

.repeat-row-card.active {
  border-color: var(--primary, #3b82f6);
  background-color: rgba(59, 130, 246, 0.03);
  box-shadow: 0 0 0 1px var(--primary, #3b82f6);
}

.row-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.radio-indicator {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  border: 2px solid var(--border-color, #cbd5e1);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
}

.repeat-row-card.active .radio-indicator {
  border-color: var(--primary, #3b82f6);
}

.radio-indicator .dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: var(--primary, #3b82f6);
}

.row-title {
  font-size: 13.5px;
  font-weight: 700;
  color: var(--text-main, #0f172a);
}

.row-badge {
  font-size: 10.5px;
  font-weight: 600;
  color: var(--primary, #3b82f6);
  background-color: rgba(59, 130, 246, 0.08);
  padding: 2px 7px;
  border-radius: 10px;
  margin-left: auto;
}

.row-body {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding-left: 24px;
}

.control-line {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.control-line .label {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-muted, #64748b);
  white-space: nowrap;
}

.minute-presets,
.monthday-quick {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}

.pill-btn {
  background-color: var(--bg-surface, #ffffff);
  border: 1px solid var(--border-color, #e2e8f0);
  border-radius: 16px;
  padding: 3px 10px;
  font-size: 11.5px;
  font-weight: 600;
  color: var(--text-main, #334155);
  cursor: pointer;
  transition: all 0.2s ease;
}

.pill-btn:hover {
  border-color: var(--primary, #3b82f6);
  color: var(--primary, #3b82f6);
}

.pill-btn.selected {
  background-color: var(--primary, #3b82f6);
  color: #ffffff;
  border-color: var(--primary, #3b82f6);
}

.custom-minute-input {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.num-input {
  width: 52px;
  padding: 3px 6px;
  border: 1px solid var(--border-color, #e2e8f0);
  border-radius: 8px;
  font-size: 12px;
  font-weight: 600;
  text-align: center;
  background-color: var(--bg-surface, #ffffff);
  color: var(--text-main, #0f172a);
}

.unit {
  font-size: 12px;
  color: var(--text-muted, #64748b);
}

.weekday-chips {
  display: flex;
  align-items: center;
  gap: 5px;
  flex-wrap: wrap;
}

.weekday-chip {
  background-color: var(--bg-surface, #ffffff);
  border: 1px solid var(--border-color, #e2e8f0);
  border-radius: 8px;
  padding: 4px 9px;
  font-size: 11.5px;
  font-weight: 600;
  color: var(--text-main, #334155);
  cursor: pointer;
  transition: all 0.2s ease;
}

.weekday-chip:hover {
  border-color: var(--primary, #3b82f6);
  color: var(--primary, #3b82f6);
}

.weekday-chip.selected {
  background-color: var(--primary, #3b82f6);
  color: #ffffff;
  border-color: var(--primary, #3b82f6);
}

.quick-preset-sub {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-left: 4px;
}

.text-link-btn {
  background: none;
  border: none;
  font-size: 11px;
  font-weight: 600;
  color: var(--primary, #3b82f6);
  cursor: pointer;
  padding: 2px 4px;
  border-radius: 4px;
}

.text-link-btn:hover {
  text-decoration: underline;
  background-color: rgba(59, 130, 246, 0.08);
}

.time-input {
  padding: 4px 10px;
  border: 1px solid var(--border-color, #e2e8f0);
  border-radius: 8px;
  font-size: 12.5px;
  font-weight: 700;
  font-family: ui-monospace, SFMono-Regular, monospace;
  background-color: var(--bg-surface, #ffffff);
  color: var(--text-main, #0f172a);
}

.day-select {
  padding: 4px 8px;
  border: 1px solid var(--border-color, #e2e8f0);
  border-radius: 8px;
  font-size: 12px;
  font-weight: 600;
  background-color: var(--bg-surface, #ffffff);
  color: var(--text-main, #0f172a);
}

.rule-preview-badge {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  background-color: var(--bg-app, #f8fafc);
  border: 1px dashed var(--primary, #3b82f6);
  border-radius: 10px;
  font-size: 12.5px;
}

.icon-sparkle {
  color: #f59e0b;
}

.preview-label {
  color: var(--text-muted, #64748b);
  font-weight: 600;
}

.preview-value {
  color: var(--primary, #3b82f6);
  font-weight: 800;
}
</style>

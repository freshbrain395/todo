<template>
  <div class="alarm-page-container animate-fade-in">
    <div class="pure-list-workspace">
      <!-- Top Toolbar (Filters, Search, Add Button) -->
      <div class="toolbar">
        <div class="filter-group">
          <button
            class="filter-btn"
            :class="{ active: alarmFilter === 'all' }"
            @click="alarmFilter = 'all'"
          >
            全部 ({{ alarmList.length }})
          </button>
          <button
            class="filter-btn"
            :class="{ active: alarmFilter === 'enabled' }"
            @click="alarmFilter = 'enabled'"
          >
            已启用 ({{ enabledAlarmCount }})
          </button>
          <button
            class="filter-btn"
            :class="{ active: alarmFilter === 'disabled' }"
            @click="alarmFilter = 'disabled'"
          >
            已关闭 ({{ disabledAlarmCount }})
          </button>
        </div>

        <div class="toolbar-right">
          <div class="search-box">
            <Search :size="14" class="search-icon" />
            <input
              type="text"
              v-model="alarmSearch"
              placeholder="搜索闹钟..."
            />
          </div>

          <button class="btn btn-primary" @click="openAddAlarmModal">
            <Plus :size="14" /> 新建闹钟
          </button>
        </div>
      </div>

      <!-- Alarm List Area -->
      <div class="list-scroll-area">
        <div v-if="filteredAlarmList.length === 0" class="empty-state">
          <div class="empty-icon"><Bell :size="42" :stroke-width="1.5" /></div>
          <p class="empty-text">暂无闹钟设置，点击右上角 "+ 新建闹钟" 添加吧！</p>
        </div>

        <div v-else class="items-grid">
          <div
            v-for="item in filteredAlarmList"
            :key="item.id"
            class="list-card-item animate-fade-in"
            :class="{ disabled: !item.enabled }"
          >
            <div class="card-left-indicator">
              <div class="mini-alarm-icon" :class="{ enabled: item.enabled }">
                <Bell :size="20" />
              </div>
            </div>

            <div class="card-body">
              <div class="card-title-row">
                <span class="card-title">{{ item.title || '闹钟提醒' }}</span>
                <span class="status-tag" :class="{ running: item.enabled, finished: !item.enabled }">
                  <span class="dot"></span>
                  {{ item.enabled ? '已启用' : '已关闭' }}
                </span>
                <span class="alarm-tag-repeat">
                  <Repeat :size="12" /> {{ formatRepeatText(item) }}
                </span>
                <span class="sound-tag clickable-sound-tag" @click.stop="previewSound(item.soundType)" title="点击试听提示音">
                  <Volume2 :size="11" />
                  {{ soundTypeShortLabel(item.soundType) }}
                </span>
                <span v-if="item.snoozeMinutes" class="snooze-tag">
                  <Coffee :size="11" /> 贪睡 {{ item.snoozeMinutes }} 分钟
                </span>
              </div>

              <div class="card-time-display">
                <span class="digits-time-huge">{{ item.time }}</span>
                <span v-if="item.repeat === 'holiday_compensate'" class="smart-tip">
                  · <Sparkles :size="12" /> 法定假期自动跳过 · 调休补班日自动响铃
                </span>
                <span v-else-if="item.repeat === 'compensate_only'" class="smart-tip">
                  · <Sparkles :size="12" /> 仅在周末补班日响铃
                </span>
                <span v-else class="finish-msg-tip">
                  · {{ item.enabled ? '已激活响铃提醒' : '已关闭' }}
                </span>
              </div>
            </div>

            <div class="card-actions">
              <!-- Switch Toggle -->
              <label class="switch-toggle" title="开启/关闭闹钟">
                <input
                  type="checkbox"
                  :checked="item.enabled"
                  @change="item.enabled = !item.enabled"
                />
                <span class="slider-round"></span>
              </label>

              <button
                class="icon-btn-action edit"
                @click="openEditAlarmModal(item)"
                title="编辑闹钟"
              >
                <Sliders :size="14" />
              </button>

              <button
                class="icon-btn-action delete"
                @click="removeAlarm(item.id)"
                title="删除闹钟"
              >
                <Trash2 :size="14" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Alarm Modal (Add / Edit) -->
    <div v-if="showAlarmModal" class="modal-backdrop" @click.self="showAlarmModal = false">
      <div class="modal-card animate-scale-up">
        <div class="modal-header">
          <h3><Bell :size="18" /> {{ editingAlarmId ? '编辑闹钟' : '新建闹钟' }}</h3>
          <button class="icon-btn-close" @click="showAlarmModal = false"><X :size="16" /></button>
        </div>

        <div class="modal-body">
          <div class="form-group">
            <label class="form-label">响铃时刻 (3D 轮盘调节) *</label>
            <WheelTimePicker v-model="alarmForm.time" />
          </div>

          <div class="form-group">
            <label class="form-label">闹钟标签 / 备注说明</label>
            <input
              type="text"
              v-model="alarmForm.title"
              class="text-input"
              placeholder="例如: 上班提醒 / 晨起早读 / 团队开会..."
            />
          </div>

          <div class="form-group">
            <label class="form-label">重复频率 / 智能调休模式</label>
            <select v-model="alarmForm.repeat" class="select-input">
              <option value="holiday_compensate">智能调休闹钟 (工作日响 / 假关 / 补班响)</option>
              <option value="compensate_only">仅调休补班日 (周六日补班时自动响)</option>
              <option value="workday">工作日 (周一至周五)</option>
              <option value="weekend">周末 (周六与周日)</option>
              <option value="everyday">每天响铃</option>
              <option value="once">单次响铃 (仅响一次)</option>
              <option value="custom">自定义星期</option>
            </select>
          </div>

          <div v-if="alarmForm.repeat === 'holiday_compensate' || alarmForm.repeat === 'compensate_only'" class="compensate-config-box">
            <label class="checkbox-option">
              <input type="checkbox" v-model="alarmForm.skipHolidays" />
              <span>自动跳过法定节假日 (假期当天不响铃)</span>
            </label>
            <label class="checkbox-option">
              <input type="checkbox" v-model="alarmForm.ringOnCompensate" />
              <span>周末调休补班智能响铃 (补班日自动激活)</span>
            </label>
            <div class="compensate-tips">
              <Sparkles :size="13" /> 已接入法定节假日与调休补班日历，自动识别调休日，避免假期误响与补班漏响。
            </div>
          </div>

          <div v-if="alarmForm.repeat === 'custom'" class="form-group">
            <label class="form-label">选择重复星期:</label>
            <div class="weekdays-selector">
              <button
                v-for="day in [1, 2, 3, 4, 5, 6, 0]"
                :key="day"
                type="button"
                class="weekday-chip"
                :class="{ active: alarmForm.customDays.includes(day) }"
                @click="toggleCustomDay(day)"
              >
                {{ weekDayLabel(day) }}
              </button>
            </div>
          </div>

          <div class="form-group">
            <label class="form-label">贪睡时长 (稍后提醒)</label>
            <div class="snooze-config-row">
              <button
                type="button"
                class="btn-step"
                @click="alarmForm.snoozeMinutes = Math.max(1, alarmForm.snoozeMinutes - 1)"
              >-</button>
              <span class="snooze-val-text">{{ alarmForm.snoozeMinutes }} 分钟</span>
              <button
                type="button"
                class="btn-step"
                @click="alarmForm.snoozeMinutes = Math.min(30, alarmForm.snoozeMinutes + 1)"
              >+</button>
            </div>
          </div>

          <div class="form-group">
            <label class="form-label">提示音效</label>
            <div class="sound-select-row">
              <select v-model="alarmForm.soundType" class="select-input flex-1">
                <option value="chime">风铃清脆 (Chime)</option>
                <option value="marimba">马林巴琴 (Marimba)</option>
                <option value="cyber">赛博提示 (Cyber)</option>
                <option value="beep">电子蜂鸣 (Beep)</option>
                <option value="silent">静音 (无声音)</option>
              </select>
              <button
                type="button"
                class="btn btn-outline preview-btn"
                @click="previewSound(alarmForm.soundType)"
                title="试听当前提示音"
              >
                <Volume2 :size="14" /> 试听
              </button>
            </div>
          </div>
        </div>

        <div class="modal-footer">
          <button class="btn btn-outline" @click="showAlarmModal = false">取消</button>
          <button class="btn btn-primary" @click="saveAlarmModal">
            <Check :size="14" /> 保存闹钟
          </button>
        </div>
      </div>
    </div>

    <!-- Alarm Ringing Modal -->
    <div v-if="ringingAlarm" class="modal-backdrop alarm-ringing-backdrop">
      <div class="modal-card ringing-card animate-pulse">
        <div class="ringing-icon"><Bell :size="40" /></div>
        <h2 class="ringing-title">闹钟响铃提醒！</h2>
        <div class="ringing-time">{{ ringingAlarm.time }}</div>
        <p class="ringing-label" v-if="ringingAlarm.title">{{ ringingAlarm.title }}</p>
        <div class="ringing-actions">
          <button class="btn btn-snooze" @click="snoozeRingingAlarm">
            <Coffee :size="16" /> 稍后提醒 (贪睡 {{ ringingAlarm.snoozeMinutes || 5 }} 分钟)
          </button>
          <button class="btn btn-dismiss" @click="dismissRingingAlarm">
            <Check :size="16" /> 知道啦 (关闭闹钟)
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import {
  Bell, Trash2, Plus, Repeat, Check, Coffee, Sliders, Sparkles, Volume2, Search, X
} from 'lucide-vue-next'
import { soundPlayer, type SoundType } from '../../utils/audio'
import WheelTimePicker from '../widgets/WheelTimePicker.vue'
import { showConfirm } from '../../utils/confirmState'
import { getUserConfig } from '../../utils/configManager'
import type { Alarm, AlarmRepeat } from '../../types'

const props = defineProps<{
  soundVolume?: number
}>()

const defaultAlarms: Alarm[] = [
  {
    id: 'alarm-1',
    time: '08:30',
    title: '上班提醒与晨会准备',
    enabled: true,
    repeat: 'holiday_compensate',
    customDays: [1, 2, 3, 4, 5],
    skipHolidays: true,
    ringOnCompensate: true,
    soundType: 'chime',
    snoozeMinutes: 5
  },
  {
    id: 'alarm-2',
    time: '12:00',
    title: '午餐及休息时间',
    enabled: true,
    repeat: 'workday',
    customDays: [1, 2, 3, 4, 5],
    skipHolidays: false,
    ringOnCompensate: false,
    soundType: 'cyber',
    snoozeMinutes: 5
  }
]

// Migrate old storage format if found (where key had label instead of title, repeatType instead of repeat)
function loadInitialAlarms(): Alarm[] {
  const raw = localStorage.getItem('todo_pro_alarm_list')
  if (!raw) return defaultAlarms
  try {
    const list = JSON.parse(raw)
    if (Array.isArray(list)) {
      return list.map((item: any) => ({
        id: item.id || 'alarm_' + Date.now(),
        time: item.time || '08:00',
        title: item.title || item.label || '闹钟提醒',
        enabled: Boolean(item.enabled),
        repeat: (item.repeat || item.repeatType || 'holiday_compensate') as AlarmRepeat,
        customDays: Array.isArray(item.customDays) ? item.customDays : [1, 2, 3, 4, 5],
        skipHolidays: item.skipHolidays !== undefined ? item.skipHolidays : true,
        ringOnCompensate: item.ringOnCompensate !== undefined ? item.ringOnCompensate : true,
        soundType: item.soundType || 'chime',
        snoozeMinutes: item.snoozeMinutes || 5
      }))
    }
  } catch (e) {
    console.error('Failed to parse alarms:', e)
  }
  return defaultAlarms
}

const alarmList = ref<Alarm[]>(loadInitialAlarms())
const alarmFilter = ref<'all' | 'enabled' | 'disabled'>('all')
const alarmSearch = ref('')
const ringingAlarm = ref<Alarm | null>(null)

const showAlarmModal = ref(false)
const editingAlarmId = ref<string | null>(null)
const alarmForm = ref<{
  time: string
  title: string
  repeat: AlarmRepeat
  customDays: number[]
  skipHolidays: boolean
  ringOnCompensate: boolean
  soundType: string
  snoozeMinutes: number
}>({
  time: '08:30',
  title: '',
  repeat: 'holiday_compensate',
  customDays: [1, 2, 3, 4, 5],
  skipHolidays: true,
  ringOnCompensate: true,
  soundType: 'chime',
  snoozeMinutes: 5
})

watch(alarmList, (newVal) => {
  localStorage.setItem('todo_pro_alarm_list', JSON.stringify(newVal))
}, { deep: true })

const enabledAlarmCount = computed(() => alarmList.value.filter(i => i.enabled).length)
const disabledAlarmCount = computed(() => alarmList.value.filter(i => !i.enabled).length)

const filteredAlarmList = computed(() => {
  return alarmList.value.filter(item => {
    if (alarmFilter.value === 'enabled' && !item.enabled) return false
    if (alarmFilter.value === 'disabled' && item.enabled) return false
    if (alarmSearch.value.trim()) {
      const q = alarmSearch.value.trim().toLowerCase()
      const matchTitle = item.title.toLowerCase().includes(q)
      const matchTime = item.time.includes(q)
      if (!matchTitle && !matchTime) return false
    }
    return true
  })
})

function previewSound(soundType: string) {
  if (soundType && soundType !== 'silent') {
    const configVol = getUserConfig()?.soundVolume
    const vol = typeof props.soundVolume === 'number' ? props.soundVolume : (typeof configVol === 'number' ? configVol : 0.8)
    soundPlayer.play(soundType as SoundType, vol)
  }
}

function openAddAlarmModal() {
  editingAlarmId.value = null
  alarmForm.value = {
    time: '08:30',
    title: '',
    repeat: 'holiday_compensate',
    customDays: [1, 2, 3, 4, 5],
    skipHolidays: true,
    ringOnCompensate: true,
    soundType: 'chime',
    snoozeMinutes: 5
  }
  showAlarmModal.value = true
}

function openEditAlarmModal(item: Alarm) {
  editingAlarmId.value = item.id
  alarmForm.value = {
    time: item.time,
    title: item.title,
    repeat: item.repeat,
    customDays: [...item.customDays],
    skipHolidays: item.skipHolidays,
    ringOnCompensate: item.ringOnCompensate,
    soundType: item.soundType,
    snoozeMinutes: item.snoozeMinutes || 5
  }
  showAlarmModal.value = true
}

function toggleCustomDay(day: number) {
  const idx = alarmForm.value.customDays.indexOf(day)
  if (idx > -1) {
    alarmForm.value.customDays.splice(idx, 1)
  } else {
    alarmForm.value.customDays.push(day)
  }
}

function weekDayLabel(day: number): string {
  const map: Record<number, string> = { 1: '周一', 2: '周二', 3: '周三', 4: '周四', 5: '周五', 6: '周六', 0: '周日' }
  return map[day] || ''
}

function formatRepeatText(item: Alarm): string {
  switch (item.repeat) {
    case 'holiday_compensate': return '智能调休 (工作日响/补班响)'
    case 'compensate_only': return '仅调休补班日'
    case 'workday': return '工作日 (周一至周五)'
    case 'weekend': return '周末 (周六与周日)'
    case 'everyday': return '每天'
    case 'once': return '仅一次'
    case 'custom':
      if (item.customDays.length === 7) return '每天'
      if (item.customDays.length === 0) return '未指定'
      return item.customDays.map(d => weekDayLabel(d)).join('、')
    default: return '每天'
  }
}

function soundTypeShortLabel(st: string): string {
  const map: Record<string, string> = {
    chime: '风铃',
    marimba: '马林巴',
    cyber: '赛博',
    beep: '蜂鸣',
    silent: '静音'
  }
  return map[st] || '默认铃声'
}

function saveAlarmModal() {
  const title = alarmForm.value.title.trim() || '闹钟提醒'
  if (editingAlarmId.value) {
    const idx = alarmList.value.findIndex(a => a.id === editingAlarmId.value)
    if (idx !== -1) {
      alarmList.value[idx].time = alarmForm.value.time
      alarmList.value[idx].title = title
      alarmList.value[idx].repeat = alarmForm.value.repeat
      alarmList.value[idx].customDays = [...alarmForm.value.customDays]
      alarmList.value[idx].skipHolidays = alarmForm.value.skipHolidays
      alarmList.value[idx].ringOnCompensate = alarmForm.value.ringOnCompensate
      alarmList.value[idx].soundType = alarmForm.value.soundType
      alarmList.value[idx].snoozeMinutes = alarmForm.value.snoozeMinutes
    }
  } else {
    const newAlarm: Alarm = {
      id: 'alarm_' + Date.now(),
      time: alarmForm.value.time,
      title,
      enabled: true,
      repeat: alarmForm.value.repeat,
      customDays: [...alarmForm.value.customDays],
      skipHolidays: alarmForm.value.skipHolidays,
      ringOnCompensate: alarmForm.value.ringOnCompensate,
      soundType: alarmForm.value.soundType,
      snoozeMinutes: alarmForm.value.snoozeMinutes
    }
    alarmList.value.unshift(newAlarm)
  }
  showAlarmModal.value = false
}

async function removeAlarm(id: string) {
  const confirmed = await showConfirm({
    title: '删除闹钟',
    message: '确定要删除该闹钟吗？',
    confirmText: '确认删除',
    type: 'danger'
  })
  if (!confirmed) return
  alarmList.value = alarmList.value.filter(a => a.id !== id)
}

function dismissRingingAlarm() {
  ringingAlarm.value = null
}

function snoozeRingingAlarm() {
  if (ringingAlarm.value) {
    const snoozeMins = ringingAlarm.value.snoozeMinutes || 5
    const now = new Date()
    now.setMinutes(now.getMinutes() + snoozeMins)
    const snoozeTime = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`
    
    // Add temporary snooze alarm
    alarmList.value.unshift({
      id: 'snooze_' + Date.now(),
      time: snoozeTime,
      title: `${ringingAlarm.value.title} (稍后提醒)`,
      enabled: true,
      repeat: 'once',
      customDays: [],
      skipHolidays: false,
      ringOnCompensate: false,
      soundType: ringingAlarm.value.soundType,
      snoozeMinutes: snoozeMins
    })
  }
  ringingAlarm.value = null
}

// Check Alarms Routine
let alarmTickerId: any = null
function startAlarmTicker() {
  alarmTickerId = setInterval(() => {
    const now = new Date()
    if (now.getSeconds() === 0) {
      const currentHM = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`
      alarmList.value.forEach(alarm => {
        if (alarm.enabled && alarm.time === currentHM) {
          ringingAlarm.value = alarm
          if (alarm.soundType !== 'silent') {
            soundPlayer.play(alarm.soundType as SoundType, props.soundVolume ?? 0.8)
          }
          if (alarm.repeat === 'once') {
            alarm.enabled = false
          }
        }
      })
    }
  }, 1000)
}

onMounted(() => {
  startAlarmTicker()
})

onUnmounted(() => {
  if (alarmTickerId) clearInterval(alarmTickerId)
})
</script>

<style scoped>
.alarm-page-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: 20px 24px;
  box-sizing: border-box;
  overflow-y: auto;
}

.pure-list-workspace {
  display: flex;
  flex-direction: column;
  height: 100%;
  width: 100%;
  max-width: 960px;
  margin: 0 auto;
  gap: 16px;
}

.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}

.filter-group {
  display: flex;
  align-items: center;
  gap: 6px;
}

.filter-btn {
  font-size: 12.5px;
  padding: 6px 14px;
  border-radius: 8px;
  border: 1px solid var(--border-color, #e2e8f0);
  background-color: var(--bg-surface, #ffffff);
  color: var(--text-main, #0f172a);
  cursor: pointer;
  font-weight: 500;
  transition: all 0.2s ease;
}

.filter-btn:hover {
  border-color: var(--primary, #3b82f6);
  color: var(--primary, #3b82f6);
}

.filter-btn.active {
  background-color: var(--primary, #3b82f6);
  color: #ffffff;
  border-color: var(--primary, #3b82f6);
  font-weight: 600;
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.25);
}

.toolbar-right {
  display: flex;
  align-items: center;
  gap: 10px;
}

.search-box {
  position: relative;
  display: flex;
  align-items: center;
}

.search-icon {
  position: absolute;
  left: 10px;
  color: var(--text-muted, #94a3b8);
}

.search-box input {
  padding: 6px 12px 6px 32px;
  border-radius: 8px;
  border: 1px solid var(--border-color, #e2e8f0);
  background: var(--bg-surface, #ffffff);
  color: var(--text-main, #0f172a);
  font-size: 12.5px;
  outline: none;
  width: 180px;
  transition: all 0.2s ease;
}

.search-box input:focus {
  border-color: var(--primary, #3b82f6);
  width: 210px;
}

.list-scroll-area {
  flex: 1;
  overflow-y: auto;
  padding-right: 4px;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 320px;
  color: var(--text-muted, #94a3b8);
  gap: 12px;
}

.items-grid {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.list-card-item {
  position: relative;
  display: flex;
  align-items: center;
  padding: 14px 18px;
  background-color: var(--bg-card, #ffffff);
  border: 1px solid var(--border-color, #e2e8f0);
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.03);
  gap: 16px;
  transition: all 0.2s ease;
}

.list-card-item:hover {
  border-color: var(--primary, #3b82f6);
  box-shadow: 0 6px 16px rgba(59, 130, 246, 0.08);
  transform: translateY(-1px);
}

.list-card-item.disabled {
  opacity: 0.65;
}

.card-left-indicator {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.mini-alarm-icon {
  width: 42px;
  height: 42px;
  border-radius: 12px;
  background: var(--bg-surface, #f8fafc);
  border: 1px solid var(--border-color, #e2e8f0);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-muted, #64748b);
  transition: all 0.2s ease;
}

.mini-alarm-icon.enabled {
  background: rgba(59, 130, 246, 0.1);
  color: var(--primary, #3b82f6);
  border-color: rgba(59, 130, 246, 0.3);
}

.card-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 0;
}

.card-title-row {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.card-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-main, #0f172a);
}

.status-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 10px;
  background: var(--bg-app, #f1f5f9);
  color: var(--text-muted, #64748b);
}

.status-tag .dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background-color: currentColor;
}

.status-tag.running {
  background: rgba(16, 185, 129, 0.12);
  color: #10b981;
}

.status-tag.finished {
  background: var(--bg-app, #f1f5f9);
  color: var(--text-muted, #94a3b8);
}

.sound-tag,
.snooze-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 6px;
  background: var(--bg-surface, #f8fafc);
  border: 1px solid var(--border-color, #e2e8f0);
  color: var(--text-muted, #64748b);
}

.clickable-sound-tag {
  cursor: pointer;
  transition: all 0.15s ease;
}

.clickable-sound-tag:hover {
  background: rgba(59, 130, 246, 0.12);
  border-color: var(--primary, #3b82f6);
  color: var(--primary, #3b82f6);
  transform: translateY(-1px);
}

.alarm-tag-repeat {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 6px;
  color: var(--primary, #3b82f6);
  background: rgba(59, 130, 246, 0.08);
  border: 1px solid rgba(59, 130, 246, 0.2);
}

.card-time-display {
  display: flex;
  align-items: baseline;
  gap: 10px;
  font-size: 13px;
}

.digits-time-huge {
  font-size: 26px;
  font-weight: 800;
  font-family: ui-monospace, SFMono-Regular, monospace;
  font-variant-numeric: tabular-nums;
  color: var(--text-main, #0f172a);
  letter-spacing: -0.5px;
}

.finish-msg-tip {
  font-size: 12px;
  color: var(--text-muted, #64748b);
}

.smart-tip {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  color: #8b5cf6;
  font-weight: 500;
  font-size: 12px;
}

.card-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

/* Switch Toggle */
.switch-toggle {
  position: relative;
  display: inline-block;
  width: 44px;
  height: 24px;
}

.switch-toggle input {
  opacity: 0;
  width: 0;
  height: 0;
}

.slider-round {
  position: absolute;
  cursor: pointer;
  top: 0; left: 0; right: 0; bottom: 0;
  background-color: var(--border-color, #cbd5e1);
  transition: .3s;
  border-radius: 24px;
}

.slider-round:before {
  position: absolute;
  content: "";
  height: 18px;
  width: 18px;
  left: 3px;
  bottom: 3px;
  background-color: white;
  transition: .3s;
  border-radius: 50%;
  box-shadow: 0 2px 4px rgba(0,0,0,0.2);
}

input:checked + .slider-round {
  background-color: #10b981;
}

input:checked + .slider-round:before {
  transform: translateX(20px);
}

.icon-btn-action {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 34px;
  height: 34px;
  border-radius: 8px;
  border: 1px solid var(--border-color, #e2e8f0);
  background: var(--bg-surface, #ffffff);
  color: var(--text-muted, #64748b);
  cursor: pointer;
  transition: all 0.2s ease;
}

.icon-btn-action:hover {
  border-color: var(--primary, #3b82f6);
  color: var(--primary, #3b82f6);
  background: var(--bg-hover, #f8fafc);
}

.icon-btn-action.delete:hover {
  border-color: #ef4444;
  color: #ef4444;
  background: rgba(239, 68, 68, 0.08);
}

/* Modal */
.modal-backdrop {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(15, 23, 42, 0.6);
  backdrop-filter: blur(6px);
  z-index: 10000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
}

.modal-card {
  width: 100%;
  max-width: 500px;
  background: var(--bg-card, #ffffff);
  border: 1px solid var(--border-color, #e2e8f0);
  border-radius: 20px;
  box-shadow: 0 24px 48px -12px rgba(0, 0, 0, 0.18);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 18px 22px;
  border-bottom: 1px solid var(--border-color, #e2e8f0);
}

.modal-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 700;
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--text-main, #0f172a);
}

.icon-btn-close {
  background: transparent;
  border: none;
  color: var(--text-muted, #64748b);
  cursor: pointer;
  padding: 4px;
  border-radius: 6px;
}

.modal-body {
  padding: 20px 22px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  max-height: 70vh;
  overflow-y: auto;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-label {
  font-size: 12.5px;
  font-weight: 600;
  color: var(--text-main, #1e293b);
}

.text-input,
.select-input {
  width: 100%;
  padding: 9px 12px;
  border-radius: 8px;
  border: 1px solid var(--border-color, #e2e8f0);
  background: var(--bg-surface, #ffffff);
  color: var(--text-main, #0f172a);
  font-size: 13px;
  box-sizing: border-box;
  outline: none;
}

.text-input:focus,
.select-input:focus {
  border-color: var(--primary, #3b82f6);
}

.compensate-config-box {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 12px;
  background: var(--bg-surface, #f8fafc);
  border: 1px dashed var(--border-color, #e2e8f0);
  border-radius: 10px;
}

.checkbox-option {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12.5px;
  color: var(--text-main, #0f172a);
  cursor: pointer;
}

.compensate-tips {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11.5px;
  color: var(--text-muted, #64748b);
}

.weekdays-selector {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.weekday-chip {
  padding: 6px 12px;
  border-radius: 8px;
  border: 1px solid var(--border-color, #e2e8f0);
  background: var(--bg-surface, #f8fafc);
  color: var(--text-main, #0f172a);
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.weekday-chip.active {
  background: var(--primary, #3b82f6);
  color: #ffffff;
  border-color: var(--primary, #3b82f6);
}

.snooze-config-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.btn-step {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  border: 1px solid var(--border-color, #e2e8f0);
  background: var(--bg-surface, #f8fafc);
  color: var(--text-main, #0f172a);
  font-size: 16px;
  font-weight: 700;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
}

.btn-step:hover {
  border-color: var(--primary, #3b82f6);
  color: var(--primary, #3b82f6);
}

.snooze-val-text {
  font-size: 13.5px;
  font-weight: 600;
  color: var(--text-main, #0f172a);
}

.sound-select-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.preview-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 9px 12px;
  white-space: nowrap;
}

.modal-footer {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 10px;
  padding: 14px 22px;
  border-top: 1px solid var(--border-color, #e2e8f0);
}

.ringing-card {
  text-align: center;
  padding: 32px 24px;
  align-items: center;
}

.ringing-icon {
  width: 72px;
  height: 72px;
  border-radius: 50%;
  background: rgba(239, 68, 68, 0.12);
  color: #ef4444;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 12px;
}

.ringing-title {
  font-size: 20px;
  font-weight: 800;
  color: #ef4444;
  margin: 0;
}

.ringing-time {
  font-size: 28px;
  font-weight: 800;
  color: var(--text-main, #0f172a);
  margin: 8px 0;
  font-family: ui-monospace, SFMono-Regular, monospace;
}

.ringing-label {
  font-size: 14px;
  color: var(--text-muted, #64748b);
  margin: 0 0 20px 0;
}

.ringing-actions {
  display: flex;
  gap: 12px;
}

.btn-dismiss {
  background: #10b981;
  color: #ffffff;
  padding: 10px 20px;
  border-radius: 10px;
  border: none;
  font-weight: 700;
  cursor: pointer;
}

.btn-snooze {
  background: var(--bg-surface, #f8fafc);
  border: 1px solid var(--border-color, #e2e8f0);
  color: var(--text-main, #0f172a);
  padding: 10px 18px;
  border-radius: 10px;
  font-weight: 600;
  cursor: pointer;
}

@keyframes pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.5; transform: scale(0.85); }
}

@media (max-width: 640px) {
  .toolbar {
    flex-direction: column;
    align-items: stretch;
  }
  .toolbar-right {
    justify-content: space-between;
  }
  .search-box {
    flex: 1;
  }
  .search-box input {
    width: 100%;
  }
  .list-card-item {
    flex-direction: column;
    align-items: stretch;
  }
  .card-actions {
    justify-content: flex-end;
  }
}
</style>

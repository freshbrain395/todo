<template>
  <div class="alarm-container animate-fade-in">
    <!-- View 1: Countdown Mode List View -->
    <div v-if="tab === 'countdown'" class="pure-list-workspace">
      <!-- Top Toolbar (Filters, Search, Add Button) -->
      <div class="toolbar">
        <div class="filter-group">
          <button
            class="filter-btn"
            :class="{ active: countdownFilter === 'all' }"
            @click="countdownFilter = 'all'"
          >
            全部 ({{ countdownList.length }})
          </button>
          <button
            class="filter-btn"
            :class="{ active: countdownFilter === 'running' }"
            @click="countdownFilter = 'running'"
          >
            计时中 ({{ runningCountdownCount }})
          </button>
          <button
            class="filter-btn"
            :class="{ active: countdownFilter === 'completed' }"
            @click="countdownFilter = 'completed'"
          >
            已完成 ({{ completedCountdownCount }})
          </button>
        </div>

        <div class="toolbar-right">
          <div class="search-box">
            <Search :size="14" class="search-icon" />
            <input
              type="text"
              v-model="countdownSearch"
              placeholder="搜索倒计时..."
            />
          </div>

          <button class="btn btn-primary" @click="openAddCountdownModal">
            <Plus :size="14" /> 新建倒计时
          </button>
        </div>
      </div>

      <!-- Countdown List Area -->
      <div class="list-scroll-area">
        <div v-if="filteredCountdownList.length === 0" class="empty-state">
          <div class="empty-icon"><Hourglass :size="42" :stroke-width="1.5" /></div>
          <p class="empty-text">暂无倒计时项目，点击右上角 "+ 新建倒计时" 添加吧！</p>
        </div>

        <div v-else class="items-grid">
          <div
            v-for="item in filteredCountdownList"
            :key="item.id"
            class="list-card-item animate-fade-in"
            :class="{ running: item.isRunning, completed: item.remainingSeconds === 0 }"
          >
            <div class="card-left-indicator">
              <div class="mini-timer-circle" :class="{ running: item.isRunning, done: item.remainingSeconds === 0 }">
                <Hourglass :size="18" />
              </div>
            </div>

            <div class="card-body">
              <div class="card-title-row">
                <span class="card-title">{{ item.title }}</span>
                <span class="status-tag" :class="{ running: item.isRunning, finished: item.remainingSeconds === 0 }">
                  <span class="dot"></span>
                  {{ item.isRunning ? '计时中' : item.remainingSeconds === 0 ? '已完成' : '就绪' }}
                </span>
                <span class="sound-tag">{{ soundTypeShortLabel(item.soundType) }}</span>
              </div>

              <div class="card-time-display">
                <span class="digits-time">{{ formatDurationText(item.remainingSeconds) }}</span>
                <span class="digits-total">/ 初始 {{ formatDurationText(item.initialSeconds) }}</span>
                <span v-if="item.finishMessage" class="finish-msg-tip">· {{ item.finishMessage }}</span>
              </div>

              <!-- Progress Track -->
              <div class="item-progress-track">
                <div
                  class="item-progress-bar"
                  :class="{ running: item.isRunning, done: item.remainingSeconds === 0 }"
                  :style="{ width: `${((item.initialSeconds - item.remainingSeconds) / (item.initialSeconds || 1)) * 100}%` }"
                ></div>
              </div>
            </div>

            <div class="card-actions">
              <button
                class="btn-action-primary"
                :class="{ running: item.isRunning }"
                @click="toggleCountdownItem(item)"
                :title="item.isRunning ? '暂停计时' : '开始计时'"
              >
                <Pause v-if="item.isRunning" :size="14" />
                <Play v-else :size="14" />
                <span>{{ item.isRunning ? '暂停' : '开始' }}</span>
              </button>

              <button
                class="icon-btn-action reset"
                @click="resetCountdownItem(item)"
                title="重置倒计时"
              >
                <RotateCcw :size="14" />
              </button>

              <button
                class="icon-btn-action edit"
                @click="openEditCountdownModal(item)"
                title="编辑倒计时"
              >
                <Sliders :size="14" />
              </button>

              <button
                class="icon-btn-action delete"
                @click="removeCountdownItem(item.id)"
                title="删除倒计时"
              >
                <Trash2 :size="14" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- View 2: Alarm Mode List View -->
    <div v-else class="pure-list-workspace">
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
                <span class="card-title">{{ item.label || '闹钟提醒' }}</span>
                <span class="status-tag" :class="{ running: item.enabled, finished: !item.enabled }">
                  <span class="dot"></span>
                  {{ item.enabled ? '已启用' : '已关闭' }}
                </span>
                <span class="alarm-tag-repeat">
                  <Repeat :size="12" /> {{ formatRepeatText(item) }}
                </span>
                <span class="sound-tag">{{ soundTypeShortLabel(item.soundType) }}</span>
              </div>

              <div class="card-time-display">
                <span class="digits-time">{{ item.time }}</span>
                <span v-if="item.repeatType === 'holiday_compensate'" class="smart-tip">
                  · <Sparkles :size="12" /> 法定假期自动跳过 · 调休补班日自动响铃
                </span>
                <span v-else-if="item.repeatType === 'compensate_only'" class="smart-tip">
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

    <!-- Countdown Modal (Add / Edit) -->
    <div v-if="showCountdownModal" class="modal-backdrop" @click.self="showCountdownModal = false">
      <div class="modal-card animate-scale-up">
        <div class="modal-header">
          <h3><Hourglass :size="18" /> {{ editingCountdownId ? '编辑倒计时' : '新建倒计时' }}</h3>
          <button class="icon-btn-close" @click="showCountdownModal = false"><X :size="16" /></button>
        </div>

        <div class="modal-body">
          <div class="form-group">
            <label class="form-label">倒计时名称 *</label>
            <input
              type="text"
              v-model="countdownForm.title"
              class="text-input"
              placeholder="例如: 番茄专注 / 煮面计时 / 敷面膜"
            />
          </div>

          <div class="form-group">
            <div class="label-with-presets">
              <label class="form-label">预设快捷时长</label>
              <div class="quick-preset-chips">
                <button type="button" class="preset-chip" @click="setModalMinutes(1)">1分</button>
                <button type="button" class="preset-chip" @click="setModalMinutes(3)">3分</button>
                <button type="button" class="preset-chip" @click="setModalMinutes(5)">5分</button>
                <button type="button" class="preset-chip" @click="setModalMinutes(10)">10分</button>
                <button type="button" class="preset-chip" @click="setModalMinutes(15)">15分</button>
                <button type="button" class="preset-chip" @click="setModalMinutes(25)">25分</button>
                <button type="button" class="preset-chip" @click="setModalMinutes(30)">30分</button>
                <button type="button" class="preset-chip" @click="setModalMinutes(60)">60分</button>
              </div>
            </div>

            <div class="time-inputs-row">
              <div class="time-unit-box">
                <input type="number" min="0" max="99" v-model.number="countdownForm.hours" class="unit-input" />
                <span class="unit-label">小时</span>
              </div>
              <span class="unit-colon">:</span>
              <div class="time-unit-box">
                <input type="number" min="0" max="59" v-model.number="countdownForm.minutes" class="unit-input" />
                <span class="unit-label">分钟</span>
              </div>
              <span class="unit-colon">:</span>
              <div class="time-unit-box">
                <input type="number" min="0" max="59" v-model.number="countdownForm.seconds" class="unit-input" />
                <span class="unit-label">秒</span>
              </div>
            </div>
          </div>

          <div class="form-group">
            <label class="form-label">提示音效</label>
            <div class="sound-select-row">
              <select v-model="countdownForm.soundType" class="select-input flex-1">
                <option value="chime">风铃清脆 (Chime)</option>
                <option value="marimba">马林巴琴 (Marimba)</option>
                <option value="cyber">赛博提示 (Cyber)</option>
                <option value="beep">电子蜂鸣 (Beep)</option>
                <option value="silent">静音 (无声音)</option>
              </select>
              <button
                type="button"
                class="btn btn-outline preview-btn"
                @click="previewSound(countdownForm.soundType)"
                title="试听当前提示音"
              >
                <Volume2 :size="14" /> 试听
              </button>
            </div>
          </div>

          <div class="form-group">
            <label class="form-label">结束提醒提示词 / 消息说明</label>
            <input
              type="text"
              v-model="countdownForm.finishMessage"
              class="text-input"
              placeholder="例如: 8分钟到了，温泉蛋煮好啦！"
            />
          </div>
        </div>

        <div class="modal-footer">
          <button class="btn btn-outline" @click="showCountdownModal = false">取消</button>
          <button class="btn btn-primary" @click="saveCountdownModal">
            <Check :size="14" /> 保存倒计时
          </button>
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
              v-model="alarmForm.label"
              class="text-input"
              placeholder="例如: 晨起早读 / 团队开会 / 喝水提醒..."
            />
          </div>

          <div class="form-group">
            <label class="form-label">重复频率 / 智能调休模式</label>
            <select v-model="alarmForm.repeatType" class="select-input">
              <option value="holiday_compensate">智能调休闹钟 (工作日响 / 假关 / 补班响)</option>
              <option value="compensate_only">仅调休补班日 (周六日补班时自动响)</option>
              <option value="workday">工作日 (周一至周五)</option>
              <option value="weekend">周末 (周六与周日)</option>
              <option value="everyday">每天响铃</option>
              <option value="once">单次响铃 (仅响一次)</option>
              <option value="custom">自定义星期</option>
            </select>
          </div>

          <div v-if="alarmForm.repeatType === 'holiday_compensate' || alarmForm.repeatType === 'compensate_only'" class="compensate-config-box">
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

          <div v-if="alarmForm.repeatType === 'custom'" class="form-group">
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
            <Check :size="14" /> 保存闹钟配置
          </button>
        </div>
      </div>
    </div>

    <!-- Countdown Ringing Modal -->
    <div v-if="ringingCountdown" class="modal-backdrop alarm-ringing-backdrop">
      <div class="modal-card ringing-card animate-pulse">
        <div class="ringing-icon"><Hourglass :size="40" /></div>
        <h2 class="ringing-title">倒计时结束提醒！</h2>
        <div class="ringing-time">{{ ringingCountdown.title }}</div>
        <p class="ringing-label">{{ ringingCountdown.finishMessage || '倒计时时间到！' }}</p>
        <div class="ringing-actions">
          <button class="btn btn-dismiss" @click="dismissRingingCountdown">
            <Check :size="16" /> 知道啦 (关闭提醒)
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
        <p class="ringing-label" v-if="ringingAlarm.label">{{ ringingAlarm.label }}</p>
        <div class="ringing-actions">
          <button class="btn btn-snooze" @click="snoozeRingingAlarm">
            <Coffee :size="16" /> 稍后提醒 (贪睡 5 分钟)
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
import { ref, computed, onUnmounted, onMounted, watch } from 'vue'
import {
  Hourglass, Bell, Play, Pause, RotateCcw,
  Trash2, Plus, Repeat, Check, Coffee, Sliders, Sparkles, Volume2, Search, X
} from 'lucide-vue-next'
import { soundPlayer, type SoundType } from '../../utils/audio'
import WheelTimePicker from '../widgets/WheelTimePicker.vue'
import { showConfirm } from '../../utils/confirmState'

const props = defineProps<{
  soundType?: SoundType
  soundVolume?: number
  mode?: 'countdown' | 'alarm'
}>()

const tab = ref<'countdown' | 'alarm'>(props.mode || 'countdown')

watch(() => props.mode, (newMode) => {
  if (newMode) {
    tab.value = newMode
  }
}, { immediate: true })

function previewSound(soundType: SoundType | 'silent') {
  if (soundType !== 'silent') {
    soundPlayer.play(soundType, props.soundVolume ?? 0.8)
  }
}

// ----------------------------------------------------
// 1. Countdown Logic & State
// ----------------------------------------------------
export interface CountdownItem {
  id: string
  title: string
  initialSeconds: number
  remainingSeconds: number
  isRunning: boolean
  soundType: SoundType | 'silent'
  notifyType: 'sound_and_popup' | 'sound_only' | 'popup_only'
  finishMessage: string
}

const defaultCountdownItems: CountdownItem[] = [
  {
    id: 'cd-1',
    title: '番茄专注',
    initialSeconds: 25 * 60,
    remainingSeconds: 25 * 60,
    isRunning: false,
    soundType: 'chime',
    notifyType: 'sound_and_popup',
    finishMessage: '👏 25分钟番茄专注已完成，休息一下吧！'
  },
  {
    id: 'cd-2',
    title: '快速休息',
    initialSeconds: 5 * 60,
    remainingSeconds: 5 * 60,
    isRunning: false,
    soundType: 'marimba',
    notifyType: 'sound_and_popup',
    finishMessage: '☕ 5分钟休息结束，准备投入工作！'
  },
  {
    id: 'cd-3',
    title: '煮温泉蛋',
    initialSeconds: 8 * 60,
    remainingSeconds: 8 * 60,
    isRunning: false,
    soundType: 'beep',
    notifyType: 'sound_and_popup',
    finishMessage: '🥚 8分钟到了，温泉蛋煮好啦！'
  }
]

const countdownList = ref<CountdownItem[]>(
  JSON.parse(localStorage.getItem('todo_pro_countdown_list') || 'null') || defaultCountdownItems
)

const countdownFilter = ref<'all' | 'running' | 'completed'>('all')
const countdownSearch = ref('')
const ringingCountdown = ref<CountdownItem | null>(null)

const showCountdownModal = ref(false)
const editingCountdownId = ref<string | null>(null)
const countdownForm = ref<{
  title: string
  hours: number
  minutes: number
  seconds: number
  soundType: SoundType | 'silent'
  notifyType: 'sound_and_popup' | 'sound_only' | 'popup_only'
  finishMessage: string
}>({
  title: '',
  hours: 0,
  minutes: 10,
  seconds: 0,
  soundType: 'chime',
  notifyType: 'sound_and_popup',
  finishMessage: ''
})

watch(countdownList, (newVal) => {
  const serializable = newVal.map(item => ({
    id: item.id,
    title: item.title,
    initialSeconds: item.initialSeconds,
    remainingSeconds: item.remainingSeconds,
    isRunning: item.isRunning,
    soundType: item.soundType,
    notifyType: item.notifyType,
    finishMessage: item.finishMessage
  }))
  localStorage.setItem('todo_pro_countdown_list', JSON.stringify(serializable))
}, { deep: true })

const runningCountdownCount = computed(() => countdownList.value.filter(i => i.isRunning).length)
const completedCountdownCount = computed(() => countdownList.value.filter(i => i.remainingSeconds === 0).length)

const filteredCountdownList = computed(() => {
  return countdownList.value.filter(item => {
    if (countdownFilter.value === 'running' && !item.isRunning) return false
    if (countdownFilter.value === 'completed' && item.remainingSeconds !== 0) return false
    if (countdownSearch.value.trim()) {
      const q = countdownSearch.value.trim().toLowerCase()
      if (!item.title.toLowerCase().includes(q)) return false
    }
    return true
  })
})

let globalCdInterval: any = null

function updateGlobalCdInterval() {
  const hasRunning = countdownList.value.some(item => item.isRunning)
  if (hasRunning && !globalCdInterval) {
    globalCdInterval = setInterval(() => {
      let anyStillRunning = false
      countdownList.value.forEach(item => {
        if (item.isRunning) {
          if (item.remainingSeconds > 0) {
            item.remainingSeconds--
            anyStillRunning = true
          } else {
            item.isRunning = false
            onCountdownFinished(item)
          }
        }
      })
      if (!anyStillRunning && globalCdInterval) {
        clearInterval(globalCdInterval)
        globalCdInterval = null
      }
    }, 1000)
  } else if (!hasRunning && globalCdInterval) {
    clearInterval(globalCdInterval)
    globalCdInterval = null
  }
}

function onCountdownFinished(item: CountdownItem) {
  const st = item.soundType || 'chime'
  if (st !== 'silent' && item.notifyType !== 'popup_only') {
    soundPlayer.play(st as SoundType, props.soundVolume ?? 0.8)
  }
  if (item.notifyType !== 'sound_only') {
    ringingCountdown.value = item
  }
}

function dismissRingingCountdown() {
  ringingCountdown.value = null
}

function toggleCountdownItem(item: CountdownItem) {
  const target = countdownList.value.find(c => c.id === item.id) || item
  if (target.remainingSeconds <= 0) {
    target.remainingSeconds = target.initialSeconds
  }
  target.isRunning = !target.isRunning
  updateGlobalCdInterval()
}

function resetCountdownItem(item: CountdownItem) {
  const target = countdownList.value.find(c => c.id === item.id) || item
  target.isRunning = false
  const secs = Number(target.initialSeconds) || 600
  target.initialSeconds = secs
  target.remainingSeconds = secs
  updateGlobalCdInterval()
}

function openAddCountdownModal() {
  editingCountdownId.value = null
  countdownForm.value = {
    title: '',
    hours: 0,
    minutes: 10,
    seconds: 0,
    soundType: 'chime',
    notifyType: 'sound_and_popup',
    finishMessage: ''
  }
  showCountdownModal.value = true
}

function openEditCountdownModal(item: CountdownItem) {
  editingCountdownId.value = item.id
  const totalSecs = item.initialSeconds
  const h = Math.floor(totalSecs / 3600)
  const m = Math.floor((totalSecs % 3600) / 60)
  const s = totalSecs % 60
  countdownForm.value = {
    title: item.title,
    hours: h,
    minutes: m,
    seconds: s,
    soundType: item.soundType,
    notifyType: item.notifyType,
    finishMessage: item.finishMessage || ''
  }
  showCountdownModal.value = true
}

function setModalMinutes(mins: number) {
  countdownForm.value.hours = Math.floor(mins / 60)
  countdownForm.value.minutes = mins % 60
  countdownForm.value.seconds = 0
}

function saveCountdownModal() {
  const totalSecs = (countdownForm.value.hours * 3600) + (countdownForm.value.minutes * 60) + countdownForm.value.seconds
  if (totalSecs <= 0) return

  const title = countdownForm.value.title.trim() || `${formatDurationText(totalSecs)} 倒计时`

  if (editingCountdownId.value) {
    const idx = countdownList.value.findIndex(i => i.id === editingCountdownId.value)
    if (idx !== -1) {
      countdownList.value[idx].title = title
      countdownList.value[idx].initialSeconds = totalSecs
      countdownList.value[idx].remainingSeconds = totalSecs
      countdownList.value[idx].soundType = countdownForm.value.soundType
      countdownList.value[idx].finishMessage = countdownForm.value.finishMessage
      countdownList.value[idx].isRunning = false
    }
  } else {
    const newItem: CountdownItem = {
      id: 'cd_' + Date.now(),
      title,
      initialSeconds: totalSecs,
      remainingSeconds: totalSecs,
      isRunning: false,
      soundType: countdownForm.value.soundType,
      notifyType: 'sound_and_popup',
      finishMessage: countdownForm.value.finishMessage || '⏰ 倒计时已完成！'
    }
    countdownList.value.unshift(newItem)
  }

  showCountdownModal.value = false
  updateGlobalCdInterval()
}

async function removeCountdownItem(id: string) {
  const confirmed = await showConfirm({
    title: '删除倒计时',
    message: '确定要删除该倒计时设置吗？',
    confirmText: '确认删除',
    type: 'danger'
  })
  if (!confirmed) return

  countdownList.value = countdownList.value.filter(item => item.id !== id)
  updateGlobalCdInterval()
}

function formatDurationText(totalSec: number): string {
  const h = Math.floor(totalSec / 3600)
  const m = Math.floor((totalSec % 3600) / 60)
  const s = totalSec % 60
  if (h > 0) {
    return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
  }
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
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

// ----------------------------------------------------
// 2. Alarm Logic & State
// ----------------------------------------------------
export interface AlarmItem {
  id: string
  time: string
  label: string
  enabled: boolean
  repeatType: 'holiday_compensate' | 'compensate_only' | 'workday' | 'weekend' | 'everyday' | 'once' | 'custom'
  customDays: number[]
  skipHolidays: boolean
  ringOnCompensate: boolean
  soundType: SoundType | 'silent'
}

const defaultAlarms: AlarmItem[] = [
  {
    id: 'alarm-1',
    time: '07:30',
    label: '晨起早读与晨练',
    enabled: true,
    repeatType: 'holiday_compensate',
    customDays: [1, 2, 3, 4, 5],
    skipHolidays: true,
    ringOnCompensate: true,
    soundType: 'chime'
  },
  {
    id: 'alarm-2',
    time: '12:00',
    label: '午餐及休息提醒',
    enabled: true,
    repeatType: 'workday',
    customDays: [1, 2, 3, 4, 5],
    skipHolidays: false,
    ringOnCompensate: false,
    soundType: 'cyber'
  }
]

const alarmList = ref<AlarmItem[]>(
  JSON.parse(localStorage.getItem('todo_pro_alarm_list') || 'null') || defaultAlarms
)

const alarmFilter = ref<'all' | 'enabled' | 'disabled'>('all')
const alarmSearch = ref('')
const ringingAlarm = ref<AlarmItem | null>(null)

const showAlarmModal = ref(false)
const editingAlarmId = ref<string | null>(null)
const alarmForm = ref({
  time: '08:00',
  label: '',
  repeatType: 'holiday_compensate' as AlarmItem['repeatType'],
  customDays: [1, 2, 3, 4, 5],
  skipHolidays: true,
  ringOnCompensate: true,
  soundType: 'chime' as SoundType | 'silent'
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
      const matchLabel = item.label.toLowerCase().includes(q)
      const matchTime = item.time.includes(q)
      if (!matchLabel && !matchTime) return false
    }
    return true
  })
})

function openAddAlarmModal() {
  editingAlarmId.value = null
  alarmForm.value = {
    time: '08:00',
    label: '',
    repeatType: 'holiday_compensate',
    customDays: [1, 2, 3, 4, 5],
    skipHolidays: true,
    ringOnCompensate: true,
    soundType: 'chime'
  }
  showAlarmModal.value = true
}

function openEditAlarmModal(item: AlarmItem) {
  editingAlarmId.value = item.id
  alarmForm.value = {
    time: item.time,
    label: item.label,
    repeatType: item.repeatType,
    customDays: [...item.customDays],
    skipHolidays: item.skipHolidays,
    ringOnCompensate: item.ringOnCompensate,
    soundType: item.soundType
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

function formatRepeatText(item: AlarmItem): string {
  switch (item.repeatType) {
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

function saveAlarmModal() {
  if (editingAlarmId.value) {
    const idx = alarmList.value.findIndex(a => a.id === editingAlarmId.value)
    if (idx !== -1) {
      alarmList.value[idx].time = alarmForm.value.time
      alarmList.value[idx].label = alarmForm.value.label.trim()
      alarmList.value[idx].repeatType = alarmForm.value.repeatType
      alarmList.value[idx].customDays = [...alarmForm.value.customDays]
      alarmList.value[idx].skipHolidays = alarmForm.value.skipHolidays
      alarmList.value[idx].ringOnCompensate = alarmForm.value.ringOnCompensate
      alarmList.value[idx].soundType = alarmForm.value.soundType
    }
  } else {
    const newAlarm: AlarmItem = {
      id: 'alarm_' + Date.now(),
      time: alarmForm.value.time,
      label: alarmForm.value.label.trim(),
      enabled: true,
      repeatType: alarmForm.value.repeatType,
      customDays: [...alarmForm.value.customDays],
      skipHolidays: alarmForm.value.skipHolidays,
      ringOnCompensate: alarmForm.value.ringOnCompensate,
      soundType: alarmForm.value.soundType
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
        }
      })
    }
  }, 1000)
}

onMounted(() => {
  updateGlobalCdInterval()
  startAlarmTicker()
})

onUnmounted(() => {
  if (globalCdInterval) clearInterval(globalCdInterval)
  if (alarmTickerId) clearInterval(alarmTickerId)
})
</script>

<style scoped>
.alarm-container {
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

/* Toolbar & Filters (Modeled directly after Todos) */
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

/* List & Grid */
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

.list-card-item.running {
  border-color: #6366f1;
  background: linear-gradient(135deg, var(--bg-card, #ffffff) 0%, rgba(99, 102, 241, 0.03) 100%);
}

.list-card-item.completed,
.list-card-item.disabled {
  opacity: 0.72;
}

.card-left-indicator {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.mini-timer-circle,
.mini-alarm-icon {
  width: 38px;
  height: 38px;
  border-radius: 10px;
  background: var(--bg-surface, #f8fafc);
  border: 1px solid var(--border-color, #e2e8f0);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-muted, #64748b);
  transition: all 0.2s ease;
}

.mini-timer-circle.running,
.mini-alarm-icon.enabled {
  background: rgba(59, 130, 246, 0.1);
  color: var(--primary, #3b82f6);
  border-color: rgba(59, 130, 246, 0.3);
}

.mini-timer-circle.done {
  background: rgba(16, 185, 129, 0.1);
  color: #10b981;
  border-color: rgba(16, 185, 129, 0.3);
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
  font-size: 14.5px;
  font-weight: 600;
  color: var(--text-main, #0f172a);
}

.alarm-time-huge {
  font-size: 20px;
  font-weight: 800;
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
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
  background: rgba(99, 102, 241, 0.12);
  color: #6366f1;
}

.status-tag.running .dot {
  animation: pulse 1.5s infinite;
}

.status-tag.finished {
  background: rgba(16, 185, 129, 0.12);
  color: #10b981;
}

.sound-tag,
.alarm-tag-label,
.alarm-tag-repeat {
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

.alarm-tag-repeat {
  color: var(--primary, #3b82f6);
  background: rgba(59, 130, 246, 0.08);
  border-color: rgba(59, 130, 246, 0.2);
}

.card-time-display {
  display: flex;
  align-items: baseline;
  gap: 8px;
  font-size: 13px;
}

.digits-time {
  font-size: 16px;
  font-weight: 700;
  font-family: ui-monospace, SFMono-Regular, monospace;
  font-variant-numeric: tabular-nums;
  color: var(--primary, #3b82f6);
}

.digits-total {
  font-size: 12px;
  color: var(--text-muted, #94a3b8);
}

.finish-msg-tip {
  font-size: 12px;
  color: var(--text-muted, #64748b);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.alarm-sub-desc {
  font-size: 12px;
  color: var(--text-muted, #64748b);
}

.smart-tip {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  color: #8b5cf6;
  font-weight: 500;
}

/* Progress bar inside card */
.item-progress-track {
  width: 100%;
  height: 4px;
  background: var(--border-color, #e2e8f0);
  border-radius: 4px;
  overflow: hidden;
  margin-top: 4px;
}

.item-progress-bar {
  height: 100%;
  background: linear-gradient(90deg, #6366f1, #ec4899);
  transition: width 0.5s ease;
}

.item-progress-bar.done {
  background: #10b981;
}

/* Actions in Card */
.card-actions {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}

.btn-action-primary {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  border-radius: 8px;
  border: none;
  background: var(--primary, #3b82f6);
  color: #ffffff;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-action-primary:hover {
  filter: brightness(1.1);
  transform: translateY(-1px);
}

.btn-action-primary.running {
  background: #f59e0b;
}

.icon-btn-action {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
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

/* Switch Toggle */
.switch-toggle {
  position: relative;
  display: inline-block;
  width: 42px;
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
  transform: translateX(18px);
}

/* Modal Windows */
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

.label-with-presets {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.quick-preset-chips {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.preset-chip {
  padding: 4px 10px;
  border-radius: 6px;
  border: 1px solid var(--border-color, #e2e8f0);
  background: var(--bg-surface, #f8fafc);
  color: var(--text-main, #0f172a);
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.preset-chip:hover {
  background: rgba(59, 130, 246, 0.1);
  border-color: var(--primary, #3b82f6);
  color: var(--primary, #3b82f6);
}

.time-inputs-row {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  margin-top: 8px;
}

.time-unit-box {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.unit-input {
  width: 64px;
  text-align: center;
  font-size: 18px;
  font-weight: 700;
  font-family: ui-monospace, monospace;
  padding: 8px 4px;
  border-radius: 8px;
  border: 1px solid var(--border-color, #e2e8f0);
  background: var(--bg-surface, #ffffff);
  color: var(--text-main, #0f172a);
}

.unit-label {
  font-size: 11px;
  color: var(--text-muted, #64748b);
  font-weight: 600;
}

.unit-colon {
  font-size: 20px;
  font-weight: 800;
  color: var(--text-muted, #94a3b8);
  margin-bottom: 16px;
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

.modal-footer {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 10px;
  padding: 14px 22px;
  border-top: 1px solid var(--border-color, #e2e8f0);
}

/* Ringing Notifications */
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
  font-size: 24px;
  font-weight: 800;
  color: var(--text-main, #0f172a);
  margin: 8px 0;
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

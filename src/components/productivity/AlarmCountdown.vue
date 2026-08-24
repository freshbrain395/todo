<template>
  <div class="alarm-container animate-fade-in">
    <div class="alarm-workspace">
      <!-- Sub Tab Switcher (Show if mode prop is not specified) -->
      <div v-if="!props.mode" class="sub-tabs">
        <button
          class="sub-tab-btn"
          :class="{ active: tab === 'countdown' }"
          @click="tab = 'countdown'"
        >
          <Hourglass :size="15" /> 快捷倒计时 (Countdown)
        </button>
        <button
          class="sub-tab-btn"
          :class="{ active: tab === 'alarm' }"
          @click="tab = 'alarm'"
        >
          <Bell :size="15" /> 闹钟 (Alarm)
        </button>
      </div>

      <!-- Tab 1: Countdown Mode (Split-pane Left-List Right-Config View) -->
      <div v-if="tab === 'countdown'" class="countdown-split-workspace">
        <!-- Left Pane: Countdown Timers List -->
        <div class="countdown-left-pane">
          <div class="pane-header">
            <div class="header-title">
              <Hourglass :size="18" class="icon-hourglass" />
              <span>我的倒计时列表</span>
              <span class="count-badge">{{ countdownList.length }} 个</span>
            </div>
            <button class="btn btn-sm btn-primary" @click="createNewCountdown">
              <Plus :size="14" /> 新建倒计时
            </button>
          </div>

          <div class="countdown-list-scroll">
            <div class="countdown-cards-stack">
              <div
                v-for="item in countdownList"
                :key="item.id"
                class="countdown-card-item"
                :class="{ active: selectedCountdownId === item.id, running: item.isRunning }"
                @click="selectedCountdownId = item.id"
              >
                <div class="card-item-left">
                  <div class="card-item-title">{{ item.title }}</div>
                  <div class="card-item-time">
                    <span class="time-main">{{ formatDurationText(item.remainingSeconds) }}</span>
                    <span class="time-sub">/ {{ formatDurationText(item.initialSeconds) }}</span>
                  </div>
                  <div class="card-item-tags">
                    <span class="status-tag" :class="{ running: item.isRunning, finished: item.remainingSeconds === 0 }">
                      <span class="dot"></span>
                      {{ item.isRunning ? '计时中' : item.remainingSeconds === 0 ? '已完成' : '就绪' }}
                    </span>
                    <span class="sound-tag">{{ soundTypeShortLabel(item.soundType) }}</span>
                  </div>
                </div>

                <div class="card-item-right" @click.stop>
                  <button
                    class="icon-btn action-play-btn"
                    :class="{ running: item.isRunning }"
                    @click="toggleCountdownItem(item)"
                    :title="item.isRunning ? '暂停' : '开始'"
                  >
                    <Pause v-if="item.isRunning" :size="15" />
                    <Play v-else :size="15" />
                  </button>

                  <button
                    class="icon-btn reset-btn"
                    @click="resetCountdownItem(item)"
                    title="重置倒计时"
                  >
                    <RotateCcw :size="14" />
                  </button>

                  <button
                    class="icon-btn delete-btn"
                    @click="removeCountdownItem(item.id)"
                    title="删除此倒计时"
                  >
                    <Trash2 :size="14" />
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Right Pane: Active Timer Focus Display & Configuration Form -->
        <div class="countdown-right-pane" v-if="activeCountdown">
          <div class="pane-header">
            <div class="header-title">
              <Sliders :size="18" class="icon-sliders" />
              <span>倒计时控制台 & 详细配置</span>
            </div>
          </div>

          <div class="countdown-right-content">
            <!-- Focus Big Ring Display -->
            <div class="active-timer-focus-box">
              <div class="focus-display-section">
                <!-- Adjust Left -->
                <div class="adjust-group left">
                  <button
                    class="btn-adjust"
                    @click="adjustCountdownTime(activeCountdown, -5)"
                    title="减少5分钟"
                    :disabled="activeCountdown.remainingSeconds <= 300"
                  >
                    -5m
                  </button>
                  <button
                    class="btn-adjust"
                    @click="adjustCountdownTime(activeCountdown, -1)"
                    title="减少1分钟"
                    :disabled="activeCountdown.remainingSeconds <= 60"
                  >
                    -1m
                  </button>
                </div>

                <!-- Circular Ring -->
                <div class="timer-circle-wrapper" :class="{ 'is-active': activeCountdown.isRunning }">
                  <svg class="progress-ring" width="220" height="220">
                    <defs>
                      <linearGradient id="countdownGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                        <stop offset="0%" stop-color="#DD6B20" />
                        <stop offset="100%" stop-color="#805AD5" />
                      </linearGradient>
                    </defs>
                    <circle
                      class="progress-ring-bg"
                      stroke-width="10"
                      r="95"
                      cx="110"
                      cy="110"
                    />
                    <circle
                      class="progress-ring-fill"
                      stroke-width="10"
                      r="95"
                      cx="110"
                      cy="110"
                      stroke="url(#countdownGradient)"
                      :style="{
                        strokeDasharray: `${2 * Math.PI * 95} ${2 * Math.PI * 95}`,
                        strokeDashoffset: `${(2 * Math.PI * 95) - (((activeCountdown.initialSeconds - activeCountdown.remainingSeconds) / (activeCountdown.initialSeconds || 1)) * 2 * Math.PI * 95)}`
                      }"
                    />
                  </svg>

                  <div class="timer-center-text">
                    <span class="time-number">{{ formatDurationText(activeCountdown.remainingSeconds) }}</span>
                    <span class="timer-status-badge" :class="{ running: activeCountdown.isRunning }">
                      <span class="status-dot"></span>
                      {{ activeCountdown.isRunning ? '计时中' : activeCountdown.remainingSeconds === 0 ? '计时完成' : '准备就绪' }}
                    </span>
                  </div>
                </div>

                <!-- Adjust Right -->
                <div class="adjust-group right">
                  <button class="btn-adjust" @click="adjustCountdownTime(activeCountdown, 1)" title="增加1分钟">
                    +1m
                  </button>
                  <button class="btn-adjust" @click="adjustCountdownTime(activeCountdown, 5)" title="增加5分钟">
                    +5m
                  </button>
                </div>
              </div>

              <!-- Main Control Row -->
              <div class="focus-controls-row">
                <button class="btn btn-reset" @click="resetCountdownItem(activeCountdown)" title="重置倒计时">
                  <RotateCcw :size="16" /> 重置
                </button>

                <button
                  class="btn btn-toggle-run"
                  :class="{ 'is-running': activeCountdown.isRunning }"
                  @click="toggleCountdownItem(activeCountdown)"
                >
                  <Pause v-if="activeCountdown.isRunning" :size="20" />
                  <Play v-else :size="20" />
                  <span>{{ activeCountdown.isRunning ? '暂停计时' : '开始倒计时' }}</span>
                </button>
              </div>
            </div>

            <!-- Configuration Details Card -->
            <div class="config-form-card">
              <div class="form-group">
                <label class="form-label">倒计时名称 / 备注 *</label>
                <input
                  type="text"
                  v-model="activeCountdown.title"
                  class="text-input"
                  placeholder="例如: 番茄专注 / 煮温泉蛋 / 歇息5分钟..."
                />
              </div>

              <div class="form-group">
                <label class="form-label">快捷预设时长</label>
                <div class="preset-chips-row">
                  <button class="chip-btn" :class="{ active: activeCountdown.initialSeconds === 60 }" @click="setCountdownPreset(activeCountdown, 1)">1 分钟</button>
                  <button class="chip-btn" :class="{ active: activeCountdown.initialSeconds === 300 }" @click="setCountdownPreset(activeCountdown, 5)">5 分钟</button>
                  <button class="chip-btn" :class="{ active: activeCountdown.initialSeconds === 600 }" @click="setCountdownPreset(activeCountdown, 10)">10 分钟</button>
                  <button class="chip-btn" :class="{ active: activeCountdown.initialSeconds === 1500 }" @click="setCountdownPreset(activeCountdown, 25)">25 分钟</button>
                  <button class="chip-btn" :class="{ active: activeCountdown.initialSeconds === 1800 }" @click="setCountdownPreset(activeCountdown, 30)">30 分钟</button>
                  <button class="chip-btn" :class="{ active: activeCountdown.initialSeconds === 3600 }" @click="setCountdownPreset(activeCountdown, 60)">60 分钟</button>
                </div>
              </div>

              <div class="form-group">
                <label class="form-label">倒计时结束提醒音效</label>
                <select v-model="activeCountdown.soundType" class="select-input">
                  <option value="chime">清脆金铃 (Digital Chime)</option>
                  <option value="marimba">柔和木音 (Soft Marimba)</option>
                  <option value="cyber">科技脉冲 (Cyber Pulse)</option>
                  <option value="beep">警报蜂鸣 (Beep Alert)</option>
                  <option value="silent">无声 (仅弹窗提醒)</option>
                </select>
              </div>

              <div class="form-group">
                <label class="form-label">提醒交互方式</label>
                <select v-model="activeCountdown.notifyType" class="select-input">
                  <option value="sound_and_popup">声音响铃 + 弹窗提醒 (默认)</option>
                  <option value="sound_only">仅播放声音提醒</option>
                  <option value="popup_only">仅显示弹窗提醒</option>
                </select>
              </div>

              <div class="form-group">
                <label class="form-label">结束提醒提示词 / 消息文本</label>
                <input
                  type="text"
                  v-model="activeCountdown.finishMessage"
                  class="text-input"
                  placeholder="例如: 8分钟到了，温泉蛋煮好啦！"
                />
              </div>

              <div class="config-actions">
                <button class="btn btn-outline" @click="resetCountdownItem(activeCountdown)">
                  重置为初始时长
                </button>
                <button class="btn btn-danger-outline" @click="removeCountdownItem(activeCountdown.id)">
                  <Trash2 :size="14" /> 删除倒计时
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Tab 2: Alarm Mode (Split-pane Left-List Right-Config View) -->
      <div v-else class="alarm-split-workspace">
        <!-- Left Pane: Alarm List -->
        <div class="alarm-left-pane">
          <div class="pane-header">
            <div class="header-title">
              <Bell :size="18" class="icon-bell" />
              <span>我的闹钟列表</span>
              <span class="alarm-count-badge">{{ alarmList.length }} 个</span>
            </div>
            <button class="btn btn-sm btn-primary" @click="resetFormForNew">
              <Plus :size="14" /> 新建
            </button>
          </div>

          <div class="alarm-list-scroll">
            <div v-if="alarmList.length === 0" class="empty-alarm-state">
              <div class="empty-icon"><Bell :size="36" :stroke-width="1.5" /></div>
              <p class="empty-text">暂无已设闹钟，右侧面板直接配置添加！</p>
            </div>

            <div v-else class="alarm-cards-stack">
              <div
                v-for="item in alarmList"
                :key="item.id"
                class="alarm-card-item"
                :class="{ active: selectedAlarmId === item.id, disabled: !item.enabled }"
                @click="selectAlarmToEdit(item)"
              >
                <div class="alarm-item-left">
                  <div class="alarm-time-display">{{ item.time }}</div>
                  <div class="alarm-meta-info">
                    <span class="alarm-tag-label" v-if="item.label">
                      <Tag :size="11" /> {{ item.label }}
                    </span>
                    <span class="alarm-tag-repeat">
                      <Repeat :size="11" /> {{ formatRepeatText(item) }}
                    </span>
                  </div>
                </div>

                <div class="alarm-item-right" @click.stop>
                  <label class="switch-toggle" title="开启/关闭闹钟">
                    <input
                      type="checkbox"
                      :checked="item.enabled"
                      @change="item.enabled = !item.enabled"
                    />
                    <span class="slider-round"></span>
                  </label>

                  <button class="icon-btn delete-btn" @click="removeAlarm(item.id)" title="删除闹钟">
                    <Trash2 :size="15" />
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Right Pane: Direct Configuration Form -->
        <div class="alarm-right-pane">
          <div class="pane-header">
            <div class="header-title">
              <Sliders :size="18" class="icon-sliders" />
              <span>{{ editingAlarmId ? '编辑闹钟配置' : '新建闹钟配置' }}</span>
            </div>
          </div>

          <div class="config-form-card">
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

            <!-- 调休闹钟高级设置面板 -->
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
                <Sparkles :size="14" /> 已接入法定节假日与调休补班日历，自动识别调休日，避免假期误响与补班漏响。
              </div>
            </div>

            <div v-if="alarmForm.repeatType === 'custom'" class="form-group">
              <label class="form-label">选择重复星期:</label>
              <div class="weekdays-selector">
                <button
                  v-for="day in [1, 2, 3, 4, 5, 6, 0]"
                  :key="day"
                  class="weekday-chip"
                  :class="{ active: alarmForm.customDays.includes(day) }"
                  @click="toggleCustomDay(day)"
                >
                  {{ weekDayLabel(day) }}
                </button>
              </div>
            </div>

            <div class="config-actions">
              <button v-if="editingAlarmId" class="btn btn-outline" @click="resetFormForNew">
                重置为新建
              </button>
              <button class="btn btn-primary btn-save-large" @click="saveAlarmForm">
                <Check :size="16" /> {{ editingAlarmId ? '保存更改' : '直接添加闹钟' }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Countdown Ringing/Finished Notification Modal -->
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

    <!-- Alarm Ringing Snooze Notification Banner/Modal -->
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
  Trash2, Plus, Tag, Repeat, Check, Coffee, Sliders, Sparkles
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

// Multi-Countdown Timer State & Data Model
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

const selectedCountdownId = ref<string>(countdownList.value[0]?.id || '')
const ringingCountdown = ref<CountdownItem | null>(null)

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

const activeCountdown = computed(() => {
  return countdownList.value.find(item => item.id === selectedCountdownId.value) || countdownList.value[0]
})

// Global tick timer for all countdown items
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
  if (item.notifyType === 'sound_and_popup' || item.notifyType === 'sound_only') {
    if (item.soundType !== 'silent') {
      soundPlayer.play(item.soundType as SoundType, props.soundVolume ?? 0.8)
    }
  }
  if (item.notifyType === 'sound_and_popup' || item.notifyType === 'popup_only') {
    ringingCountdown.value = item
  }
}

function dismissRingingCountdown() {
  ringingCountdown.value = null
}

function toggleCountdownItem(item: CountdownItem) {
  if (item.remainingSeconds <= 0) {
    item.remainingSeconds = item.initialSeconds
  }
  item.isRunning = !item.isRunning
  updateGlobalCdInterval()
}

function resetCountdownItem(item: CountdownItem) {
  item.isRunning = false
  item.remainingSeconds = item.initialSeconds
  updateGlobalCdInterval()
}

function adjustCountdownTime(item: CountdownItem, deltaMinutes: number) {
  const newSecs = item.remainingSeconds + deltaMinutes * 60
  if (newSecs >= 10) {
    item.remainingSeconds = newSecs
    if (!item.isRunning) {
      item.initialSeconds = newSecs
    }
  }
}

function setCountdownPreset(item: CountdownItem, mins: number) {
  item.isRunning = false
  item.initialSeconds = mins * 60
  item.remainingSeconds = mins * 60
  updateGlobalCdInterval()
}

function createNewCountdown() {
  const newId = 'cd_' + Date.now()
  const newItem: CountdownItem = {
    id: newId,
    title: '新建倒计时',
    initialSeconds: 10 * 60,
    remainingSeconds: 10 * 60,
    isRunning: false,
    soundType: 'chime',
    notifyType: 'sound_and_popup',
    finishMessage: '⏰ 倒计时已完成！'
  }
  countdownList.value.unshift(newItem)
  selectedCountdownId.value = newId
}

async function removeCountdownItem(id: string) {
  const confirmed = await showConfirm({
    title: '删除倒计时',
    message: '确定要删除该倒计时设置吗？',
    confirmText: '确认删除',
    type: 'danger'
  })
  if (!confirmed) return

  if (countdownList.value.length <= 1) {
    alert('请至少保留一个倒计时项目！')
    return
  }

  countdownList.value = countdownList.value.filter(c => c.id !== id)
  if (selectedCountdownId.value === id) {
    selectedCountdownId.value = countdownList.value[0]?.id || ''
  }
  updateGlobalCdInterval()
}

function formatDurationText(totalSeconds: number): string {
  const h = Math.floor(totalSeconds / 3600)
  const m = Math.floor((totalSeconds % 3600) / 60)
  const s = totalSeconds % 60
  if (h > 0) {
    return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
  }
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
}

function soundTypeShortLabel(sound: SoundType | 'silent'): string {
  const map: Record<string, string> = {
    chime: '🔔 拆分响铃',
    marimba: '🪵 木音提醒',
    cyber: '⚡ 科技音',
    beep: '🚨 警报音',
    silent: '🔇 静音'
  }
  return map[sound] || sound
}


// Alarm State (Split View Pro Features)
export type RepeatType = 'once' | 'workday' | 'holiday_compensate' | 'compensate_only' | 'weekend' | 'everyday' | 'custom'

export interface AlarmItem {
  id: number
  time: string
  label: string
  enabled: boolean
  repeatType: RepeatType
  customDays: number[]
  skipHolidays?: boolean
  ringOnCompensate?: boolean
}

// 示例法定调休补班日与节假日库（支持智能调度）
const compensateWorkdayList = ref<string[]>([
  '2026-01-25', '2026-02-08', '2026-04-26', '2026-05-09',
  '2026-09-27', '2026-10-10'
])

const officialHolidayList = ref<string[]>([
  '2026-01-01', '2026-02-16', '2026-02-17', '2026-02-18',
  '2026-04-05', '2026-05-01', '2026-10-01', '2026-10-02'
])

const alarmList = ref<AlarmItem[]>(
  JSON.parse(localStorage.getItem('todo_pro_alarm_list') || '[]')
)
const ringingAlarm = ref<AlarmItem | null>(null)
const editingAlarmId = ref<number | null>(null)
const selectedAlarmId = ref<number | null>(null)

const alarmForm = ref({
  time: '08:00',
  label: '晨起早读',
  repeatType: 'holiday_compensate' as RepeatType,
  customDays: [1, 2, 3, 4, 5] as number[],
  skipHolidays: true,
  ringOnCompensate: true
})

watch(alarmList, (newVal) => {
  localStorage.setItem('todo_pro_alarm_list', JSON.stringify(newVal))
}, { deep: true })

function resetFormForNew() {
  editingAlarmId.value = null
  selectedAlarmId.value = null
  alarmForm.value = {
    time: '08:00',
    label: '',
    repeatType: 'holiday_compensate',
    customDays: [1, 2, 3, 4, 5],
    skipHolidays: true,
    ringOnCompensate: true
  }
}

function selectAlarmToEdit(item: AlarmItem) {
  editingAlarmId.value = item.id
  selectedAlarmId.value = item.id
  alarmForm.value = {
    time: item.time,
    label: item.label,
    repeatType: item.repeatType,
    customDays: [...item.customDays],
    skipHolidays: item.skipHolidays ?? true,
    ringOnCompensate: item.ringOnCompensate ?? true
  }
}

function toggleCustomDay(day: number) {
  const idx = alarmForm.value.customDays.indexOf(day)
  if (idx >= 0) {
    alarmForm.value.customDays.splice(idx, 1)
  } else {
    alarmForm.value.customDays.push(day)
  }
}

function weekDayLabel(day: number) {
  const map: Record<number, string> = { 1: '一', 2: '二', 3: '三', 4: '四', 5: '五', 6: '六', 0: '日' }
  return `周${map[day]}`
}

function formatRepeatText(item: AlarmItem): string {
  if (item.repeatType === 'once') return '单次响铃'
  if (item.repeatType === 'holiday_compensate') return '⚡ 智能调休 (避假/补班响)'
  if (item.repeatType === 'compensate_only') return '📅 仅调休补班日'
  if (item.repeatType === 'workday') return '工作日 (周一至周五)'
  if (item.repeatType === 'weekend') return '周末 (周六日)'
  if (item.repeatType === 'everyday') return '每天响铃'
  if (item.repeatType === 'custom') {
    if (item.customDays.length === 0) return '不重复'
    return '周 ' + item.customDays.map(d => weekDayLabel(d)).join(' ')
  }
  return '单次'
}

function saveAlarmForm() {
  if (!alarmForm.value.time) {
    alert('请选择响铃时间！')
    return
  }

  if (editingAlarmId.value) {
    const idx = alarmList.value.findIndex(a => a.id === editingAlarmId.value)
    if (idx >= 0) {
      alarmList.value[idx].time = alarmForm.value.time
      alarmList.value[idx].label = alarmForm.value.label.trim() || '响铃提醒'
      alarmList.value[idx].repeatType = alarmForm.value.repeatType
      alarmList.value[idx].customDays = [...alarmForm.value.customDays]
      alarmList.value[idx].skipHolidays = alarmForm.value.skipHolidays
      alarmList.value[idx].ringOnCompensate = alarmForm.value.ringOnCompensate
    }
  } else {
    alarmList.value.unshift({
      id: Date.now(),
      time: alarmForm.value.time,
      label: alarmForm.value.label.trim() || '响铃提醒',
      enabled: true,
      repeatType: alarmForm.value.repeatType,
      customDays: [...alarmForm.value.customDays],
      skipHolidays: alarmForm.value.skipHolidays,
      ringOnCompensate: alarmForm.value.ringOnCompensate
    })
  }
  resetFormForNew()
}

function removeAlarm(id: number) {
  alarmList.value = alarmList.value.filter(a => a.id !== id)
  if (editingAlarmId.value === id) {
    resetFormForNew()
  }
}

function formatDateStr(d: Date): string {
  const yyyy = d.getFullYear()
  const mm = String(d.getMonth() + 1).padStart(2, '0')
  const dd = String(d.getDate()).padStart(2, '0')
  return `${yyyy}-${mm}-${dd}`
}

function shouldRingToday(item: AlarmItem, now: Date): boolean {
  const dateStr = formatDateStr(now)
  const isHoliday = officialHolidayList.value.includes(dateStr)
  const isCompensateWorkday = compensateWorkdayList.value.includes(dateStr)

  if (item.repeatType === 'holiday_compensate') {
    if (item.skipHolidays && isHoliday) return false
    if (item.ringOnCompensate && isCompensateWorkday) return true
    const currentDay = now.getDay()
    return currentDay >= 1 && currentDay <= 5
  }

  if (item.repeatType === 'compensate_only') {
    return isCompensateWorkday
  }

  const currentDay = now.getDay()
  if (item.repeatType === 'workday') return currentDay >= 1 && currentDay <= 5
  if (item.repeatType === 'weekend') return currentDay === 0 || currentDay === 6
  if (item.repeatType === 'everyday') return true
  if (item.repeatType === 'custom') return item.customDays.includes(currentDay)
  return true
}

let alarmCheckTimer: any = null

function checkAlarms() {
  const now = new Date()
  const currentHM = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`
  const currentSec = now.getSeconds()

  if (currentSec === 0) {
    alarmList.value.forEach(a => {
      if (a.enabled && a.time === currentHM && shouldRingToday(a, now)) {
        soundPlayer.play(props.soundType || 'chime', props.soundVolume ?? 0.8)
        ringingAlarm.value = a
        if (a.repeatType === 'once') {
          a.enabled = false
        }
      }
    })
  }
}

function snoozeRingingAlarm() {
  soundPlayer.play(props.soundType || 'chime', props.soundVolume ?? 0.8)
  const now = new Date()
  now.setMinutes(now.getMinutes() + 5)
  const snoozeTime = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`

  alarmList.value.unshift({
    id: Date.now(),
    time: snoozeTime,
    label: `(贪睡) ${ringingAlarm.value?.label || '闹钟'}`,
    enabled: true,
    repeatType: 'once',
    customDays: []
  })
  ringingAlarm.value = null
  alert('💤 已开启贪睡模式，5 分钟后再次提醒！')
}

function dismissRingingAlarm() {
  ringingAlarm.value = null
}

onMounted(() => {
  alarmCheckTimer = setInterval(checkAlarms, 1000)
  updateGlobalCdInterval()
})

onUnmounted(() => {
  if (alarmCheckTimer) clearInterval(alarmCheckTimer)
  if (globalCdInterval) clearInterval(globalCdInterval)
})
</script>

<style scoped>
.alarm-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100%;
  min-height: 100%;
  width: 100%;
  padding: 16px 0;
  box-sizing: border-box;
  overflow-y: auto;
  background: radial-gradient(circle at center, rgba(221, 107, 32, 0.05) 0%, transparent 70%);
}

.alarm-workspace {
  width: 100%;
  max-width: 1100px;
  background-color: transparent;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
  padding: 0 16px;
  box-sizing: border-box;
  margin: auto 0;
}

.sub-tabs {
  display: flex;
  gap: 8px;
  background-color: var(--bg-surface);
  padding: 5px;
  border-radius: 20px;
  border: 1px solid var(--border-color);
  box-shadow: var(--shadow-sm);
}

.sub-tab-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border-radius: 16px;
  border: none;
  background: transparent;
  color: var(--text-muted);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.25s ease;
}

.sub-tab-btn.active {
  background-color: var(--primary);
  color: #ffffff;
  box-shadow: 0 4px 12px rgba(49, 130, 206, 0.3);
}

/* 1. Countdown Full-screen Split Workspace Layout */
.countdown-split-workspace {
  display: flex;
  flex-direction: row;
  align-items: stretch;
  gap: 24px;
  width: 100%;
  background-color: transparent;
  border: none;
  border-radius: 0;
  padding: 0;
  box-shadow: none;
  box-sizing: border-box;
  min-height: 520px;
}

.countdown-left-pane {
  width: 320px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.countdown-right-pane {
  flex: 1;
  min-width: 300px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  border-left: 1px solid var(--border-color);
  padding-left: 24px;
}

@media (max-width: 820px) {
  .countdown-split-workspace {
    flex-direction: column;
  }
  .countdown-left-pane {
    width: 100%;
  }
  .countdown-right-pane {
    border-left: none;
    border-top: 1px solid var(--border-color);
    padding-left: 0;
    padding-top: 20px;
  }
}

.count-badge {
  font-size: 11px;
  font-weight: 700;
  background-color: rgba(221, 107, 32, 0.12);
  color: #DD6B20;
  padding: 2px 8px;
  border-radius: 10px;
}

.countdown-list-scroll {
  flex: 1;
  overflow-y: auto;
  max-height: 540px;
  padding-right: 4px;
}

.countdown-cards-stack {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.countdown-card-item {
  background-color: transparent;
  border: none;
  border-bottom: 1px solid var(--border-color);
  border-radius: 0;
  border-left: 3px solid transparent;
  padding: 12px 10px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: none;
}

.countdown-card-item:hover {
  background-color: var(--bg-card-hover);
  border-left-color: var(--text-muted);
}

.countdown-card-item.active {
  background-color: rgba(221, 107, 32, 0.08);
  border-left-color: #DD6B20;
  box-shadow: none;
}

.card-item-left {
  display: flex;
  flex-direction: column;
  gap: 4px;
  flex: 1;
  min-width: 0;
}

.card-item-title {
  font-size: 13.5px;
  font-weight: 700;
  color: var(--text-main);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.card-item-time {
  display: flex;
  align-items: baseline;
  gap: 4px;
  font-family: 'Roboto Mono', monospace, sans-serif;
}

.time-main {
  font-size: 16px;
  font-weight: 700;
  color: #DD6B20;
}

.time-sub {
  font-size: 11px;
  color: var(--text-muted);
}

.card-item-tags {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 2px;
}

.status-tag {
  font-size: 10px;
  font-weight: 600;
  padding: 1px 6px;
  border-radius: 4px;
  background-color: var(--bg-app);
  color: var(--text-muted);
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.status-tag.running {
  background-color: rgba(221, 107, 32, 0.15);
  color: #DD6B20;
}

.status-tag.finished {
  background-color: rgba(16, 185, 129, 0.15);
  color: #10B981;
}

.status-tag .dot {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background-color: currentColor;
}

.sound-tag {
  font-size: 10px;
  color: var(--text-muted);
  background-color: var(--bg-app);
  padding: 1px 6px;
  border-radius: 4px;
}

.card-item-right {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}

.action-play-btn {
  background-color: rgba(221, 107, 32, 0.12);
  color: #DD6B20;
  border-radius: 50%;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  cursor: pointer;
  transition: all 0.2s ease;
}

.action-play-btn:hover {
  transform: scale(1.1);
  background-color: #DD6B20;
  color: #FFFFFF;
}

.action-play-btn.running {
  background-color: #DD6B20;
  color: #FFFFFF;
}

.countdown-right-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.active-timer-focus-box {
  background-color: transparent;
  border: none;
  border-radius: 0;
  padding: 10px 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.focus-display-section {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 20px;
  width: 100%;
}

.adjust-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.btn-adjust {
  background-color: var(--bg-surface);
  border: 1px solid var(--border-color);
  color: var(--text-main);
  width: 42px;
  height: 42px;
  border-radius: 50%;
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
  box-shadow: var(--shadow-sm);
}

.btn-adjust:hover:not(:disabled) {
  border-color: var(--primary);
  color: var(--primary);
  transform: scale(1.08);
}

.btn-adjust:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

.timer-circle-wrapper {
  position: relative;
  width: 220px;
  height: 220px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: transform 0.3s ease;
}

.timer-circle-wrapper.is-active {
  transform: scale(1.02);
}

.progress-ring-bg {
  fill: transparent;
  stroke: var(--bg-surface);
}

.progress-ring-fill {
  fill: transparent;
  stroke-linecap: round;
  transition: stroke-dashoffset 0.8s linear;
  transform: rotate(-90deg);
  transform-origin: 50% 50%;
}

.timer-center-text {
  position: absolute;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
}

.time-number {
  font-family: 'Roboto Mono', monospace, sans-serif;
  font-size: 42px;
  font-weight: 800;
  color: var(--text-main);
  letter-spacing: -1px;
}

.timer-status-badge {
  font-size: 11px;
  font-weight: 600;
  color: var(--text-muted);
  background-color: var(--bg-surface);
  padding: 3px 10px;
  border-radius: 12px;
  border: 1px solid var(--border-color);
  display: flex;
  align-items: center;
  gap: 6px;
}

.timer-status-badge.running {
  color: #DD6B20;
  border-color: rgba(221, 107, 32, 0.3);
  background-color: rgba(221, 107, 32, 0.08);
}

.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background-color: currentColor;
}

.focus-controls-row {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 14px;
}

.btn-toggle-run {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background: linear-gradient(135deg, #DD6B20 0%, #C05621 100%);
  color: #FFFFFF;
  border: none;
  font-size: 14px;
  font-weight: 700;
  padding: 10px 24px;
  border-radius: 20px;
  cursor: pointer;
  transition: all 0.25s ease;
  box-shadow: 0 4px 16px rgba(221, 107, 32, 0.35);
}

.btn-toggle-run:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(221, 107, 32, 0.45);
}

.btn-toggle-run.is-running {
  background: linear-gradient(135deg, #E53E3E 0%, #C53030 100%);
  box-shadow: 0 4px 16px rgba(229, 62, 62, 0.35);
}

.preset-chips-row {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.chip-btn {
  background-color: var(--bg-surface);
  border: 1px solid var(--border-color);
  border-radius: 16px;
  padding: 5px 12px;
  font-size: 11.5px;
  font-weight: 600;
  color: var(--text-main);
  cursor: pointer;
  transition: all 0.2s ease;
}

.chip-btn:hover, .chip-btn.active {
  border-color: #DD6B20;
  color: #DD6B20;
  background-color: rgba(221, 107, 32, 0.08);
}


/* 2. Alarm Split Workspace Layout */
.alarm-split-workspace {
  display: flex;
  flex-direction: row;
  align-items: stretch;
  gap: 24px;
  width: 100%;
  background-color: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 16px;
  padding: 24px;
  box-shadow: var(--shadow-md);
  box-sizing: border-box;
  min-height: 520px;
}

.alarm-left-pane {
  width: 320px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.alarm-right-pane {
  flex: 1;
  min-width: 300px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  border-left: 1px solid var(--border-color);
  padding-left: 24px;
}

@media (max-width: 820px) {
  .alarm-split-workspace {
    flex-direction: column;
  }
  .alarm-left-pane {
    width: 100%;
  }
  .alarm-right-pane {
    border-left: none;
    border-top: 1px solid var(--border-color);
    padding-left: 0;
    padding-top: 20px;
  }
}

.pane-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  padding-bottom: 12px;
  border-bottom: 1px dashed var(--border-color);
}

.pane-header .header-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 15px;
  font-weight: 700;
  color: var(--text-main);
}

.icon-bell, .icon-hourglass, .icon-sliders {
  color: var(--primary);
}

.alarm-count-badge {
  font-size: 11px;
  font-weight: 700;
  background-color: rgba(49, 130, 206, 0.12);
  color: var(--primary);
  padding: 2px 8px;
  border-radius: 10px;
}

.alarm-list-scroll {
  flex: 1;
  overflow-y: auto;
  max-height: 540px;
}

.empty-alarm-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 10px;
  text-align: center;
  color: var(--text-muted);
}

.empty-icon {
  font-size: 36px;
  margin: 0 0 10px 0;
}

.empty-text {
  font-size: 13px;
  margin: 0;
}

.alarm-cards-stack {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.alarm-card-item {
  background-color: transparent;
  border: none;
  border-bottom: 1px solid var(--border-color);
  border-radius: 0;
  border-left: 3px solid transparent;
  padding: 14px 10px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: none;
}

.alarm-card-item:hover {
  background-color: var(--bg-card-hover);
  border-left-color: var(--text-muted);
}

.alarm-card-item.active {
  background-color: rgba(49, 130, 206, 0.08);
  border-left-color: var(--primary);
  box-shadow: none;
}

.alarm-card-item.disabled {
  opacity: 0.5;
}

.alarm-item-left {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.alarm-time-display {
  font-family: 'Roboto Mono', monospace, sans-serif;
  font-size: 22px;
  font-weight: 800;
  color: var(--text-main);
}

.alarm-meta-info {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 11px;
  color: var(--text-muted);
}

.alarm-tag-label, .alarm-tag-repeat {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.alarm-item-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.switch-toggle {
  position: relative;
  display: inline-block;
  width: 40px;
  height: 22px;
}

.switch-toggle input {
  opacity: 0;
  width: 0;
  height: 0;
}

.slider-round {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: var(--border-color);
  transition: .3s;
  border-radius: 22px;
}

.slider-round:before {
  position: absolute;
  content: "";
  height: 16px;
  width: 16px;
  left: 3px;
  bottom: 3px;
  background-color: white;
  transition: .3s;
  border-radius: 50%;
}

input:checked + .slider-round {
  background-color: var(--primary);
}

input:checked + .slider-round:before {
  transform: translateX(18px);
}

.config-form-card {
  display: flex;
  flex-direction: column;
  gap: 16px;
  width: 100%;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-label {
  font-size: 13px;
  font-weight: 700;
  color: var(--text-main);
}

.text-input, .select-input {
  width: 100%;
  padding: 10px 14px;
  border-radius: var(--radius-sm, 8px);
  border: 1px solid var(--border-color);
  background-color: var(--bg-app);
  color: var(--text-main);
  font-size: 13px;
  outline: none;
  box-sizing: border-box;
}

.text-input:focus, .select-input:focus {
  border-color: var(--primary);
}

.compensate-config-box {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 12px 14px;
  background-color: rgba(221, 107, 32, 0.06);
  border: 1px dashed rgba(221, 107, 32, 0.3);
  border-radius: var(--radius-md, 8px);
  margin-top: -4px;
}

.checkbox-option {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  font-weight: 600;
  color: var(--text-main);
  cursor: pointer;
}

.checkbox-option input[type="checkbox"] {
  accent-color: var(--primary);
  width: 15px;
  height: 15px;
  cursor: pointer;
}

.compensate-tips {
  font-size: 11px;
  color: var(--text-muted);
  line-height: 1.4;
  padding-top: 4px;
  border-top: 1px dashed var(--border-color);
}

.weekdays-selector {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.weekday-chip {
  padding: 6px 12px;
  border-radius: 8px;
  border: 1px solid var(--border-color);
  background-color: var(--bg-app);
  color: var(--text-main);
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.weekday-chip.active {
  background-color: var(--primary);
  color: #ffffff;
  border-color: var(--primary);
}

.config-actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 8px;
}

.btn-save-large {
  padding: 10px 24px;
  font-size: 14px;
  font-weight: 700;
}

.modal-backdrop {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background-color: rgba(15, 23, 42, 0.65);
  backdrop-filter: blur(6px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 99999;
}

.ringing-card {
  background-color: var(--bg-card);
  border: 2px solid #DD6B20;
  border-radius: 20px;
  padding: 32px 40px;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.4);
}

.ringing-icon {
  font-size: 48px;
  margin-bottom: 8px;
}

.ringing-title {
  font-size: 20px;
  font-weight: 800;
  color: var(--text-main);
  margin: 0 0 6px 0;
}

.ringing-time {
  font-family: 'Roboto Mono', monospace, sans-serif;
  font-size: 24px;
  font-weight: 800;
  color: #DD6B20;
  margin-bottom: 8px;
}

.ringing-label {
  font-size: 14px;
  color: var(--text-muted);
  margin: 0 0 24px 0;
}

.ringing-actions {
  display: flex;
  gap: 12px;
}

.btn-snooze {
  background-color: var(--bg-surface);
  border: 1px solid var(--border-color);
  color: var(--text-main);
  padding: 10px 18px;
  border-radius: 10px;
  font-weight: 600;
  cursor: pointer;
}

.btn-dismiss {
  background-color: #DD6B20;
  color: #ffffff;
  border: none;
  padding: 10px 24px;
  border-radius: 10px;
  font-weight: 700;
  cursor: pointer;
}

.btn-dismiss:hover {
  background-color: #C05621;
}

.icon-btn {
  background: transparent;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  padding: 6px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s ease;
}

.icon-btn:hover {
  background-color: var(--bg-card-hover);
  color: var(--text-main);
}

.icon-btn.delete-btn:hover {
  color: #EF4444;
  background-color: rgba(239, 68, 68, 0.1);
}
</style>

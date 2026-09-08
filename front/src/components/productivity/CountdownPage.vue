<template>
  <div class="countdown-container animate-fade-in">
    <div class="pure-list-workspace">
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
                <span class="sound-tag clickable-sound-tag" @click.stop="previewSound(item.soundType)" title="点击试听提示音">
                  <Volume2 :size="11" />
                  {{ soundTypeShortLabel(item.soundType) }}
                </span>
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
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import {
  Hourglass, Play, Pause, RotateCcw,
  Trash2, Plus, Check, Sliders, Volume2, Search, X
} from 'lucide-vue-next'
import { soundPlayer, type SoundType } from '../../utils/audio'
import { showConfirm } from '../../utils/confirmState'
import { getUserConfig } from '../../utils/configManager'
import type { Countdown } from '../../types'

const props = defineProps<{
  soundVolume?: number
}>()

const defaultCountdownItems: Countdown[] = [
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

const countdownList = ref<Countdown[]>(
  JSON.parse(localStorage.getItem('todo_pro_countdown_list') || 'null') || defaultCountdownItems
)

const countdownFilter = ref<'all' | 'running' | 'completed'>('all')
const countdownSearch = ref('')
const ringingCountdown = ref<Countdown | null>(null)

const showCountdownModal = ref(false)
const editingCountdownId = ref<string | null>(null)
const countdownForm = ref<{
  title: string
  hours: number
  minutes: number
  seconds: number
  soundType: string
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
  localStorage.setItem('todo_pro_countdown_list', JSON.stringify(newVal))
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

function previewSound(soundType: string) {
  if (soundType && soundType !== 'silent') {
    const configVol = getUserConfig()?.soundVolume
    const vol = typeof props.soundVolume === 'number' ? props.soundVolume : (typeof configVol === 'number' ? configVol : 0.8)
    soundPlayer.play(soundType as SoundType, vol)
  }
}

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

function onCountdownFinished(item: Countdown) {
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

function toggleCountdownItem(item: Countdown) {
  const target = countdownList.value.find(c => c.id === item.id) || item
  if (target.remainingSeconds <= 0) {
    target.remainingSeconds = target.initialSeconds
  }
  target.isRunning = !target.isRunning
  updateGlobalCdInterval()
}

function resetCountdownItem(item: Countdown) {
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

function openEditCountdownModal(item: Countdown) {
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
    const newItem: Countdown = {
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

onMounted(() => {
  updateGlobalCdInterval()
})

onUnmounted(() => {
  if (globalCdInterval) clearInterval(globalCdInterval)
})
</script>

<style scoped>
.countdown-container {
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

.list-card-item.running {
  border-color: #6366f1;
  background: linear-gradient(135deg, var(--bg-card, #ffffff) 0%, rgba(99, 102, 241, 0.03) 100%);
}

.list-card-item.completed {
  opacity: 0.72;
}

.card-left-indicator {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.mini-timer-circle {
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

.mini-timer-circle.running {
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

.sound-tag {
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

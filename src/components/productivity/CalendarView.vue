<template>
  <div class="calendar-view-container animate-fade-in">
    <div class="calendar-single-workspace">
      <!-- Top Section: Monthly Interactive Calendar -->
      <div class="calendar-main-section">
        <!-- Calendar Header Controls -->
        <div class="calendar-header">
          <div class="month-display">
            <CalendarIcon :size="20" class="icon-primary" />
            <span class="year-month-text" v-if="calendarMode === 'year'">{{ currentYear }} 年</span>
            <span class="year-month-text" v-else-if="calendarMode === 'week'">{{ currentYear }} 年 {{ currentWeekDays[0]?.dateStr }} - {{ currentWeekDays[6]?.dateStr }}</span>
            <span class="year-month-text" v-else-if="calendarMode === 'day'">{{ currentYear }} 年 {{ selectedDate.getMonth() + 1 }} 月 {{ selectedDate.getDate() }} 日</span>
            <span class="year-month-text" v-else>{{ currentYear }} 年 {{ currentMonth + 1 }} 月</span>
            <span v-if="isCurrentMonthToday && calendarMode === 'month'" class="today-badge">本月</span>
          </div>

          <!-- View Mode Segmented Controls -->
          <div class="header-center-tabs">
            <div class="mode-segmented">
              <button class="mode-tab" :class="{ active: calendarMode === 'day' }" @click="calendarMode = 'day'">日</button>
              <button class="mode-tab" :class="{ active: calendarMode === 'week' }" @click="calendarMode = 'week'">周</button>
              <button class="mode-tab" :class="{ active: calendarMode === 'month' }" @click="calendarMode = 'month'">月</button>
              <button class="mode-tab" :class="{ active: calendarMode === 'year' }" @click="calendarMode = 'year'">年</button>
            </div>
          </div>

          <div class="header-actions">
            <button class="btn btn-sm btn-outline" @click="prevPeriod" title="上一个周期">
              <ChevronLeft :size="16" />
            </button>
            <button class="btn btn-sm btn-outline" @click="goToday" title="返回今天">
              今天
            </button>
            <button class="btn btn-sm btn-outline" @click="nextPeriod" title="下一个周期">
              <ChevronRight :size="16" />
            </button>
          </div>
        </div>

        <!-- 1. Day View -->
        <div v-if="calendarMode === 'day'" class="day-view-wrapper animate-fade-in">
          <!-- All Day & General Todos Section -->
          <div class="day-allday-section" v-if="dayEventsSummary.length > 0">
            <div class="allday-header">
              <span class="allday-title"><CalendarCheck :size="14" /> 当日待办事项与全天日程 ({{ dayEventsSummary.length }} 个)</span>
            </div>
            <div class="allday-events-grid">
              <div
                v-for="ev in dayEventsSummary"
                :key="ev.id"
                class="allday-event-chip"
                :class="[`priority-${ev.priority || 'medium'}`, { completed: ev.completed }]"
              >
                <div class="chip-top">
                  <span class="chip-time"><Clock :size="10" /> {{ ev.time }}</span>
                  <span class="chip-cat">{{ ev.category }}</span>
                </div>
                <div class="chip-title">{{ ev.title }}</div>
              </div>
            </div>
          </div>

          <!-- Hourly Timeline -->
          <div class="day-timeline-section">
            <div class="timeline-header-title"><Clock :size="14" /> 24 小时时间轴分布</div>
            <div class="day-timeline-scroll">
              <div v-for="slot in dayTimeSlots" :key="slot.hour" class="time-slot-row" :class="{ 'has-events': slot.events.length > 0 }">
                <div class="slot-time-label">{{ slot.label }}</div>
                <div class="slot-events-cell">
                  <div
                    v-for="ev in slot.events"
                    :key="ev.id"
                    class="slot-event-chip"
                    :class="[`priority-${ev.priority || 'medium'}`, { completed: ev.completed }]"
                  >
                    <span class="ev-chip-time" v-if="ev.time"><Clock :size="10" /> {{ ev.time }}</span>
                    <span class="ev-chip-title">{{ ev.title }}</span>
                    <span class="ev-chip-cat" v-if="ev.category">{{ ev.category }}</span>
                  </div>
                  <div v-if="slot.events.length === 0" class="empty-slot-hint">无指定时刻日程</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 2. Week View -->
        <div v-else-if="calendarMode === 'week'" class="week-view-wrapper animate-fade-in">
          <div class="week-columns-grid">
            <div
              v-for="day in currentWeekDays"
              :key="day.dateStr"
              class="week-column"
              :class="{ 'is-selected': day.isSelected, 'is-today': day.isToday }"
              @click="selectDate(day.date)"
            >
              <div class="week-col-header">
                <span class="col-week-label">周{{ day.weekLabel }}</span>
                <span class="col-date-num">{{ day.dateStr }}</span>
                <span v-if="day.holidayInfo?.badge" class="holiday-badge" :class="day.holidayInfo.isHoliday ? 'holiday' : 'compensate'">
                  {{ day.holidayInfo.badge }}
                </span>
              </div>
              <div class="week-col-events">
                <div
                  v-for="ev in day.events"
                  :key="ev.id"
                  class="week-event-chip"
                  :class="[`priority-${ev.priority || 'medium'}`, { completed: ev.completed }]"
                >
                  <span class="ev-time" v-if="ev.time">{{ ev.time }}</span>
                  <span class="ev-text">{{ ev.title }}</span>
                </div>
                <div v-if="day.events.length === 0" class="empty-week-col">无日程</div>
              </div>
            </div>
          </div>
        </div>

        <!-- 3. Month View -->
        <div v-else-if="calendarMode === 'month'" class="month-view-wrapper animate-fade-in">
          <!-- Month Holiday & Compensate Summary Bar -->
          <div class="holiday-summary-bar" v-if="currentMonthSummary.list.length > 0">
            <span class="summary-chip holiday" v-if="currentMonthSummary.holidayDays > 0">
              <Sun :size="13" /> 本月法定放假 {{ currentMonthSummary.holidayDays }} 天
            </span>
            <span class="summary-chip compensate" v-if="currentMonthSummary.compensateDays > 0">
              <Briefcase :size="13" /> 周末调休补班 {{ currentMonthSummary.compensateDays }} 天
            </span>
          </div>

          <!-- Weekdays Header Grid -->
          <div class="weekdays-grid">
            <div v-for="(day, idx) in weekDays" :key="idx" class="weekday-cell" :class="{ weekend: idx === 5 || idx === 6 }">
              {{ day }}
            </div>
          </div>

          <!-- 6x7 Days Calendar Grid -->
          <div class="days-grid">
            <div
              v-for="(cell, index) in calendarCells"
              :key="index"
              class="day-cell"
              :class="{
                'other-month': !cell.isCurrentMonth,
                'is-today': cell.isToday,
                'is-selected': cell.isSameDate(selectedDate),
                'is-holiday': cell.holidayInfo?.isHoliday,
                'is-compensate': cell.holidayInfo?.isCompensate
              }"
              @click="selectDate(cell.date)"
            >
              <div class="day-number-row">
                <span class="day-number">{{ cell.date.getDate() }}</span>
                <span v-if="cell.holidayInfo?.badge" class="holiday-badge" :class="cell.holidayInfo.isHoliday ? 'holiday' : 'compensate'">
                  {{ cell.holidayInfo.badge }}
                </span>
              </div>

              <!-- Holiday Label or Lunar Text Small Subtitle -->
              <div
                class="cell-holiday-label"
                :class="{
                  'is-festive': cell.holidayInfo?.isHoliday,
                  'is-compensate': cell.holidayInfo?.isCompensate,
                  'is-solar-term': cell.isSolarTerm
                }"
              >
                {{ cell.holidayInfo?.label ? cell.holidayInfo.label : cell.lunarText }}
              </div>

              <!-- Event Indicators Dots -->
              <div class="cell-events-dots" v-if="cell.eventsCount > 0">
                <span class="event-dot" v-for="n in Math.min(3, cell.eventsCount)" :key="n"></span>
                <span v-if="cell.eventsCount > 3" class="more-dots">+{{ cell.eventsCount - 3 }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 4. Year View -->
        <div v-else-if="calendarMode === 'year'" class="year-view-wrapper animate-fade-in">
          <div class="year-months-grid">
            <div
              v-for="m in yearMonthsList"
              :key="m.monthIndex"
              class="mini-month-card"
              @click="selectMonthInYear(m.monthIndex)"
            >
              <div class="mini-month-header">{{ m.monthName }}</div>
              <div class="mini-days-grid">
                <div
                  v-for="(cell, cIdx) in m.cells"
                  :key="cIdx"
                  class="mini-day-cell"
                  :class="{ 'other-m': !cell.isCurrentMonth, 'is-today': cell.isToday, 'is-holiday': cell.holidayInfo?.isHoliday }"
                >
                  {{ cell.dayNum }}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Bottom Section: Selected Date Schedule & Todo List -->
      <div class="calendar-schedule-section">
        <div class="pane-header">
          <div class="header-title">
            <Clock :size="18" class="icon-primary" />
            <span>{{ formattedSelectedDate }} 待办日程 (农历 {{ selectedLunarInfo.fullText }})</span>
          </div>
          <button class="btn btn-sm btn-primary" @click="openQuickAdd">
            <Plus :size="14" /> 记一笔
          </button>
        </div>

        <!-- Selected Date Info Summary Banner -->
        <div class="selected-date-card">
          <div class="date-big-num">{{ selectedDate.getDate() }}</div>
          <div class="date-details">
            <div class="full-date-str">{{ formattedFullDate }} 星期{{ weekDayLabel(selectedDate.getDay()) }}</div>
            <div class="lunar-detail-str">农历 {{ selectedLunarInfo.fullText }}</div>
            <div class="holiday-status-row" v-if="selectedHolidayInfo">
              <span class="pill-badge" :class="selectedHolidayInfo.isHoliday ? 'holiday' : selectedHolidayInfo.isCompensate ? 'compensate' : 'normal'">
                {{ selectedHolidayInfo.badge ? selectedHolidayInfo.badge : '节' }} {{ selectedHolidayInfo.label }}
              </span>
              <span v-if="selectedHolidayInfo.isCompensate" class="compensate-tip">（工作日调休补班）</span>
              <span v-else-if="selectedHolidayInfo.isHoliday" class="compensate-tip holiday">（法定休假日）</span>
            </div>
          </div>
        </div>

        <!-- Quick Add Event Form -->
        <div v-if="showQuickAdd" class="quick-add-box animate-fade-in">
          <div class="quick-add-header">
            <span class="quick-add-title-text"><CalendarPlus :size="14" /> 新增日程记录与提醒</span>
            <button class="icon-btn-close-sm" @click="showQuickAdd = false" title="关闭"><X :size="12" /></button>
          </div>

          <div class="form-group-sm">
            <label class="form-label-sm">记录名称 *</label>
            <input
              type="text"
              v-model="newEventTitle"
              class="text-input input-sm"
              placeholder="如: 部门周例会 / 提交项目报告..."
              @keyup.enter="saveQuickEvent"
            />
          </div>

          <div class="form-group-sm">
            <div class="label-with-presets">
              <label class="form-label-sm">记录执行时间</label>
              <div class="quick-time-chips">
                <button type="button" class="chip-btn" @click="newEventTime = '09:00'">09:00</button>
                <button type="button" class="chip-btn" @click="newEventTime = '12:00'">12:00</button>
                <button type="button" class="chip-btn" @click="newEventTime = '15:00'">15:00</button>
                <button type="button" class="chip-btn" @click="newEventTime = '18:00'">18:00</button>
              </div>
            </div>
            <input
              type="time"
              v-model="newEventTime"
              class="text-input input-sm time-input-custom"
            />
          </div>

          <div class="form-group-sm">
            <div class="reminder-setting-row">
              <label class="checkbox-option-sm">
                <input type="checkbox" v-model="newEventEnableReminder" />
                <span>开启定时提醒</span>
              </label>

              <select
                v-if="newEventEnableReminder"
                v-model="newEventRemindOffset"
                class="select-input-sm"
              >
                <option value="0">准时提醒 ({{ newEventTime || '09:00' }})</option>
                <option value="10">提前 10 分钟提醒</option>
                <option value="30">提前 30 分钟提醒</option>
                <option value="60">提前 1 小时提醒</option>
              </select>
            </div>
          </div>

          <div class="form-row-sm">
            <div class="form-group-sm flex-1">
              <label class="form-label-sm">分类</label>
              <input
                type="text"
                v-model="newEventCategory"
                class="text-input input-sm"
                placeholder="如: 会议 / 个人"
              />
            </div>

            <div class="form-group-sm flex-1">
              <label class="form-label-sm">优先级</label>
              <select v-model="newEventPriority" class="select-input-sm">
                <option value="high">高优 (High)</option>
                <option value="medium">中优 (Medium)</option>
                <option value="low">低优 (Low)</option>
              </select>
            </div>
          </div>

          <div class="quick-add-actions">
            <button class="btn btn-sm btn-outline" @click="showQuickAdd = false">取消</button>
            <button class="btn btn-sm btn-primary" @click="saveQuickEvent">
              <Check :size="13" /> 保存日程记录
            </button>
          </div>
        </div>

        <!-- Schedule Items List -->
        <div class="schedule-list-scroll">
          <div v-if="selectedDayEvents.length === 0" class="empty-schedule-state">
            <div class="empty-icon"><CalendarIcon :size="36" :stroke-width="1.5" /></div>
            <p class="empty-text">该日期暂无安排，点击右上角 "记一笔" 快捷创建任务提醒吧！</p>
          </div>

          <div v-else class="schedule-items-stack">
            <div
              v-for="ev in selectedDayEvents"
              :key="ev.id"
              class="schedule-item-row"
              :class="{ completed: ev.completed }"
            >
              <div class="item-icon">
                <CheckSquare v-if="ev.type === 'todo'" :size="16" class="icon-todo" />
                <Bell v-else :size="16" class="icon-alarm" />
              </div>

              <div class="item-body">
                <div class="item-title" :class="{ strike: ev.completed }">{{ ev.title }}</div>
                <div class="item-meta">
                  <span class="tag tag-time" v-if="ev.time"><Clock :size="10" /> {{ ev.time }}</span>
                  <span class="tag tag-cat" v-if="ev.category"><Folder :size="10" /> {{ ev.category }}</span>
                </div>
              </div>

              <button class="icon-btn delete-btn-sm" @click.stop="deleteCalendarEvent(ev)" title="删除日程任务">
                <Trash2 :size="14" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import {
  Calendar as CalendarIcon, ChevronLeft, ChevronRight,
  Clock, Plus, CheckSquare, Bell, Trash2, X, Check,
  CalendarCheck, Sun, Briefcase, CalendarPlus, Folder
} from 'lucide-vue-next'
import type { Todo } from '../../types'
import { getLunar, type LunarResult } from '../../utils/lunar'

const props = defineProps<{
  todos?: Todo[]
}>()

const emit = defineEmits<{
  (e: 'add-todo', payload: any): void
  (e: 'delete-todo', id: number): void
}>()

const weekDays = ['一', '二', '三', '四', '五', '六', '日']

const today = new Date()
const currentYear = ref(today.getFullYear())
const currentMonth = ref(today.getMonth()) // 0 - 11
const selectedDate = ref<Date>(new Date(today.getFullYear(), today.getMonth(), today.getDate()))

const showQuickAdd = ref(false)
const newEventTitle = ref('')
const newEventTime = ref('09:00')
const newEventCategory = ref('日历日程')
const newEventPriority = ref<'high' | 'medium' | 'low'>('medium')
const newEventEnableReminder = ref(true)
const newEventRemindOffset = ref('0')

async function deleteCalendarEvent(ev: { id: string | number; title: string }) {
  const targetId = Number(ev.id)
  if (!isNaN(targetId)) {
    emit('delete-todo', targetId)
  }
}

interface HolidayInfo {
  badge?: string
  isHoliday?: boolean
  isCompensate?: boolean
  label: string
}

// 常见固定公历节日与纪念日
const fixedHolidays: Record<string, string> = {
  '01-01': '元旦',
  '02-14': '情人节',
  '03-08': '妇女节',
  '03-12': '植树节',
  '04-01': '愚人节',
  '05-01': '劳动节',
  '05-04': '青年节',
  '06-01': '儿童节',
  '07-01': '建党节',
  '08-01': '建军节',
  '09-10': '教师节',
  '10-01': '国庆节',
  '10-24': '程序员节',
  '11-01': '万圣节',
  '11-11': '双十一',
  '12-24': '平安夜',
  '12-25': '圣诞节'
}

// 包含具体年份（如 2026年）法定放假/调休安排与传统重大农历节日
const specificYearHolidays: Record<string, HolidayInfo> = {
  // 元旦
  '2026-01-01': { badge: '休', isHoliday: true, label: '元旦节' },
  '2026-01-25': { badge: '班', isCompensate: true, label: '春节补班' },
  // 农历腊八 & 小年
  '2026-01-26': { label: '腊八节' },
  '2026-02-10': { label: '北方小年' },
  '2026-02-11': { label: '南方小年' },
  // 春节放假安排
  '2026-02-16': { badge: '休', isHoliday: true, label: '除夕' },
  '2026-02-17': { badge: '休', isHoliday: true, label: '春节' },
  '2026-02-18': { badge: '休', isHoliday: true, label: '初二' },
  '2026-02-19': { badge: '休', isHoliday: true, label: '初三' },
  '2026-02-20': { badge: '休', isHoliday: true, label: '初四' },
  '2026-02-21': { badge: '休', isHoliday: true, label: '初五' },
  '2026-02-22': { badge: '休', isHoliday: true, label: '初六' },
  '2026-02-28': { badge: '班', isCompensate: true, label: '调休补班' },
  '2026-03-03': { label: '元宵节' },
  '2026-03-20': { label: '龙抬头' },
  // 清明节
  '2026-04-05': { badge: '休', isHoliday: true, label: '清明节' },
  '2026-04-06': { badge: '休', isHoliday: true, label: '清明假期' },
  '2026-04-26': { badge: '班', isCompensate: true, label: '五一补班' },
  // 五一劳动节
  '2026-05-01': { badge: '休', isHoliday: true, label: '劳动节' },
  '2026-05-02': { badge: '休', isHoliday: true, label: '劳动节假期' },
  '2026-05-03': { badge: '休', isHoliday: true, label: '劳动节假期' },
  '2026-05-09': { badge: '班', isCompensate: true, label: '劳动节补班' },
  // 端午节
  '2026-06-19': { badge: '休', isHoliday: true, label: '端午节' },
  '2026-06-20': { badge: '休', isHoliday: true, label: '端午假期' },
  // 七夕节
  '2026-08-19': { label: '七夕节' },
  // 中秋节
  '2026-09-25': { badge: '休', isHoliday: true, label: '中秋节' },
  '2026-09-27': { badge: '班', isCompensate: true, label: '国庆调休补班' },
  // 国庆节
  '2026-10-01': { badge: '休', isHoliday: true, label: '国庆节' },
  '2026-10-02': { badge: '休', isHoliday: true, label: '国庆假期' },
  '2026-10-03': { badge: '休', isHoliday: true, label: '国庆假期' },
  '2026-10-04': { badge: '休', isHoliday: true, label: '国庆假期' },
  '2026-10-05': { badge: '休', isHoliday: true, label: '国庆假期' },
  '2026-10-10': { badge: '班', isCompensate: true, label: '国庆调休补班' },
  '2026-10-18': { label: '重阳节' }
}

function formatDateKey(d: Date): string {
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

function getHolidayInfo(d: Date): HolidayInfo | undefined {
  const fullKey = formatDateKey(d)
  if (specificYearHolidays[fullKey]) {
    return specificYearHolidays[fullKey]
  }

  const monthDayKey = `${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
  if (fixedHolidays[monthDayKey]) {
    return { label: fixedHolidays[monthDayKey] }
  }

  return undefined
}

function isSameDate(d1: Date, d2: Date): boolean {
  return d1.getFullYear() === d2.getFullYear() &&
    d1.getMonth() === d2.getMonth() &&
    d1.getDate() === d2.getDate()
}

const isCurrentMonthToday = computed(() => {
  return today.getFullYear() === currentYear.value && today.getMonth() === currentMonth.value
})

const formattedSelectedDate = computed(() => {
  return `${selectedDate.value.getMonth() + 1}月${selectedDate.value.getDate()}日`
})

const formattedFullDate = computed(() => {
  return `${selectedDate.value.getFullYear()}年${selectedDate.value.getMonth() + 1}月${selectedDate.value.getDate()}日`
})

const selectedHolidayInfo = computed(() => {
  return getHolidayInfo(selectedDate.value)
})

const currentMonthSummary = computed(() => {
  const year = currentYear.value
  const month = currentMonth.value
  let holidayDays = 0
  let compensateDays = 0
  const list: { dateStr: string; label: string; badge?: string; isHoliday?: boolean; isCompensate?: boolean }[] = []

  const daysInMonth = new Date(year, month + 1, 0).getDate()
  for (let d = 1; d <= daysInMonth; d++) {
    const dateObj = new Date(year, month, d)
    const info = getHolidayInfo(dateObj)
    if (info?.badge) {
      if (info.isHoliday) holidayDays++
      if (info.isCompensate) compensateDays++
      list.push({
        dateStr: `${month + 1}月${d}日`,
        label: info.label,
        badge: info.badge,
        isHoliday: info.isHoliday,
        isCompensate: info.isCompensate
      })
    }
  }

  return { holidayDays, compensateDays, list }
})

function weekDayLabel(dayIdx: number): string {
  const map: Record<number, string> = { 1: '一', 2: '二', 3: '三', 4: '四', 5: '五', 6: '六', 0: '日' }
  return map[dayIdx] || '日'
}

// Compute 6x7 Calendar Cells
interface CalendarCell {
  date: Date
  isCurrentMonth: boolean
  isToday: boolean
  isSameDate: (target: Date) => boolean
  eventsCount: number
  holidayInfo?: HolidayInfo
  lunarInfo: LunarResult
  lunarText: string
  isSolarTerm: boolean
}

const calendarCells = computed<CalendarCell[]>(() => {
  const cells: CalendarCell[] = []
  const year = currentYear.value
  const month = currentMonth.value

  const firstDay = new Date(year, month, 1)
  const dayOfWeek = firstDay.getDay() // 0 (Sun) - 6 (Sat)
  // Calculate offset to start from Monday (0: Mon, 1: Tue, ..., 6: Sun)
  const startOffset = (dayOfWeek + 6) % 7

  // Start date of the 6x7 grid (can be in previous month)
  const startDate = new Date(year, month, 1 - startOffset)

  // Generate 42 cells (6 rows * 7 columns)
  for (let i = 0; i < 42; i++) {
    const d = new Date(startDate.getFullYear(), startDate.getMonth(), startDate.getDate() + i)
    const isCurrentMonth = d.getMonth() === month
    cells.push(createCellObj(d, isCurrentMonth))
  }

  return cells
})

function getEventsForDate(d: Date) {
  const key = formatDateKey(d)
  const list: {
    id: string | number;
    title: string;
    time?: string;
    category?: string;
    priority?: 'high' | 'medium' | 'low';
    completed?: boolean;
    type: 'todo' | 'alarm';
    hasExactTime: boolean;
    hourNum?: number;
  }[] = []

  if (props.todos) {
    props.todos.forEach(t => {
      const rawDateStr = (t.remind_at && t.remind_at.trim()) ? t.remind_at.trim() : (t.created_at || '')
      if (!rawDateStr) return

      const datePart = rawDateStr.split(' ')[0].split('T')[0]
      const parts = datePart.split(/[-/]/)

      if (parts.length >= 3) {
        const y = parts[0]
        const m = String(parseInt(parts[1], 10)).padStart(2, '0')
        const dayNum = String(parseInt(parts[2], 10)).padStart(2, '0')
        const normalizedKey = `${y}-${m}-${dayNum}`

        if (normalizedKey === key) {
          let timeStr = ''
          let hasExactTime = false
          let hourNum: number | undefined = undefined

          if (t.remind_at) {
            let tPart = ''
            if (t.remind_at.includes(' ')) {
              tPart = t.remind_at.split(' ')[1] || ''
            } else if (t.remind_at.includes('T')) {
              tPart = t.remind_at.split('T')[1] || ''
            }
            if (tPart && tPart.length >= 2) {
              const parsedH = parseInt(tPart.substring(0, 2), 10)
              if (!isNaN(parsedH) && parsedH >= 0 && parsedH < 24) {
                hourNum = parsedH
                hasExactTime = true
                timeStr = tPart.substring(0, 5)
              }
            }
          }

          list.push({
            id: t.id,
            title: t.title,
            time: timeStr || (t.remind_at ? '全天' : '待办'),
            category: t.category || '待办',
            priority: t.priority || 'medium',
            completed: t.completed,
            type: 'todo',
            hasExactTime,
            hourNum
          })
        }
      }
    })
  }

  return list
}

function createCellObj(d: Date, isCurrentMonth: boolean): CalendarCell {
  const evs = getEventsForDate(d)
  const lunar = getLunar(d)
  return {
    date: d,
    isCurrentMonth,
    isToday: isSameDate(d, today),
    isSameDate: (target: Date) => isSameDate(d, target),
    eventsCount: evs.length,
    holidayInfo: getHolidayInfo(d),
    lunarInfo: lunar,
    lunarText: lunar.displayText,
    isSolarTerm: !!lunar.solarTerm
  }
}

const selectedLunarInfo = computed(() => {
  return getLunar(selectedDate.value)
})

const selectedDayEvents = computed(() => {
  return getEventsForDate(selectedDate.value)
})

type CalendarMode = 'day' | 'week' | 'month' | 'year'
const calendarMode = ref<CalendarMode>('month')

const currentWeekDays = computed(() => {
  const curr = new Date(selectedDate.value)
  const day = curr.getDay()
  const diffToMon = (day + 6) % 7
  const monday = new Date(curr.getFullYear(), curr.getMonth(), curr.getDate() - diffToMon)

  const list: { date: Date; dateStr: string; weekLabel: string; isSelected: boolean; isToday: boolean; events: any[]; holidayInfo?: HolidayInfo }[] = []
  for (let i = 0; i < 7; i++) {
    const d = new Date(monday.getFullYear(), monday.getMonth(), monday.getDate() + i)
    list.push({
      date: d,
      dateStr: `${d.getMonth() + 1}.${String(d.getDate()).padStart(2, '0')}`,
      weekLabel: weekDays[i],
      isSelected: isSameDate(d, selectedDate.value),
      isToday: isSameDate(d, today),
      events: getEventsForDate(d),
      holidayInfo: getHolidayInfo(d)
    })
  }
  return list
})

const dayEventsSummary = computed(() => {
  return getEventsForDate(selectedDate.value)
})

const dayTimeSlots = computed(() => {
  const events = dayEventsSummary.value.filter(e => e.hasExactTime)
  const slots: { hour: number; label: string; events: any[] }[] = []

  for (let h = 0; h < 24; h++) {
    const hourStr = String(h).padStart(2, '0')
    const matchedEvents = events.filter(e => e.hourNum === h)
    slots.push({
      hour: h,
      label: `${hourStr}:00`,
      events: matchedEvents
    })
  }
  return slots
})

const yearMonthsList = computed(() => {
  const year = currentYear.value
  const months = []
  for (let m = 0; m < 12; m++) {
    const firstDay = new Date(year, m, 1)
    const dayOfWeek = firstDay.getDay()
    const startOffset = (dayOfWeek + 6) % 7
    const startDate = new Date(year, m, 1 - startOffset)

    const cells = []
    for (let i = 0; i < 42; i++) {
      const d = new Date(startDate.getFullYear(), startDate.getMonth(), startDate.getDate() + i)
      cells.push({
        date: d,
        dayNum: d.getDate(),
        isCurrentMonth: d.getMonth() === m,
        isToday: isSameDate(d, today),
        isSelected: isSameDate(d, selectedDate.value),
        holidayInfo: getHolidayInfo(d)
      })
    }
    months.push({
      monthIndex: m,
      monthName: `${m + 1} 月`,
      cells
    })
  }
  return months
})

function prevMonth() {
  if (currentMonth.value === 0) {
    currentMonth.value = 11
    currentYear.value--
  } else {
    currentMonth.value--
  }
}

function nextMonth() {
  if (currentMonth.value === 11) {
    currentMonth.value = 0
    currentYear.value++
  } else {
    currentMonth.value++
  }
}

function prevPeriod() {
  if (calendarMode.value === 'day') {
    const d = new Date(selectedDate.value)
    d.setDate(d.getDate() - 1)
    selectedDate.value = d
    currentYear.value = d.getFullYear()
    currentMonth.value = d.getMonth()
  } else if (calendarMode.value === 'week') {
    const d = new Date(selectedDate.value)
    d.setDate(d.getDate() - 7)
    selectedDate.value = d
    currentYear.value = d.getFullYear()
    currentMonth.value = d.getMonth()
  } else if (calendarMode.value === 'month') {
    prevMonth()
  } else if (calendarMode.value === 'year') {
    currentYear.value--
  }
}

function nextPeriod() {
  if (calendarMode.value === 'day') {
    const d = new Date(selectedDate.value)
    d.setDate(d.getDate() + 1)
    selectedDate.value = d
    currentYear.value = d.getFullYear()
    currentMonth.value = d.getMonth()
  } else if (calendarMode.value === 'week') {
    const d = new Date(selectedDate.value)
    d.setDate(d.getDate() + 7)
    selectedDate.value = d
    currentYear.value = d.getFullYear()
    currentMonth.value = d.getMonth()
  } else if (calendarMode.value === 'month') {
    nextMonth()
  } else if (calendarMode.value === 'year') {
    currentYear.value++
  }
}

function selectMonthInYear(mIndex: number) {
  currentMonth.value = mIndex
  calendarMode.value = 'month'
}

function goToday() {
  currentYear.value = today.getFullYear()
  currentMonth.value = today.getMonth()
  selectedDate.value = new Date(today.getFullYear(), today.getMonth(), today.getDate())
}

function selectDate(d: Date) {
  selectedDate.value = d
  currentYear.value = d.getFullYear()
  currentMonth.value = d.getMonth()
  showQuickAdd.value = false
}

function openQuickAdd() {
  showQuickAdd.value = true
  newEventTitle.value = ''
  newEventTime.value = '09:00'
  newEventCategory.value = '日历日程'
  newEventPriority.value = 'medium'
  newEventEnableReminder.value = true
  newEventRemindOffset.value = '0'
}

function saveQuickEvent() {
  if (!newEventTitle.value.trim()) return

  const dateKey = formatDateKey(selectedDate.value)
  const timePart = newEventTime.value || '09:00'
  const fullDateStr = `${dateKey} ${timePart}:00`

  let remindAtStr: string | null = fullDateStr
  if (newEventEnableReminder.value) {
    if (newEventRemindOffset.value !== '0') {
      const offsetMin = parseInt(newEventRemindOffset.value, 10) || 0
      const [h, m] = timePart.split(':').map(Number)
      const eventDate = new Date(selectedDate.value.getFullYear(), selectedDate.value.getMonth(), selectedDate.value.getDate(), h, m)
      eventDate.setMinutes(eventDate.getMinutes() - offsetMin)

      const ry = eventDate.getFullYear()
      const rm = String(eventDate.getMonth() + 1).padStart(2, '0')
      const rd = String(eventDate.getDate()).padStart(2, '0')
      const rh = String(eventDate.getHours()).padStart(2, '0')
      const rmin = String(eventDate.getMinutes()).padStart(2, '0')
      remindAtStr = `${ry}-${rm}-${rd} ${rh}:${rmin}:00`
    }
  } else {
    remindAtStr = null
  }

  emit('add-todo', {
    title: newEventTitle.value.trim(),
    dateStr: fullDateStr,
    remindAt: remindAtStr,
    priority: newEventPriority.value,
    category: newEventCategory.value.trim() || '日历日程'
  })

  newEventTitle.value = ''
  showQuickAdd.value = false
}
</script>

<style scoped>
.calendar-view-container {
  display: flex;
  justify-content: center;
  align-items: flex-start;
  height: 100%;
  width: 100%;
  padding: 20px 24px;
  box-sizing: border-box;
  overflow-y: auto;
}

.calendar-single-workspace {
  display: flex;
  flex-direction: column;
  gap: 28px;
  width: 100%;
  max-width: 960px;
  margin: 0 auto;
}

.calendar-main-section {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.calendar-schedule-section {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 16px;
  border-top: 1px dashed var(--border-color);
  padding-top: 24px;
}

.calendar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-bottom: 10px;
  border-bottom: 1px dashed var(--border-color);
}

.month-display {
  display: flex;
  align-items: center;
  gap: 8px;
}

.year-month-text {
  font-size: 18px;
  font-weight: 800;
  color: var(--text-main);
  font-family: 'Outfit', 'Inter', sans-serif;
}

.today-badge {
  font-size: 11px;
  font-weight: 700;
  background-color: rgba(49, 130, 206, 0.12);
  color: var(--primary);
  padding: 2px 8px;
  border-radius: 10px;
}

.header-actions {
  display: flex;
  gap: 6px;
}

/* Month Holiday & Compensate Summary Bar */
.holiday-summary-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  background-color: var(--bg-surface);
  border-radius: var(--radius-sm);
  border: 1px solid var(--border-color);
  font-size: 11px;
}

.summary-chip {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 8px;
  border-radius: 10px;
  font-weight: 600;
}

.summary-chip.holiday {
  background-color: rgba(229, 62, 62, 0.12);
  color: #E53E3E;
}

.summary-chip.compensate {
  background-color: rgba(221, 107, 32, 0.12);
  color: #DD6B20;
}

.weekdays-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  text-align: center;
  font-size: 12px;
  font-weight: 700;
  color: var(--text-muted);
  padding: 6px 0;
  border-bottom: 1px solid var(--border-color);
}

.weekday-cell.weekend {
  color: #DD6B20;
}

.days-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  grid-template-rows: repeat(6, minmax(50px, 1fr));
  gap: 4px;
  padding-top: 4px;
}

.day-cell {
  position: relative;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  min-height: 52px;
  padding: 4px 6px;
  border-radius: 8px;
  border: 1px solid transparent;
  cursor: pointer;
  transition: all 0.2s ease;
  background-color: transparent;
}

.day-cell.is-holiday {
  background-color: rgba(229, 62, 62, 0.04);
}

.day-cell.is-compensate {
  background-color: rgba(221, 107, 32, 0.06);
}

.day-cell:hover {
  background-color: var(--bg-surface);
}

.day-cell.other-month {
  opacity: 0.35;
}

.day-cell.is-today {
  border-color: var(--primary);
  background-color: rgba(49, 130, 206, 0.05);
}

.day-cell.is-selected {
  background-color: var(--bg-surface);
  border-color: var(--primary);
  box-shadow: 0 0 0 2px rgba(49, 130, 206, 0.25);
}

.day-number-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.day-number {
  font-size: 14px;
  font-weight: 700;
  color: var(--text-main);
}

.holiday-badge {
  font-size: 10px;
  font-weight: 800;
  padding: 1px 4px;
  border-radius: 4px;
  line-height: 1;
}

.holiday-badge.holiday {
  background-color: rgba(229, 62, 62, 0.15);
  color: #E53E3E;
}

.holiday-badge.compensate {
  background-color: rgba(221, 107, 32, 0.15);
  color: #DD6B20;
}

.cell-holiday-label {
  font-size: 10px;
  font-weight: 500;
  color: var(--text-muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin: 1px 0;
  line-height: 1.2;
}

.cell-holiday-label.is-solar-term {
  color: var(--primary);
  font-weight: 700;
}

.cell-holiday-label.is-festive {
  color: #E53E3E;
  font-weight: 700;
}

.cell-holiday-label.is-compensate {
  color: #DD6B20;
  font-weight: 700;
}

.cell-events-dots {
  display: flex;
  align-items: center;
  gap: 3px;
}

.event-dot {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background-color: var(--primary);
}

.more-dots {
  font-size: 9px;
  color: var(--text-muted);
}

/* Right Pane Schedule Styles */
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

.icon-primary {
  color: var(--primary);
}

.selected-date-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  background-color: var(--bg-surface);
  border: 1px solid var(--border-color);
  border-radius: 12px;
}

.date-big-num {
  font-size: 42px;
  font-weight: 900;
  color: var(--primary);
  font-family: 'Outfit', 'Inter', monospace;
  line-height: 1;
}

.date-details {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.full-date-str {
  font-size: 14px;
  font-weight: 700;
  color: var(--text-main);
}

.lunar-detail-str {
  font-size: 12px;
  font-weight: 600;
  color: var(--primary);
}

.holiday-status-row {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  margin-top: 2px;
}

.pill-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 12px;
}

.pill-badge.holiday {
  background-color: rgba(229, 62, 62, 0.15);
  color: #E53E3E;
}

.pill-badge.compensate {
  background-color: rgba(221, 107, 32, 0.15);
  color: #DD6B20;
}

.pill-badge.normal {
  background-color: rgba(49, 130, 206, 0.12);
  color: var(--primary);
}

.compensate-tip {
  font-size: 11px;
  color: var(--text-muted);
  font-weight: 500;
}

.compensate-tip.holiday {
  color: #E53E3E;
}

.quick-add-box {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 12px;
  background-color: var(--bg-surface);
  border: 1px dashed var(--primary);
  border-radius: 8px;
}

.quick-add-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

.schedule-list-scroll {
  flex: 1;
  overflow-y: auto;
  padding-right: 4px;
}

.empty-schedule-state {
  text-align: center;
  padding: 40px 20px;
  color: var(--text-muted);
}

.empty-icon {
  font-size: 36px;
  margin-bottom: 8px;
}

.schedule-items-stack {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.schedule-item-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 14px;
  border-bottom: 1px solid var(--border-color);
  background-color: transparent;
  transition: background-color 0.2s;
}

.schedule-item-row:hover {
  background-color: var(--bg-surface);
}

.schedule-item-row.completed {
  opacity: 0.55;
}

.item-icon {
  display: flex;
  align-items: center;
}

.icon-todo {
  color: var(--primary);
}

.icon-alarm {
  color: #DD6B20;
}

.item-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.item-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-main);
}

.item-title.strike {
  text-decoration: line-through;
  color: var(--text-muted);
}

.item-meta {
  display: flex;
  gap: 8px;
  font-size: 11px;
}

.tag-time {
  color: var(--primary);
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 3px;
}

.tag-cat {
  color: var(--text-muted);
}

/* Header Segmented Tabs */
.header-center-tabs {
  display: flex;
  justify-content: center;
}

.mode-segmented {
  display: flex;
  align-items: center;
  background-color: var(--bg-surface);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  padding: 2px;
  gap: 2px;
}

.mode-tab {
  border: none;
  background: transparent;
  padding: 4px 10px;
  font-size: 12px;
  font-weight: 600;
  color: var(--text-muted);
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.mode-tab:hover {
  color: var(--text-main);
}

.mode-tab.active {
  background-color: var(--primary);
  color: #ffffff;
  font-weight: 700;
}

/* 1. Day View Timeline Styles */
.day-view-wrapper {
  flex: 1;
  border: 1px solid var(--border-color);
  border-radius: 12px;
  background-color: var(--bg-surface);
  max-height: 480px;
  overflow-y: auto;
}

.day-timeline-scroll {
  display: flex;
  flex-direction: column;
}

.time-slot-row {
  display: flex;
  align-items: flex-start;
  min-height: 44px;
  border-bottom: 1px dashed var(--border-color);
  padding: 6px 12px;
  gap: 12px;
}

.slot-time-label {
  width: 50px;
  font-size: 11px;
  font-weight: 700;
  color: var(--text-muted);
  font-family: monospace;
}

.slot-events-cell {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.slot-event-chip {
  background-color: rgba(49, 130, 206, 0.12);
  border-left: 3px solid var(--primary);
  border-radius: 4px;
  padding: 4px 8px;
  font-size: 12px;
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--text-main);
}

.slot-event-chip.completed {
  opacity: 0.5;
  text-decoration: line-through;
}

.ev-chip-time {
  font-weight: 700;
  color: var(--primary);
  font-size: 11px;
}

.empty-slot-hint {
  font-size: 11px;
  color: transparent;
}

/* 2. Week View Styles */
.week-view-wrapper {
  flex: 1;
}

.week-columns-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 8px;
  min-height: 420px;
}

.week-column {
  background-color: var(--bg-surface);
  border: 1px solid var(--border-color);
  border-radius: 10px;
  padding: 8px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.week-column:hover {
  border-color: var(--primary);
}

.week-column.is-selected {
  border-color: var(--primary);
  box-shadow: 0 0 0 2px rgba(49, 130, 206, 0.2);
}

.week-column.is-today {
  background-color: rgba(49, 130, 206, 0.04);
}

.week-col-header {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  padding-bottom: 6px;
  border-bottom: 1px solid var(--border-color);
}

.col-week-label {
  font-size: 11px;
  font-weight: 700;
  color: var(--text-muted);
}

.col-date-num {
  font-size: 13px;
  font-weight: 800;
  color: var(--text-main);
}

.week-col-body {
  display: flex;
  flex-direction: column;
  gap: 6px;
  flex: 1;
}

.week-event-card {
  position: relative;
  border-radius: 8px;
  padding: 8px 10px;
  font-size: 11px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.05);
}

.week-event-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.12);
}

.week-event-card.completed {
  opacity: 0.5;
  text-decoration: line-through;
}

/* Priority Background Styling for Cards */
.week-event-card.priority-high, .slot-event-chip.priority-high, .allday-event-chip.priority-high {
  background: linear-gradient(135deg, rgba(254, 215, 215, 0.8) 0%, rgba(254, 178, 178, 0.5) 100%);
  border: 1px solid #FEB2B2;
  border-left: 4px solid #E53E3E;
  color: #742A2A;
}

.week-event-card.priority-medium, .slot-event-chip.priority-medium, .allday-event-chip.priority-medium {
  background: linear-gradient(135deg, rgba(235, 248, 255, 0.85) 0%, rgba(223, 225, 255, 0.6) 100%);
  border: 1px solid #BEE3F8;
  border-left: 4px solid #3182CE;
  color: #2B6CB0;
}

.week-event-card.priority-low, .slot-event-chip.priority-low, .allday-event-chip.priority-low {
  background: linear-gradient(135deg, rgba(240, 255, 244, 0.85) 0%, rgba(198, 246, 213, 0.6) 100%);
  border: 1px solid #C6F6D5;
  border-left: 4px solid #38A169;
  color: #22543D;
}

/* Dark Theme overrides for cards */
[data-theme="dark"] .week-event-card.priority-high,
[data-theme="dark"] .slot-event-chip.priority-high,
[data-theme="dark"] .allday-event-chip.priority-high {
  background: linear-gradient(135deg, rgba(155, 44, 44, 0.45) 0%, rgba(116, 42, 42, 0.35) 100%);
  border-color: #9B2C2C;
  border-left-color: #FC8181;
  color: #FEB2B2;
}

[data-theme="dark"] .week-event-card.priority-medium,
[data-theme="dark"] .slot-event-chip.priority-medium,
[data-theme="dark"] .allday-event-chip.priority-medium {
  background: linear-gradient(135deg, rgba(44, 82, 130, 0.45) 0%, rgba(67, 56, 202, 0.35) 100%);
  border-color: #2C5282;
  border-left-color: #63B3ED;
  color: #BEE3F8;
}

[data-theme="dark"] .week-event-card.priority-low,
[data-theme="dark"] .slot-event-chip.priority-low,
[data-theme="dark"] .allday-event-chip.priority-low {
  background: linear-gradient(135deg, rgba(34, 84, 61, 0.45) 0%, rgba(40, 116, 80, 0.35) 100%);
  border-color: #22543D;
  border-left-color: #68D391;
  color: #C6F6D5;
}

/* Nord Theme overrides */
[data-theme="nord"] .week-event-card.priority-high,
[data-theme="nord"] .slot-event-chip.priority-high,
[data-theme="nord"] .allday-event-chip.priority-high {
  background: linear-gradient(135deg, rgba(191, 97, 106, 0.35) 0%, rgba(191, 97, 106, 0.25) 100%);
  border-color: #BF616A;
  border-left-color: #BF616A;
  color: #E5E9F0;
}

[data-theme="nord"] .week-event-card.priority-medium,
[data-theme="nord"] .slot-event-chip.priority-medium,
[data-theme="nord"] .allday-event-chip.priority-medium {
  background: linear-gradient(135deg, rgba(136, 192, 208, 0.35) 0%, rgba(94, 129, 172, 0.25) 100%);
  border-color: #88C0D0;
  border-left-color: #88C0D0;
  color: #E5E9F0;
}

[data-theme="nord"] .week-event-card.priority-low,
[data-theme="nord"] .slot-event-chip.priority-low,
[data-theme="nord"] .allday-event-chip.priority-low {
  background: linear-gradient(135deg, rgba(163, 190, 140, 0.35) 0%, rgba(163, 190, 140, 0.25) 100%);
  border-color: #A3BE8C;
  border-left-color: #A3BE8C;
  color: #E5E9F0;
}

.ev-footer-tag {
  display: flex;
  justify-content: flex-end;
  margin-top: 2px;
}

.priority-badge {
  font-size: 9px;
  font-weight: 700;
  padding: 1px 5px;
  border-radius: 4px;
  text-transform: uppercase;
}

.priority-badge.high {
  background-color: rgba(229, 62, 62, 0.2);
  color: #E53E3E;
}

.priority-badge.medium {
  background-color: rgba(49, 130, 206, 0.2);
  color: #3182CE;
}

.priority-badge.low {
  background-color: rgba(56, 161, 105, 0.2);
  color: #38A169;
}

/* Day View Allday Section */
.day-allday-section {
  background-color: var(--bg-surface);
  border: 1px solid var(--border-color);
  border-radius: 10px;
  padding: 12px 16px;
  margin-bottom: 16px;
}

.allday-header {
  margin-bottom: 10px;
}

.allday-title {
  font-size: 13px;
  font-weight: 700;
  color: var(--text-main);
}

.allday-events-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 10px;
}

.allday-event-chip {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.chip-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 10px;
  font-weight: 700;
}

.chip-title {
  font-size: 12px;
  font-weight: 600;
}

.day-timeline-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.timeline-header-title {
  font-size: 13px;
  font-weight: 700;
  color: var(--text-muted);
}

.empty-week-col {
  font-size: 10px;
  color: var(--text-muted);
  text-align: center;
  margin-top: 10px;
  opacity: 0.5;
}

/* 4. Year View Styles */
.year-view-wrapper {
  flex: 1;
}

.year-months-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

.mini-month-card {
  background-color: var(--bg-surface);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.mini-month-card:hover {
  border-color: var(--primary);
  transform: translateY(-1px);
}

.mini-month-header {
  font-size: 12px;
  font-weight: 800;
  color: var(--primary);
  margin-bottom: 6px;
  text-align: center;
}

.mini-days-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 2px;
  text-align: center;
  font-size: 9px;
}

.mini-day-cell {
  padding: 2px 0;
  color: var(--text-main);
  border-radius: 2px;
}

.mini-day-cell.other-m {
  opacity: 0.2;
}

.mini-day-cell.is-today {
  background-color: var(--primary);
  color: #ffffff;
  font-weight: 700;
}

.mini-day-cell.is-holiday {
  color: #E53E3E;
  font-weight: 700;
}

/* Enhanced Quick Add Box Styling */
.quick-add-box {
  background-color: var(--bg-surface);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 14px 16px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 14px;
}

.quick-add-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 13px;
  font-weight: 700;
  color: var(--primary);
  padding-bottom: 6px;
  border-bottom: 1px solid var(--border-color);
}

.icon-btn-close-sm {
  background: transparent;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  padding: 2px;
  border-radius: 4px;
}

.icon-btn-close-sm:hover {
  background-color: var(--bg-app);
  color: var(--text-main);
}

.form-group-sm {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.form-row-sm {
  display: flex;
  gap: 10px;
}

.form-label-sm {
  font-size: 11.5px;
  font-weight: 600;
  color: var(--text-muted);
}

.input-sm, .select-input-sm {
  font-size: 12px;
  padding: 5px 8px;
  border-radius: 6px;
  border: 1px solid var(--border-color);
  background-color: var(--bg-app);
  color: var(--text-main);
  outline: none;
}

.label-with-presets {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.quick-time-chips {
  display: flex;
  gap: 4px;
}

.chip-btn {
  background-color: var(--bg-app);
  border: 1px solid var(--border-color);
  border-radius: 4px;
  font-size: 10px;
  padding: 2px 6px;
  cursor: pointer;
  color: var(--text-main);
}

.chip-btn:hover {
  border-color: var(--primary);
  color: var(--primary);
}

.time-input-custom {
  width: 100%;
}

.reminder-setting-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  background-color: var(--bg-app);
  padding: 6px 10px;
  border-radius: 6px;
  border: 1px solid var(--border-color);
}

.checkbox-option-sm {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11.5px;
  cursor: pointer;
  color: var(--text-main);
}

.week-ev-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 4px;
}

.ev-cat {
  font-size: 9.5px;
  color: var(--primary);
  background-color: rgba(49, 130, 206, 0.1);
  padding: 1px 4px;
  border-radius: 3px;
  white-space: nowrap;
}

.ev-chip-cat {
  font-size: 10px;
  color: var(--primary);
  margin-left: auto;
}
</style>

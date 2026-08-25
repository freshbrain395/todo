<template>
  <div
    class="app-layout"
    :class="[navPosition === 'left' ? 'layout-nav-left' : navPosition === 'desktop' ? 'layout-nav-desktop' : 'layout-nav-top']"
    :data-theme="theme"
  >
    <!-- 1. Header Bar with Navigation Tabs (Hidden in Desktop OS Mode) -->
    <header v-if="navPosition !== 'desktop'" class="header">
      <div class="header-left">
        <!-- Mobile Navigation Toggle Button (< 640px) -->
        <button
          class="mobile-nav-toggle-btn"
          @click="toggleMobileNavMenu"
          :title="showMobileNavMenu ? '关闭导航菜单' : '展开导航菜单'"
        >
          <X v-if="showMobileNavMenu" :size="18" />
          <Menu v-else :size="18" />
        </button>

        <h1 class="app-title"><ListTodo :size="20" /> Todo Agent</h1>
      </div>

      <!-- Center Navbar Navigation Tabs (Desktop & Tablet) -->
      <nav class="navbar-tabs">
        <button
          class="nav-tab-btn"
          :class="{ active: currentTab === 'calendar' }"
          @click="currentTab = 'calendar'"
          title="任务日历"
          data-tooltip="任务日历"
        >
          <Calendar :size="15" /> <span>任务日历</span>
        </button>

        <button
          class="nav-tab-btn"
          :class="{ active: currentTab === 'todos' }"
          @click="currentTab = 'todos'"
          title="待办事项"
          data-tooltip="待办事项"
        >
          <CheckSquare :size="15" /> <span>待办事项</span>
        </button>

        <button
          class="nav-tab-btn"
          :class="{ active: currentTab === 'pomodoro' }"
          @click="currentTab = 'pomodoro'"
          title="番茄时钟"
          data-tooltip="番茄时钟"
        >
          <Flame :size="15" /> <span>番茄时钟</span>
        </button>

        <button
          class="nav-tab-btn"
          :class="{ active: currentTab === 'countdown' }"
          @click="currentTab = 'countdown'"
          title="倒计时"
          data-tooltip="倒计时"
        >
          <Hourglass :size="15" /> <span>倒计时</span>
        </button>

        <button
          class="nav-tab-btn"
          :class="{ active: currentTab === 'alarm' }"
          @click="currentTab = 'alarm'"
          title="闹钟"
          data-tooltip="闹钟"
        >
          <Bell :size="15" /> <span>闹钟</span>
        </button>

        <button
          class="nav-tab-btn"
          :class="{ active: currentTab === 'local-clock' }"
          @click="currentTab = 'local-clock'"
          title="本地时钟"
          data-tooltip="本地时钟"
        >
          <Clock :size="15" /> <span>本地时钟</span>
        </button>

        <button
          class="nav-tab-btn"
          :class="{ active: currentTab === 'settings' }"
          @click="currentTab = 'settings'"
          title="系统设置"
          data-tooltip="系统设置"
        >
          <Settings :size="15" /> <span>系统设置</span>
        </button>
      </nav>

      <!-- Mobile Dropdown Navigation Menu (< 640px) -->
      <div v-if="showMobileNavMenu" class="mobile-dropdown-menu animate-fade-in" @click.stop>
        <div class="mobile-nav-links">
          <button
            class="mobile-nav-item"
            :class="{ active: currentTab === 'calendar' }"
            @click="selectMobileTab('calendar')"
          >
            <Calendar :size="16" /> <span>任务日历</span>
          </button>
          <button
            class="mobile-nav-item"
            :class="{ active: currentTab === 'todos' }"
            @click="selectMobileTab('todos')"
          >
            <CheckSquare :size="16" /> <span>待办事项</span>
          </button>
          <button
            class="mobile-nav-item"
            :class="{ active: currentTab === 'pomodoro' }"
            @click="selectMobileTab('pomodoro')"
          >
            <Flame :size="16" /> <span>番茄时钟</span>
          </button>
          <button
            class="mobile-nav-item"
            :class="{ active: currentTab === 'countdown' }"
            @click="selectMobileTab('countdown')"
          >
            <Hourglass :size="16" /> <span>倒计时</span>
          </button>
          <button
            class="mobile-nav-item"
            :class="{ active: currentTab === 'alarm' }"
            @click="selectMobileTab('alarm')"
          >
            <Bell :size="16" /> <span>闹钟</span>
          </button>
          <button
            class="mobile-nav-item"
            :class="{ active: currentTab === 'local-clock' }"
            @click="selectMobileTab('local-clock')"
          >
            <Clock :size="16" /> <span>本地时钟</span>
          </button>
          <button
            class="mobile-nav-item"
            :class="{ active: currentTab === 'settings' }"
            @click="selectMobileTab('settings')"
          >
            <Settings :size="16" /> <span>系统设置</span>
          </button>
        </div>
      </div>
    </header>


    <!-- 2. Main Content Area -->
    <main class="main-content">
      <!-- Tab 0: Desktop View -->
      <template v-if="currentTab === 'desktop'">
        <DesktopView
          :todos="todos"
          :current-user="currentUser"
          @open-app="tab => currentTab = tab"
          @open-add-todo="openAddModal"
          @open-login="showAuthModal = true"
        />
      </template>

      <!-- Tab 1: Todos List View -->
      <template v-else-if="currentTab === 'todos'">
        <div class="pure-list-workspace">
          <!-- Filter & Search Toolbar (modeled after PomodoroTimer) -->
          <div class="toolbar">
            <div class="filter-group">
              <button
                class="filter-btn"
                :class="{ active: currentFilter === 'all' }"
                @click="setFilter('all')"
              >
                全部 ({{ todos.length }})
              </button>
              <button
                class="filter-btn"
                :class="{ active: currentFilter === 'pending' }"
                @click="setFilter('pending')"
              >
                未完成 ({{ pendingTodosCount }})
              </button>
              <button
                class="filter-btn"
                :class="{ active: currentFilter === 'completed' }"
                @click="setFilter('completed')"
              >
                已完成 ({{ completedTodosCount }})
              </button>
            </div>

            <div class="toolbar-right">
              <div class="search-box">
                <Search :size="14" class="search-icon" />
                <input
                  type="text"
                  v-model="searchKeyword"
                  placeholder="搜索待办事项..."
                  @input="loadTodos"
                />
              </div>

              <button class="btn btn-primary" @click="openAddModal">
                <Plus :size="14" /> 新建任务
              </button>
            </div>
          </div>

          <!-- Stats Summary Banner (matching PomodoroTimer layout) -->
          <div class="stats-banner-row">
            <div class="stats-pill">
              <CheckSquare :size="14" class="icon-primary" />
              <span>待完成 <strong>{{ pendingTodosCount }}</strong> 项</span>
            </div>
            <div class="stats-pill">
              <Check :size="14" class="icon-success" />
              <span>已完成 <strong>{{ completedTodosCount }}</strong> 项</span>
            </div>
            <div class="stats-pill">
              <Flame :size="14" class="icon-flame" />
              <span>高优先级 <strong>{{ highPriorityTodosCount }}</strong> 项</span>
            </div>
            <button
              v-if="completedTodosCount > 0"
              class="clear-stats-btn"
              @click="clearCompletedTodos"
              title="清理已完成的待办任务"
            >
              <Trash2 :size="12" /> 清理已完成
            </button>
          </div>

          <!-- Todo List Grid / Card View (matching Pomodoro list card structure) -->
          <div class="list-scroll-area">
            <div v-if="loading" class="empty-state">
              <div class="spinner"></div>
              <p>加载中...</p>
            </div>

            <div v-else-if="todos.length === 0" class="empty-state">
              <div class="empty-icon"><Inbox :size="42" :stroke-width="1.5" /></div>
              <p class="empty-text">暂无待办事项，点击右上角 "+ 新建任务" 或使用快捷创建吧！</p>
            </div>

            <div v-else class="items-grid">
              <div
                v-for="todo in todos"
                :key="todo.id"
                class="list-card-item animate-fade-in"
                :class="{
                  completed: todo.completed,
                  'prio-high': todo.priority === 'high',
                  'has-active-menu': activeMenuId && activeMenuId.endsWith('-' + todo.id)
                }"
              >
                <div class="card-left-indicator">
                  <div
                    class="mini-todo-icon"
                    :class="{ checked: todo.completed }"
                    @click="toggleStatus(todo)"
                    title="切换完成状态"
                  >
                    <Check v-if="todo.completed" :size="18" />
                    <Square v-else :size="18" />
                  </div>
                </div>

                <div class="card-body">
                  <!-- Row 1: Title Line -->
                  <div class="card-title-row">
                    <!-- Inline Direct Editable Title -->
                    <div v-if="editingId === todo.id" class="inline-edit-wrapper" @click.stop>
                      <input
                        ref="inlineInputRef"
                        type="text"
                        class="inline-edit-input"
                        v-model="inlineEditText"
                        @blur="saveInlineEdit(todo)"
                        @keydown.enter="saveInlineEdit(todo)"
                        @keydown.esc="cancelInlineEdit"
                        placeholder="任务标题..."
                      />
                    </div>
                    <span
                      v-else
                      class="card-title clickable-title"
                      :class="{ strike: todo.completed }"
                      @click="startInlineEdit(todo)"
                      title="点击直接修改标题"
                    >
                      {{ todo.title }}
                    </span>
                  </div>

                  <!-- Row 2: Interactive Metadata & Configuration Row (Hover/Click to edit) -->
                  <div class="card-meta-row">
                    <!-- 1. Priority Selector with Custom Rounded Dropdown (Hover to auto-expand) -->
                    <div
                      class="meta-item-config hover-expand"
                      @mouseenter="openMenuHover('prio-' + todo.id)"
                      @mouseleave="closeMenuHover()"
                      @click.stop="toggleMenu('prio-' + todo.id)"
                    >
                      <div class="interactive-pill prio-pill" :class="todo.priority" title="鼠标悬浮展开/修改优先级">
                        <span class="prio-dot"></span>
                        <span class="prio-text">{{ priorityLabel(todo.priority) }}</span>
                        <ChevronDown :size="10" class="pill-arrow" :class="{ rotated: activeMenuId === 'prio-' + todo.id }" />
                      </div>

                      <!-- Custom Rounded Popover Menu -->
                      <div v-if="activeMenuId === 'prio-' + todo.id" class="custom-dropdown-menu animate-fade-in" @click.stop>
                        <button
                          type="button"
                          class="dropdown-item"
                          :class="{ selected: todo.priority === 'high' }"
                          @click="selectPriority(todo, 'high')"
                        >
                          <span class="dot-prio red"></span>
                          <span class="item-name">🔴 高优先级</span>
                          <Check v-if="todo.priority === 'high'" :size="13" class="check-icon" />
                        </button>
                        <button
                          type="button"
                          class="dropdown-item"
                          :class="{ selected: todo.priority === 'medium' }"
                          @click="selectPriority(todo, 'medium')"
                        >
                          <span class="dot-prio yellow"></span>
                          <span class="item-name">🟡 中优先级</span>
                          <Check v-if="todo.priority === 'medium'" :size="13" class="check-icon" />
                        </button>
                        <button
                          type="button"
                          class="dropdown-item"
                          :class="{ selected: todo.priority === 'low' }"
                          @click="selectPriority(todo, 'low')"
                        >
                          <span class="dot-prio blue"></span>
                          <span class="item-name">🔵 低优先级</span>
                          <Check v-if="todo.priority === 'low'" :size="13" class="check-icon" />
                        </button>
                      </div>
                    </div>

                    <!-- 2. Category / Tag Selector with Custom Rounded Dropdown (Hover to auto-expand) -->
                    <div
                      class="meta-item-config hover-expand"
                      @mouseenter="openMenuHover('cat-' + todo.id)"
                      @mouseleave="closeMenuHover()"
                      @click.stop="toggleMenu('cat-' + todo.id)"
                    >
                      <div class="interactive-pill cat-pill" title="鼠标悬浮展开/修改标签分类">
                        <Folder :size="12" />
                        <span class="cat-text">{{ todo.category || '默认' }}</span>
                        <ChevronDown :size="10" class="pill-arrow" :class="{ rotated: activeMenuId === 'cat-' + todo.id }" />
                      </div>

                      <!-- Custom Rounded Popover Menu -->
                      <div v-if="activeMenuId === 'cat-' + todo.id" class="custom-dropdown-menu animate-fade-in" @click.stop>
                        <button
                          v-for="cat in ['工作', '学习', '生活', '常规']"
                          :key="cat"
                          type="button"
                          class="dropdown-item"
                          :class="{ selected: todo.category === cat }"
                          @click="selectCategory(todo, cat)"
                        >
                          <Folder :size="13" class="item-icon" />
                          <span class="item-name">{{ cat }}</span>
                          <Check v-if="todo.category === cat" :size="13" class="check-icon" />
                        </button>
                      </div>
                    </div>

                    <!-- 3. Reminder Switch & Modal Trigger -->
                    <div class="meta-item-config">
                      <div
                        class="interactive-pill reminder-pill"
                        :class="{ active: !!todo.remind_at }"
                        @click="openReminderModal(todo)"
                        title="点击配置提醒时间（支持12/24小时制与快捷设置）"
                      >
                        <Clock :size="12" />
                        <span v-if="todo.remind_at" class="reminder-text">{{ formatRemindDisplay(todo.remind_at) }}</span>
                        <span v-else class="reminder-text placeholder">设置提醒</span>
                        <button
                          v-if="todo.remind_at"
                          type="button"
                          class="btn-clear-reminder"
                          @click.stop="updateTodoReminder(todo, '')"
                          title="清除提醒"
                        >
                          <X :size="11" />
                        </button>
                      </div>
                    </div>

                  </div>
                </div>

                <div class="card-actions">
                  <button class="icon-btn-action delete" @click="deleteTodo(todo.id)" title="删除任务">
                    <Trash2 :size="14" />
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </template>

      <!-- Tab 2: Calendar View -->
      <template v-else-if="currentTab === 'calendar'">
        <CalendarView
          :todos="todos"
          @delete-todo="deleteTodo"
        />
      </template>

      <!-- Tab 4: Local Clock View -->
      <template v-else-if="currentTab === 'local-clock'">
        <LocalClockPage />
      </template>

      <!-- Tab 5: Countdown Timer View -->
      <template v-else-if="currentTab === 'countdown'">
        <AlarmCountdown mode="countdown" />
      </template>

      <!-- Tab 6: Alarm View -->
      <template v-else-if="currentTab === 'alarm'">
        <AlarmCountdown mode="alarm" />
      </template>

      <!-- Tab 7: Pomodoro Timer View -->
      <template v-else-if="currentTab === 'pomodoro'">
        <PomodoroTimer />
      </template>

      <!-- Tab 8: Settings View -->
      <template v-else-if="currentTab === 'settings'">
        <SettingsPage
          v-model:theme="theme"
          v-model:config="llmConfig"
          @update:navPosition="val => navPosition = val"
          @logout="handleLogout"
          @userChanged="loadTodos"
        />
      </template>
    </main>

    <!-- Floating Desktop Dock Bar (When in Desktop OS Layout Mode) -->
    <div v-if="navPosition === 'desktop'" class="desktop-dock-wrapper">
      <div class="desktop-dock-bar">
        <button
          class="dock-btn"
          :class="{ active: currentTab === 'desktop' }"
          @click="currentTab = 'desktop'"
          title="返回桌面"
        >
          <LayoutGrid :size="20" />
          <span class="dock-tooltip">桌面</span>
        </button>

        <div class="dock-divider"></div>

        <button
          class="dock-btn"
          :class="{ active: currentTab === 'calendar' }"
          @click="currentTab = 'calendar'"
          title="任务日历"
        >
          <Calendar :size="20" />
          <span class="dock-tooltip">任务日历</span>
        </button>

        <button
          class="dock-btn"
          :class="{ active: currentTab === 'todos' }"
          @click="currentTab = 'todos'"
          title="待办事项"
        >
          <CheckSquare :size="20" />
          <span class="dock-tooltip">待办事项</span>
        </button>

        <button
          class="dock-btn"
          :class="{ active: currentTab === 'pomodoro' }"
          @click="currentTab = 'pomodoro'"
          title="番茄时钟"
        >
          <Flame :size="20" />
          <span class="dock-tooltip">番茄时钟</span>
        </button>

        <button
          class="dock-btn"
          :class="{ active: currentTab === 'countdown' }"
          @click="currentTab = 'countdown'"
          title="倒计时"
        >
          <Hourglass :size="20" />
          <span class="dock-tooltip">倒计时</span>
        </button>

        <button
          class="dock-btn"
          :class="{ active: currentTab === 'alarm' }"
          @click="currentTab = 'alarm'"
          title="闹钟"
        >
          <Bell :size="20" />
          <span class="dock-tooltip">闹钟</span>
        </button>

        <button
          class="dock-btn"
          :class="{ active: currentTab === 'local-clock' }"
          @click="currentTab = 'local-clock'"
          title="本地时钟"
        >
          <Clock :size="20" />
          <span class="dock-tooltip">本地时钟</span>
        </button>

        <button
          class="dock-btn"
          :class="{ active: currentTab === 'settings' }"
          @click="currentTab = 'settings'"
          title="系统设置"
        >
          <Settings :size="20" />
          <span class="dock-tooltip">系统设置</span>
        </button>
      </div>
    </div>

    <!-- Modals -->
    <!-- Add / Edit Modal -->
    <div v-if="showAddEditModal" class="modal-backdrop" @click.self="showAddEditModal = false">
      <div class="modal-card animate-fade-in">
        <h2 class="modal-title">
          <Edit3 v-if="editingTodo" :size="18" />
          <Plus v-else :size="18" />
          <span>{{ editingTodo ? '编辑待办事项' : '添加新待办事项' }}</span>
        </h2>

        <div class="form-group">
          <label>任务标题 *</label>
          <input type="text" v-model="todoForm.title" placeholder="请输入任务标题..." />
        </div>

        <div class="form-row">
          <div class="form-group flex-1">
            <label>任务分类</label>
            <input type="text" v-model="todoForm.category" placeholder="如: 工作 / 生活 / 学习" />
          </div>

          <div class="form-group flex-1">
            <label>优先级</label>
            <select v-model="todoForm.priority">
              <option value="high">高优 (high)</option>
              <option value="medium">中优 (medium)</option>
              <option value="low">低优 (low)</option>
            </select>
          </div>
        </div>

        <div class="form-group">
          <label class="checkbox-label">
            <input type="checkbox" v-model="todoForm.enableReminder" />
            设置定时提醒时间
          </label>
          <div v-if="todoForm.enableReminder" class="modal-wheel-picker-wrap">
            <WheelDateTimePicker v-model="todoForm.remindAt" />
          </div>
        </div>

        <div class="modal-actions">
          <button class="btn" @click="showAddEditModal = false">取消</button>
          <button class="btn btn-primary" @click="saveTodoForm">保存</button>
        </div>
      </div>
    </div>

    <!-- Dedicated Task Reminder Picker Modal -->
    <div v-if="showReminderModal" class="modal-backdrop" @click.self="showReminderModal = false">
      <div class="modal-card modal-reminder-card animate-fade-in">
        <div class="modal-header-row">
          <h2 class="modal-title">
            <Clock :size="18" class="text-primary" />
            <span>设置待办提醒时间</span>
          </h2>
          <button class="modal-close-btn" @click="showReminderModal = false">
            <X :size="16" />
          </button>
        </div>

        <div class="modal-target-todo-info" v-if="reminderTargetTodo">
          <span class="target-label">任务:</span>
          <span class="target-title">{{ reminderTargetTodo.title }}</span>
        </div>

        <!-- 3D Wheel Picker with 12h/24h System Support -->
        <WheelDateTimePicker v-model="reminderPickerValue" />

        <div class="modal-actions-space-between">
          <button
            v-if="reminderTargetTodo?.remind_at"
            type="button"
            class="btn btn-danger-outline"
            @click="clearModalReminder"
          >
            <BellOff :size="14" /> 关闭提醒
          </button>
          <div v-else></div>

          <div class="modal-actions-right">
            <button type="button" class="btn" @click="showReminderModal = false">取消</button>
            <button type="button" class="btn btn-primary" @click="saveModalReminder">确认设置</button>
          </div>
        </div>
      </div>
    </div>

    <!-- Model Config Modal -->
    <div v-if="showModelModal" class="modal-backdrop" @click.self="showModelModal = false">
      <div class="modal-card animate-fade-in">
        <h2 class="modal-title"><Settings :size="18" /> <span>配置大语言模型 (LLM)</span></h2>

        <div class="form-group">
          <label>服务提供商 (Provider) *</label>
          <select v-model="llmConfig.provider" @change="onProviderChange">
            <option value="siliconflow">SiliconFlow (硅基流动云端 API)</option>
            <option value="ollama">Native Ollama (本地大模型)</option>
          </select>
        </div>

        <div class="form-group">
          <label>接口地址 (Base URL)</label>
          <input type="text" v-model="llmConfig.base_url" placeholder="http/https 接口地址" />
        </div>

        <div class="form-group">
          <label>API Key (密钥)</label>
          <input
            type="password"
            v-model="llmConfig.api_key"
            placeholder="sk-..."
            :disabled="llmConfig.provider === 'ollama'"
          />
        </div>

        <div class="form-group">
          <label>模型名称 (Model Name) *</label>
          <input type="text" v-model="llmConfig.model" placeholder="例如: deepseek-ai/DeepSeek-V4-Flash" />
        </div>

        <div class="form-group">
          <label class="checkbox-label">
            <input type="checkbox" v-model="llmConfig.enable_thinking" />
            启用深度思考与推理过程 (Think Mode)
          </label>
        </div>

        <div class="modal-actions">
          <button class="btn" @click="showModelModal = false">取消</button>
          <button class="btn btn-primary" @click="saveLlmConfig">保存配置</button>
        </div>
      </div>
    </div>

    <!-- Login / Registration / Local Mode Modal -->
    <LoginPage
      v-if="showAuthModal"
      @login-success="onLoginSuccess"
      @use-local-mode="onUseLocalMode"
      @close="showAuthModal = false"
    />
  </div>
</template>


<script setup lang="ts">
import { ref, computed, nextTick, onMounted, onUnmounted, watch } from 'vue'
import {
  CheckSquare, Calendar, Clock, Flame, Settings, Menu, X, Hourglass, Bell,
  Plus, Edit3, Trash2, Folder, Search, ListTodo, Inbox, LayoutGrid, Check, Square, ChevronDown, BellOff
} from 'lucide-vue-next'
import type { Todo, LlmConfig, FilterType, ThemeType, NavPosition, User } from './types'
import { showConfirm } from './utils/confirmState'
import { getLlmConfig, saveLlmConfig as persistLlmConfig, getTheme, saveTheme, getNavPosition, saveNavPosition } from './utils/aiStorage'
import { getUserConfig, getCurrentUserId } from './utils/configManager'
import DesktopView from './components/common/DesktopView.vue'
import LocalClockPage from './components/productivity/LocalClockPage.vue'
import CalendarView from './components/productivity/CalendarView.vue'
import PomodoroTimer from './components/productivity/PomodoroTimer.vue'
import AlarmCountdown from './components/productivity/AlarmCountdown.vue'
import SettingsPage from './components/common/SettingsPage.vue'
import LoginPage from './components/common/LoginPage.vue'
import WheelDateTimePicker from './components/widgets/WheelDateTimePicker.vue'

// User Auth & Local Mode State
const currentUser = ref<User | null>(
  localStorage.getItem('todo_current_user')
    ? JSON.parse(localStorage.getItem('todo_current_user')!)
    : null
)
const showAuthModal = ref(false)

// User Dropdown Menu State & Event Listeners
const showUserMenu = ref(false)

// Mobile Navigation Dropdown Menu State (< 640px)
const showMobileNavMenu = ref(false)

function toggleUserMenu(e: Event) {
  e.stopPropagation()
  showUserMenu.value = !showUserMenu.value
  showMobileNavMenu.value = false
}
void toggleUserMenu

// Popover Menus State
const activeMenuId = ref<string | null>(null)
let menuCloseTimer: any = null

function openMenuHover(id: string) {
  if (menuCloseTimer) {
    clearTimeout(menuCloseTimer)
    menuCloseTimer = null
  }
  activeMenuId.value = id
}

function closeMenuHover() {
  menuCloseTimer = setTimeout(() => {
    activeMenuId.value = null
    menuCloseTimer = null
  }, 180)
}

function toggleMenu(id: string) {
  if (menuCloseTimer) {
    clearTimeout(menuCloseTimer)
    menuCloseTimer = null
  }
  activeMenuId.value = activeMenuId.value === id ? null : id
}

function selectPriority(todo: Todo, prio: 'high' | 'medium' | 'low') {
  if (menuCloseTimer) {
    clearTimeout(menuCloseTimer)
    menuCloseTimer = null
  }
  activeMenuId.value = null
  updateTodoPriority(todo, prio)
}

function selectCategory(todo: Todo, cat: string) {
  if (menuCloseTimer) {
    clearTimeout(menuCloseTimer)
    menuCloseTimer = null
  }
  activeMenuId.value = null
  updateTodoCategory(todo, cat)
}

function closeUserMenu() {
  showUserMenu.value = false
  showMobileNavMenu.value = false
  activeMenuId.value = null
}

function toggleMobileNavMenu(e: Event) {
  e.stopPropagation()
  showMobileNavMenu.value = !showMobileNavMenu.value
  showUserMenu.value = false
}

// Navigation Position State (top | left | desktop)
const userInitialConfig = getUserConfig(getCurrentUserId())
const storedNavPos = getNavPosition() as NavPosition | null
const navPosition = ref<NavPosition>(storedNavPos || userInitialConfig.navPosition || 'top')

// Navigation Tab State
type TabType = 'desktop' | 'todos' | 'calendar' | 'local-clock' | 'countdown' | 'alarm' | 'pomodoro' | 'settings'
const currentTab = ref<TabType>(navPosition.value === 'desktop' ? 'desktop' : 'todos')

function selectMobileTab(tab: TabType) {
  currentTab.value = tab
  showMobileNavMenu.value = false
}

watch(navPosition, (newVal) => {
  saveNavPosition(newVal)
  if (newVal === 'desktop') {
    currentTab.value = 'desktop'
  } else if (currentTab.value === 'desktop') {
    currentTab.value = 'todos'
  }
})

onMounted(() => {
  window.addEventListener('click', closeUserMenu)
})

onUnmounted(() => {
  window.removeEventListener('click', closeUserMenu)
})

function onLoginSuccess(user: User) {
  currentUser.value = user
  localStorage.setItem('todo_current_user', JSON.stringify(user))
  localStorage.removeItem('todo_guest_mode')
  showAuthModal.value = false
  statusMessage.value = `🔑 已登录为 [${user.username}] (ID: ${user.id})`
  loadTodos()
}

function onUseLocalMode() {
  currentUser.value = null
  localStorage.removeItem('todo_current_user')
  localStorage.setItem('todo_guest_mode', 'true')
  showAuthModal.value = false
  statusMessage.value = `🏠 已切换为【游客模式】（离线本地可用）`
  loadTodos()
}

function handleLogout() {
  currentUser.value = null
  localStorage.removeItem('todo_current_user')
  localStorage.removeItem('todo_guest_mode')
  showAuthModal.value = true
  statusMessage.value = `↩️ 已退出登录`
  loadTodos()
}

// Theme State
const storedTheme = getTheme() as ThemeType | null
const theme = ref<ThemeType>(storedTheme || 'light')
watch(theme, (newVal) => {
  saveTheme(newVal)
  document.documentElement.setAttribute('data-theme', newVal)
}, { immediate: true })

// LLM Config State
const storedLlmConfig = getLlmConfig()
const llmConfig = ref<LlmConfig>(storedLlmConfig || {
  provider: 'siliconflow',
  base_url: 'https://api.siliconflow.cn/v1',
  api_key: '',
  model: 'deepseek-ai/DeepSeek-V4-Flash',
  enable_thinking: false
})

// Todos State
const todos = ref<Todo[]>([])
const loading = ref(false)
const currentFilter = ref<FilterType>('all')
const searchKeyword = ref('')
const statusMessage = ref('就绪 - Rust 后端与 SQLite 数据库连接正常')

// Modals State
const showAddEditModal = ref(false)
const editingTodo = ref<Todo | null>(null)
const todoForm = ref({
  title: '',
  category: '工作',
  priority: 'medium' as 'high' | 'medium' | 'low',
  enableReminder: false,
  remindAt: ''
})

const showModelModal = ref(false)

// Tauri Invoke Helper (with fallback for web browser testing)
async function tauriInvoke<T>(cmd: string, args: Record<string, any> = {}): Promise<T> {
  try {
    const { invoke } = await import('@tauri-apps/api/core')
    return await invoke<T>(cmd, args)
  } catch (e) {
    console.warn(`[Tauri Web Fallback] ${cmd}`, args, e)
    // Web fallback mock implementation with user_id isolation
    const storageKey = `web_todos_${args.user_id || 0}`
    if (cmd === 'get_todos') {
      if (!localStorage.getItem(storageKey)) {
        const defaultData: Todo[] = [
          { id: 1, title: '完成项目整体架构设计', category: '工作', priority: 'high', completed: true, created_at: new Date().toISOString(), updated_at: new Date().toISOString(), user_id: args.user_id || 0 },
          { id: 2, title: '完成 Tauri Rust SQLite 数据库集成', category: '工作', priority: 'high', completed: true, created_at: new Date().toISOString(), updated_at: new Date().toISOString(), user_id: args.user_id || 0 },
          { id: 3, title: '集成大语言模型配置与语义解析', category: 'AI', priority: 'medium', completed: false, created_at: new Date().toISOString(), updated_at: new Date().toISOString(), user_id: args.user_id || 0 }
        ]
        localStorage.setItem(storageKey, JSON.stringify(defaultData))
      }
      const stored = JSON.parse(localStorage.getItem(storageKey) || '[]') as Todo[]
      return stored as T
    }
    if (cmd === 'add_todo') {
      const stored = JSON.parse(localStorage.getItem(storageKey) || '[]') as Todo[]
      const newId = Date.now()
      stored.push({
        id: newId,
        title: args.title,
        priority: args.priority,
        category: args.category,
        completed: false,
        remind_at: args.remind_at,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        user_id: args.user_id || 0
      })
      localStorage.setItem(storageKey, JSON.stringify(stored))
      return newId as T
    }
    if (cmd === 'update_todo_status') {
      const stored = JSON.parse(localStorage.getItem(storageKey) || '[]') as Todo[]
      const idx = stored.findIndex(t => t.id === args.id)
      if (idx >= 0) stored[idx].completed = args.completed
      localStorage.setItem(storageKey, JSON.stringify(stored))
      return true as T
    }
    if (cmd === 'update_todo') {
      const stored = JSON.parse(localStorage.getItem(storageKey) || '[]') as Todo[]
      const idx = stored.findIndex(t => t.id === args.id)
      if (idx >= 0) {
        stored[idx].title = args.title
        stored[idx].category = args.category
        stored[idx].priority = args.priority
        stored[idx].remind_at = args.remind_at
        stored[idx].updated_at = new Date().toISOString()
      }
      localStorage.setItem(storageKey, JSON.stringify(stored))
      return true as T
    }
    if (cmd === 'delete_todo') {
      let stored = JSON.parse(localStorage.getItem(storageKey) || '[]') as Todo[]
      stored = stored.filter(t => t.id !== args.id)
      localStorage.setItem(storageKey, JSON.stringify(stored))
      return true as T
    }
    if (cmd === 'execute_ai_command') {
      const input = (args.input || '') as string
      const config = (args.config || {}) as LlmConfig
      const userId = args.user_id || 0

      // 1. 如果配置了 API Key，在 Web Fallback 下直接请求大模型 API
      if (config.api_key && config.provider === 'siliconflow') {
        try {
          const resp = await fetch(`${config.base_url}/chat/completions`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${config.api_key}`
            },
            body: JSON.stringify({
              model: config.model || 'deepseek-ai/DeepSeek-V4-Flash',
              messages: [
                { role: 'system', content: '你是一个高效智能的 Todo 待办事项助手。' },
                { role: 'user', content: input }
              ]
            })
          })
          const json = await resp.json()
          if (json.choices && json.choices.length > 0) {
            const aiText = json.choices[0].message.content
            return {
              action: 'chat',
              message: aiText,
              should_refresh: false,
              data: null
            } as T
          }
        } catch (apiErr) {
          console.warn('Web API Fetch Failed, fallback to mock parser:', apiErr)
        }
      }

      // 2. 离线模式 / 未填 Key 时的智能待办指令解析
      let stored = JSON.parse(localStorage.getItem(storageKey) || '[]') as Todo[]

      if (input.includes('新建') || input.includes('创建') || input.includes('添加') || input.includes('提醒我') || input.includes('安排')) {
        let title = input.replace(/(帮我|请|提醒我|新建|创建|添加|安排|待办|任务)/g, '').trim()
        if (!title) title = '新智能待办任务'
        const newTodo: Todo = {
          id: Date.now(),
          title: title,
          category: input.includes('工作') ? '工作' : input.includes('学习') ? '学习' : '生活',
          priority: input.includes('高') || input.includes('紧急') ? 'high' : 'medium',
          completed: false,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
          user_id: userId
        }
        stored.push(newTodo)
        localStorage.setItem(storageKey, JSON.stringify(stored))
        return {
          action: 'add',
          message: `已自动为您创建待办任务：【${title}】`,
          should_refresh: true,
          data: newTodo
        } as T
      } else if (input.includes('完成') || input.includes('做完') || input.includes('标记')) {
        if (stored.length > 0) {
          stored[0].completed = true
          localStorage.setItem(storageKey, JSON.stringify(stored))
          return {
            action: 'complete',
            message: `已为您标记任务【${stored[0].title}】为已完成！`,
            should_refresh: true,
            data: stored[0]
          } as T
        }
      } else if (input.includes('删除') || input.includes('清理')) {
        if (stored.length > 0) {
          const deleted = stored.shift()
          localStorage.setItem(storageKey, JSON.stringify(stored))
          return {
            action: 'delete',
            message: `已为您删除任务【${deleted?.title || ''}】`,
            should_refresh: true,
            data: null
          } as T
        }
      }

      return {
        action: 'chat',
        message: `收到！我是您的 AI 待办助手。您刚才说："${input}"。我可以帮助您创建、完成或整理待办事项！在“系统设置”或 AI 聊天页配置您的 LLM API Key，即可开启完全通用的智能深度对话！`,
        should_refresh: false,
        data: null
      } as T
    }
    throw e
  }
}

// Priority Helpers
function priorityLabel(prio: string) {
  if (prio === 'high') return '高优'
  if (prio === 'low') return '低优'
  return '中优'
}

const pendingTodosCount = computed(() => todos.value.filter(t => !t.completed).length)
const completedTodosCount = computed(() => todos.value.filter(t => t.completed).length)
const highPriorityTodosCount = computed(() => todos.value.filter(t => t.priority === 'high' && !t.completed).length)

// Direct Inline Edit State & Methods
const editingId = ref<number | null>(null)
const inlineEditText = ref('')
const inlineInputRef = ref<HTMLInputElement | null>(null)

function startInlineEdit(todo: Todo) {
  editingId.value = todo.id
  inlineEditText.value = todo.title
  nextTick(() => {
    if (inlineInputRef.value) {
      inlineInputRef.value.focus()
      inlineInputRef.value.select()
    }
  })
}

async function saveInlineEdit(todo: Todo) {
  if (editingId.value !== todo.id) return
  const newTitle = inlineEditText.value.trim()
  editingId.value = null
  if (!newTitle || newTitle === todo.title) return

  const oldTitle = todo.title
  todo.title = newTitle
  try {
    const uid = currentUser.value ? currentUser.value.id : 0
    await tauriInvoke('update_todo', {
      id: todo.id,
      title: newTitle,
      category: todo.category,
      priority: todo.priority,
      remind_at: todo.remind_at,
      user_id: uid
    })
    statusMessage.value = `✏️ 已更新待办标题 [${newTitle}]`
  } catch (err: any) {
    todo.title = oldTitle
    statusMessage.value = `❌ 更新标题失败: ${err?.message || err}`
  }
}

function cancelInlineEdit() {
  editingId.value = null
  inlineEditText.value = ''
}

// Inline Config Updaters (Priority, Category, Reminder)
async function updateTodoPriority(todo: Todo, newPriority: string) {
  const prio = newPriority as 'high' | 'medium' | 'low'
  if (todo.priority === prio) return
  todo.priority = prio
  try {
    const uid = currentUser.value ? currentUser.value.id : 0
    await tauriInvoke('update_todo', {
      id: todo.id,
      title: todo.title,
      category: todo.category,
      priority: prio,
      remind_at: todo.remind_at,
      user_id: uid
    })
    statusMessage.value = `🎯 已更新任务 [${todo.title}] 优先级为 ${priorityLabel(prio)}`
  } catch (err: any) {
    statusMessage.value = `❌ 更新优先级失败: ${err?.message || err}`
  }
}

async function updateTodoCategory(todo: Todo, newCategory: string) {
  if (todo.category === newCategory) return
  todo.category = newCategory
  try {
    const uid = currentUser.value ? currentUser.value.id : 0
    await tauriInvoke('update_todo', {
      id: todo.id,
      title: todo.title,
      category: newCategory,
      priority: todo.priority,
      remind_at: todo.remind_at,
      user_id: uid
    })
    statusMessage.value = `🏷️ 已更新任务 [${todo.title}] 标签为 [${newCategory}]`
  } catch (err: any) {
    statusMessage.value = `❌ 更新标签失败: ${err?.message || err}`
  }
}

function formatRemindDisplay(remindStr?: string | null) {
  if (!remindStr) return ''
  if (remindStr.startsWith('每') || remindStr.includes('重复')) {
    return remindStr.replace(' 重复提醒', '')
  }
  const clean = remindStr.replace('T', ' ')
  if (clean.length >= 16) {
    return clean.slice(5, 16)
  }
  return clean
}

function formatInputDateTime(remindStr?: string | null) {
  if (!remindStr) return ''
  return remindStr.slice(0, 16).replace(' ', 'T')
}
void formatInputDateTime

async function updateTodoReminder(todo: Todo, val: string) {
  const remindFormatted = val ? (val.includes('T') ? val.replace('T', ' ') + (val.length === 16 ? ':00' : '') : val) : null
  todo.remind_at = remindFormatted
  try {
    const uid = currentUser.value ? currentUser.value.id : 0
    await tauriInvoke('update_todo', {
      id: todo.id,
      title: todo.title,
      category: todo.category,
      priority: todo.priority,
      remind_at: remindFormatted,
      user_id: uid
    })
    statusMessage.value = remindFormatted ? `⏰ 已为 [${todo.title}] 设置提醒: ${remindFormatted}` : `🔕 已关闭 [${todo.title}] 提醒`
  } catch (err: any) {
    statusMessage.value = `❌ 更新提醒失败: ${err?.message || err}`
  }
}

// Dedicated Reminder Modal State & Methods
const showReminderModal = ref(false)
const reminderTargetTodo = ref<Todo | null>(null)
const reminderPickerValue = ref('')

function openReminderModal(todo: Todo) {
  reminderTargetTodo.value = todo
  reminderPickerValue.value = todo.remind_at ? todo.remind_at.slice(0, 16).replace(' ', 'T') : ''
  showReminderModal.value = true
}

async function saveModalReminder() {
  if (!reminderTargetTodo.value) return
  const val = reminderPickerValue.value
  await updateTodoReminder(reminderTargetTodo.value, val)
  showReminderModal.value = false
}

async function clearModalReminder() {
  if (!reminderTargetTodo.value) return
  await updateTodoReminder(reminderTargetTodo.value, '')
  showReminderModal.value = false
}

async function clearCompletedTodos() {
  const completedList = todos.value.filter(t => t.completed)
  if (completedList.length === 0) return
  const confirmed = await showConfirm({
    title: '清理已完成待办',
    message: `确定要清理已完成的 ${completedList.length} 项待办任务吗？`,
    confirmText: '确认清理',
    type: 'danger'
  })
  if (!confirmed) return
  for (const item of completedList) {
    await deleteTodo(item.id, true)
  }
}

// Load Todos
async function loadTodos() {
  loading.value = true
  try {
    const uid = currentUser.value ? currentUser.value.id : 0
    const result = await tauriInvoke<Todo[]>('get_todos', {
      filter: currentFilter.value,
      search: searchKeyword.value,
      user_id: uid
    })
    todos.value = result || []
    statusMessage.value = `${currentUser.value ? `👤 [${currentUser.value.username}]` : '🏠 [本地模式]'} 共加载 ${todos.value.length} 项待办任务`
  } catch (err: any) {
    statusMessage.value = `❌ 加载失败: ${err?.message || err}`
  } finally {
    loading.value = false
  }
}

function setFilter(filter: FilterType) {
  currentFilter.value = filter
  loadTodos()
}

// Toggle Status
async function toggleStatus(todo: Todo) {
  const newStatus = !todo.completed
  try {
    const uid = currentUser.value ? currentUser.value.id : 0
    await tauriInvoke('update_todo_status', { id: todo.id, completed: newStatus, user_id: uid })
    todo.completed = newStatus
    statusMessage.value = newStatus ? `✅ 标记任务 [${todo.title}] 已完成` : `↩️ 恢复任务 [${todo.title}] 为未完成`
  } catch (err: any) {
    statusMessage.value = `❌ 更新状态失败: ${err}`
  }
}

// Add/Edit Form Actions
function openAddModal() {
  editingTodo.value = null
  todoForm.value = {
    title: '',
    category: '工作',
    priority: 'medium',
    enableReminder: false,
    remindAt: ''
  }
  showAddEditModal.value = true
}

function openEditModal(todo: Todo) {
  editingTodo.value = todo
  todoForm.value = {
    title: todo.title,
    category: todo.category,
    priority: todo.priority,
    enableReminder: !!todo.remind_at,
    remindAt: todo.remind_at || ''
  }
  showAddEditModal.value = true
}
void openEditModal

async function saveTodoForm() {
  if (!todoForm.value.title.trim()) {
    alert('任务标题不能为空！')
    return
  }

  const remindStr = todoForm.value.enableReminder && todoForm.value.remindAt ? todoForm.value.remindAt.replace('T', ' ') + ':00' : null
  const uid = currentUser.value ? currentUser.value.id : 0

  try {
    if (editingTodo.value) {
      await tauriInvoke('update_todo', {
        id: editingTodo.value.id,
        title: todoForm.value.title.trim(),
        category: todoForm.value.category.trim(),
        priority: todoForm.value.priority,
        remind_at: remindStr,
        user_id: uid
      })
      statusMessage.value = `✅ 待办事项 [${todoForm.value.title}] 更新成功`
    } else {
      await tauriInvoke('add_todo', {
        title: todoForm.value.title.trim(),
        category: todoForm.value.category.trim(),
        priority: todoForm.value.priority,
        remind_at: remindStr,
        user_id: uid
      })
      statusMessage.value = `✨ 成功创建待办事项 [${todoForm.value.title}]`
    }
    showAddEditModal.value = false
    loadTodos()
  } catch (err: any) {
    statusMessage.value = `❌ 保存失败: ${err}`
  }
}

// Delete Todo
async function deleteTodo(id: number, skipConfirm = false) {
  if (!skipConfirm) {
    const confirmed = await showConfirm({
      title: '彻底删除任务',
      message: '确定要彻底删除该待办事项吗？删除后不可恢复。',
      type: 'danger'
    })
    if (!confirmed) return
  }
  try {
    const uid = currentUser.value ? currentUser.value.id : 0
    await tauriInvoke('delete_todo', { id, user_id: uid })
    statusMessage.value = `🗑️ 任务已成功删除`
    loadTodos()
  } catch (err: any) {
    statusMessage.value = `❌ 删除失败: ${err}`
  }
}

// Provider Change
function onProviderChange() {
  if (llmConfig.value.provider === 'siliconflow') {
    llmConfig.value.base_url = 'https://api.siliconflow.cn/v1'
  } else {
    llmConfig.value.base_url = 'http://localhost:11434'
  }
}

function saveLlmConfig() {
  persistLlmConfig(llmConfig.value)
  showModelModal.value = false
  statusMessage.value = `⚙️ LLM 配置已更新 [Provider: ${llmConfig.value.provider}, Model: ${llmConfig.value.model}]`
}

onMounted(() => {
  document.documentElement.setAttribute('data-theme', theme.value)
  loadTodos()
  
  // 启动软件后，若未登录且未记住游客模式，自动弹出 3D 登录/注册卡片
  const isGuest = localStorage.getItem('todo_guest_mode') === 'true'
  if (!currentUser.value && !isGuest) {
    showAuthModal.value = true
  }
})
</script>

<style scoped>
.app-layout {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background-color: var(--bg-app);
}

/* VS Code style Left Navigation Sidebar */
.layout-nav-left {
  flex-direction: row;
  height: 100vh;
  overflow: hidden;
}

.layout-nav-left .header {
  width: 200px;
  min-width: 200px;
  max-width: 200px;
  height: 100vh;
  flex-direction: column;
  justify-content: flex-start;
  align-items: stretch;
  padding: 16px 12px;
  border-bottom: none;
  border-right: 1px solid var(--border-color);
  box-sizing: border-box;
  flex-shrink: 0;
  gap: 16px;
  background-color: var(--bg-surface);
}

.layout-nav-left .header-left {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 8px;
  padding: 0 4px 12px 4px;
  border-bottom: 1px solid var(--border-color);
  width: 100%;
}

.layout-nav-left .app-title {
  font-size: 16px;
  font-weight: 700;
  color: var(--primary);
  margin: 0;
}

.layout-nav-left .navbar-tabs {
  display: flex;
  flex-direction: column;
  align-items: stretch;
  gap: 4px;
  background: transparent;
  border: none;
  padding: 0;
  width: 100%;
  flex: 1;
  overflow-y: auto;
}

.layout-nav-left .nav-tab-btn {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 10px;
  padding: 9px 12px;
  border-radius: 6px;
  width: 100%;
  font-size: 13px;
  font-weight: 500;
  text-align: left;
  border: 1px solid transparent;
  color: var(--text-muted);
  box-sizing: border-box;
  transition: all 0.18s ease;
}

.layout-nav-left .nav-tab-btn span {
  display: inline-block !important;
}

.layout-nav-left .nav-tab-btn:hover {
  background-color: var(--bg-hover);
  color: var(--text-main);
}

.layout-nav-left .nav-tab-btn.active {
  background-color: var(--bg-hover);
  color: var(--primary);
  border-left: 3px solid var(--primary);
  border-radius: 4px;
  font-weight: 600;
  box-shadow: none;
}

.layout-nav-left .main-content {
  flex: 1;
  height: 100vh;
  min-height: 0;
  overflow-y: auto;
}

@media (max-width: 640px) {
  .layout-nav-left {
    flex-direction: column;
  }

  .layout-nav-left .header {
    width: 100%;
    min-width: 100%;
    max-width: 100%;
    height: auto;
    flex-direction: row;
    align-items: center;
    justify-content: space-between;
    padding: 12px 16px;
    border-right: none;
    border-bottom: 1px solid var(--border-color);
  }

  .layout-nav-left .header-left {
    flex-direction: row;
    align-items: center;
    border-bottom: none;
    padding-bottom: 0;
    width: auto;
  }

  .layout-nav-left .navbar-tabs {
    display: none;
  }
}

.header {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 20px;
  background-color: var(--bg-surface);
  border-bottom: 1px solid var(--border-color);
  gap: 12px;
  flex-wrap: nowrap;
  z-index: 100;
}

.mobile-nav-toggle-btn {
  display: none;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 8px;
  border: 1px solid var(--border-color);
  background: var(--bg-app);
  color: var(--text-main);
  cursor: pointer;
  transition: all 0.2s ease;
}

.mobile-nav-toggle-btn:hover {
  background: var(--bg-hover);
  border-color: var(--primary);
  color: var(--primary);
}

.navbar-tabs {
  display: flex;
  align-items: center;
  gap: 4px;
  background-color: var(--bg-app);
  padding: 4px;
  border-radius: 10px;
  border: 1px solid var(--border-color);
  flex-shrink: 1;
}

.nav-tab-btn {
  position: relative;
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  border-radius: 8px;
  border: none;
  background: transparent;
  color: var(--text-muted);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.2s ease;
  flex-shrink: 0;
}

.nav-tab-btn:hover {
  color: var(--text-main);
  background-color: var(--bg-hover);
}

.nav-tab-btn.active {
  color: var(--primary);
  background-color: var(--bg-surface);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

/* Mobile Dropdown Navigation Styles (< 640px) */
.mobile-dropdown-menu {
  position: absolute;
  top: calc(100% + 1px);
  left: 0;
  right: 0;
  background-color: var(--bg-surface);
  border-bottom: 1px solid var(--border-color);
  box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.15);
  padding: 12px 16px;
  z-index: 999;
  display: flex;
  flex-direction: column;
  gap: 12px;
  backdrop-filter: blur(12px);
}

.mobile-nav-links {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px;
}

.mobile-nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  border-radius: 8px;
  border: 1px solid var(--border-color);
  background-color: var(--bg-app);
  color: var(--text-muted);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.mobile-nav-item:hover {
  background-color: var(--bg-hover);
  color: var(--text-main);
  border-color: var(--primary);
}

.mobile-nav-item.active {
  background-color: var(--primary);
  color: #ffffff;
  border-color: var(--primary);
  font-weight: 600;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

.mobile-nav-divider {
  height: 1px;
  background-color: var(--border-color);
  margin: 2px 0;
}

.mobile-user-section {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.mobile-user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  font-weight: 600;
  color: var(--text-main);
}

.mobile-action-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  border-radius: 8px;
  border: none;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.mobile-action-btn.primary {
  background-color: var(--primary);
  color: #ffffff;
}

.mobile-action-btn.danger {
  background-color: rgba(239, 68, 68, 0.1);
  color: #ef4444;
}

.mobile-action-btn.danger:hover {
  background-color: #ef4444;
  color: #ffffff;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
  white-space: nowrap;
}

.app-title {
  font-size: 18px;
  font-weight: 700;
  color: var(--primary);
  white-space: nowrap;
}

.sub-badge {
  font-size: 11px;
  font-weight: 600;
  background-color: var(--border-color);
  color: var(--text-muted);
  padding: 2px 8px;
  border-radius: 12px;
  white-space: nowrap;
}

.model-badge-btn {
  background-color: var(--bg-app);
  color: var(--ai-purple);
  border: 1px solid var(--border-color);
  border-radius: 16px;
  padding: 4px 12px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.2s;
}

.model-badge-btn:hover {
  border-color: var(--ai-purple);
  transform: translateY(-1px);
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
  white-space: nowrap;
}

/* Responsive Header Styles */
@media (max-width: 1024px) {
  .header {
    padding: 10px 14px;
    gap: 8px;
  }

  .sub-badge {
    display: none;
  }

  .nav-tab-btn {
    padding: 5px 10px;
    font-size: 12px;
  }
}

@media (max-width: 860px) {
  .nav-tab-btn span {
    display: none;
  }

  .nav-tab-btn {
    padding: 6px 10px;
  }

  /* Show Hover Tooltip when text is hidden */
  .nav-tab-btn[data-tooltip]:hover::after {
    content: attr(data-tooltip);
    position: absolute;
    top: calc(100% + 8px);
    left: 50%;
    transform: translateX(-50%);
    background-color: var(--text-main);
    color: var(--bg-surface);
    padding: 4px 8px;
    border-radius: 6px;
    font-size: 11px;
    font-weight: 500;
    white-space: nowrap;
    pointer-events: none;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    z-index: 1000;
  }

  .app-title {
    font-size: 16px;
  }
}

@media (max-width: 640px) {
  .mobile-nav-toggle-btn {
    display: flex;
  }

  .navbar-tabs {
    display: none;
  }

  .header-right .user-dropdown-container {
    display: none;
  }

  .ai-assistant-toggle-btn span {
    display: none;
  }

  .app-title {
    font-size: 15px;
  }

  .main-content {
    padding: 12px 10px;
  }

  .toolbar {
    flex-direction: column;
    align-items: stretch;
    gap: 10px;
  }

  .toolbar-right {
    width: 100%;
    justify-content: space-between;
  }

  .search-box {
    flex: 1;
  }

  .search-box input {
    width: 100%;
  }

  .filter-group {
    flex-wrap: wrap;
  }
}

@media (max-width: 480px) {
  .todo-card {
    padding: 10px 12px;
  }

  .card-meta {
    flex-wrap: wrap;
    gap: 4px;
  }
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

/* Stats Banner Row */
.stats-banner-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 16px;
  background: var(--bg-surface, #f8fafc);
  border: 1px solid var(--border-color, #e2e8f0);
  border-radius: 10px;
  flex-wrap: wrap;
}

.stats-pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 12.5px;
  color: var(--text-main, #1e293b);
}

.icon-primary { color: var(--primary, #3b82f6); }
.icon-success { color: #10b981; }
.icon-flame { color: #ef4444; }

.clear-stats-btn {
  margin-left: auto;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 11.5px;
  color: var(--text-muted, #94a3b8);
  background: transparent;
  border: none;
  cursor: pointer;
  transition: color 0.2s;
}

.clear-stats-btn:hover { color: #ef4444; }

/* List & Grid */
.list-scroll-area {
  flex: 1;
  overflow-y: auto;
  padding-right: 4px;
  padding-bottom: 80px;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 280px;
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
  z-index: 1;
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

.list-card-item:hover,
.list-card-item.has-active-menu {
  border-color: var(--primary, #3b82f6);
  box-shadow: 0 6px 16px rgba(59, 130, 246, 0.08);
  transform: translateY(-1px);
  z-index: 40;
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

.mini-todo-icon {
  width: 38px;
  height: 38px;
  border-radius: 10px;
  background: var(--bg-surface, #f8fafc);
  border: 1px solid var(--border-color, #e2e8f0);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-muted, #64748b);
  cursor: pointer;
  transition: all 0.2s ease;
}

.mini-todo-icon:hover {
  border-color: var(--primary, #3b82f6);
  color: var(--primary, #3b82f6);
}

.mini-todo-icon.checked {
  background: rgba(16, 185, 129, 0.1);
  color: #10b981;
  border-color: rgba(16, 185, 129, 0.3);
}

.card-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-width: 0;
}

/* Row 1: Title Line */
.card-title-row {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
}

.card-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-main, #0f172a);
  line-height: 1.4;
}

.clickable-title {
  cursor: text;
  padding: 2px 6px;
  margin: -2px -6px;
  border-radius: 6px;
  transition: all 0.2s ease;
}

.clickable-title:hover {
  background-color: rgba(59, 130, 246, 0.08);
  color: var(--primary, #3b82f6);
}

.inline-edit-wrapper {
  display: inline-flex;
  align-items: center;
  flex: 1;
  width: 100%;
}

.inline-edit-input {
  font-size: 14.5px;
  font-weight: 600;
  color: var(--text-main, #0f172a);
  background: var(--bg-surface, #ffffff);
  border: 1.5px solid var(--primary, #3b82f6);
  border-radius: 6px;
  padding: 4px 8px;
  outline: none;
  width: 100%;
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2);
  font-family: inherit;
}

.card-title.strike {
  text-decoration: line-through;
  color: var(--text-muted, #94a3b8);
}

/* Row 2: Metadata & Quick Interactive Config Row */
.card-meta-row {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.meta-item-config {
  position: relative;
  display: inline-flex;
  align-items: center;
  z-index: 50;
}

.interactive-pill {
  position: relative;
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 3px 9px;
  border-radius: 6px;
  border: 1px solid var(--border-color, #e2e8f0);
  background: var(--bg-surface, #f8fafc);
  color: var(--text-muted, #64748b);
  font-size: 11.5px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  user-select: none;
}

.interactive-pill:hover {
  border-color: var(--primary, #3b82f6);
  background: var(--bg-surface, #ffffff);
  color: var(--primary, #3b82f6);
  box-shadow: 0 2px 6px rgba(59, 130, 246, 0.15);
  transform: translateY(-1px);
}

.interactive-pill .pill-arrow {
  opacity: 0.5;
  transition: transform 0.2s;
}

.interactive-pill:hover .pill-arrow {
  opacity: 1;
  transform: rotate(180deg);
}

.prio-pill .prio-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background-color: currentColor;
}

.prio-pill.high {
  background: rgba(239, 68, 68, 0.08);
  border-color: rgba(239, 68, 68, 0.25);
  color: #ef4444;
}

.prio-pill.medium {
  background: rgba(245, 158, 11, 0.08);
  border-color: rgba(245, 158, 11, 0.25);
  color: #f59e0b;
}

.prio-pill.low {
  background: rgba(59, 130, 246, 0.08);
  border-color: rgba(59, 130, 246, 0.25);
  color: var(--primary, #3b82f6);
}

.cat-pill:hover {
  border-color: var(--primary, #3b82f6);
  color: var(--primary, #3b82f6);
}

.reminder-pill.active {
  background: rgba(128, 90, 213, 0.1);
  border-color: rgba(128, 90, 213, 0.3);
  color: var(--ai-purple, #805ad5);
}

.reminder-pill .placeholder {
  opacity: 0.7;
}

.pill-arrow.rotated {
  transform: rotate(180deg);
  opacity: 1;
}

/* Custom Rounded Popover Menus (Highest Layer to avoid occlusion) */
.custom-dropdown-menu {
  position: absolute;
  top: calc(100% + 4px);
  left: 0;
  z-index: 1000;
  min-width: 145px;
  background: var(--bg-surface, #ffffff);
  border: 1px solid var(--border-color, #e2e8f0);
  border-radius: 12px;
  padding: 6px;
  box-shadow: 0 12px 28px -4px rgba(0, 0, 0, 0.18), 0 6px 14px -2px rgba(0, 0, 0, 0.08);
  display: flex;
  flex-direction: column;
  gap: 2px;
  animation: modalScale 0.15s ease-out;
  backdrop-filter: blur(12px);
}

/* Hover bridge so moving mouse between pill and menu stays connected */
.custom-dropdown-menu::before {
  content: '';
  position: absolute;
  top: -8px;
  left: 0;
  right: 0;
  height: 8px;
}

.dropdown-header {
  font-size: 10.5px;
  font-weight: 700;
  color: var(--text-muted, #94a3b8);
  padding: 4px 8px;
  border-bottom: 1px solid var(--border-color, #f1f5f9);
  margin-bottom: 2px;
}

.dropdown-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 10px;
  border-radius: 8px;
  border: none;
  background: transparent;
  color: var(--text-main, #334155);
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  width: 100%;
  text-align: left;
  transition: all 0.15s ease;
}

.dropdown-item:hover {
  background: var(--bg-app, #f8fafc);
  color: var(--primary, #3b82f6);
}

.dropdown-item.selected {
  background: rgba(59, 130, 246, 0.08);
  color: var(--primary, #3b82f6);
  font-weight: 700;
}

.dropdown-item .item-icon {
  color: var(--text-muted, #94a3b8);
}

.dropdown-item .check-icon {
  margin-left: auto;
  color: var(--primary, #3b82f6);
}

.dot-prio {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  flex-shrink: 0;
}
.dot-prio.red { background-color: #ef4444; }
.dot-prio.yellow { background-color: #f59e0b; }
.dot-prio.blue { background-color: #3b82f6; }

.btn-clear-reminder {
  position: relative;
  z-index: 3;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  color: var(--text-muted, #94a3b8);
  cursor: pointer;
  padding: 1px 2px;
  border-radius: 4px;
  transition: color 0.2s;
}

.btn-clear-reminder:hover {
  color: #ef4444;
}

/* Modal Reminder Card & Wheel Picker Styles */
.modal-reminder-card {
  max-width: 520px;
  width: 92%;
  border-radius: 20px;
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.modal-header-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.modal-close-btn {
  background: transparent;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  padding: 4px;
  border-radius: 8px;
  transition: all 0.2s;
}

.modal-close-btn:hover {
  background: var(--bg-app);
  color: var(--text-main);
}

.modal-target-todo-info {
  background: var(--bg-app, #f8fafc);
  border: 1px solid var(--border-color, #e2e8f0);
  border-radius: 10px;
  padding: 8px 12px;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
}

.modal-target-todo-info .target-label {
  color: var(--text-muted);
  font-weight: 600;
}

.modal-target-todo-info .target-title {
  color: var(--text-main);
  font-weight: 700;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.modal-actions-space-between {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-top: 6px;
}

.modal-actions-right {
  display: flex;
  align-items: center;
  gap: 10px;
}

.btn-danger-outline {
  background: transparent;
  border: 1px solid rgba(239, 68, 68, 0.3);
  color: #ef4444;
  border-radius: 10px;
  padding: 8px 14px;
  font-size: 12.5px;
  font-weight: 600;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-danger-outline:hover {
  background: rgba(239, 68, 68, 0.1);
  border-color: #ef4444;
}

.modal-wheel-picker-wrap {
  margin-top: 8px;
}

/* Global Rounded Select Styling */
select {
  border-radius: 10px !important;
  padding: 8px 12px;
  border: 1px solid var(--border-color, #e2e8f0);
  background-color: var(--bg-surface, #ffffff);
  color: var(--text-main, #334155);
  font-family: inherit;
  outline: none;
  transition: border-color 0.2s, box-shadow 0.2s;
}

select:focus {
  border-color: var(--primary, #3b82f6);
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2);
}

option {
  border-radius: 8px;
  padding: 6px 10px;
}

.status-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  font-weight: 600;
  padding: 3px 8px;
  border-radius: 10px;
  background: var(--bg-app, #f1f5f9);
  color: var(--text-muted, #64748b);
}

.status-tag .dot {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background-color: currentColor;
}

.status-tag.pending {
  background: rgba(59, 130, 246, 0.08);
  color: var(--primary, #3b82f6);
}

.status-tag.finished {
  background: rgba(16, 185, 129, 0.1);
  color: #10b981;
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

.btn-action-primary.done {
  background: #10b981;
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

.ai-input-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 20px;
  background-color: var(--bg-surface);
  border-top: 1px solid var(--border-color);
}

.ai-input-bar input {
  flex: 1;
}



/* Modals */
.modal-backdrop {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
  backdrop-filter: blur(4px);
}

.modal-card {
  width: 440px;
  max-width: calc(100vw - 24px);
  box-sizing: border-box;
  background-color: var(--bg-surface);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  padding: 24px;
  box-shadow: var(--shadow-lg);
}

.modal-title {
  font-size: 16px;
  font-weight: 700;
  margin-bottom: 18px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-bottom: 14px;
}

.form-group label {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-muted);
}

.form-row {
  display: flex;
  gap: 12px;
}

.flex-1 {
  flex: 1;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

.modal-actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 20px;
}

/* User Dropdown Menu */
.user-dropdown {
  position: relative;
  display: inline-block;
}

.user-avatar-btn {
  background-color: var(--bg-app);
  border: 1px solid var(--border-color);
  color: var(--text-main);
  border-radius: 16px;
  padding: 5px 12px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.user-avatar-btn:hover {
  border-color: var(--primary);
  color: var(--primary);
}

.dropdown-menu {
  position: absolute;
  top: calc(100% + 6px);
  right: 0;
  background-color: var(--bg-surface);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-lg);
  min-width: 130px;
  display: none;
  flex-direction: column;
  padding: 4px;
  z-index: 1000;
}

.user-dropdown:hover .dropdown-menu {
  display: flex;
}

.dropdown-item {
  padding: 8px 12px;
  font-size: 12px;
  font-weight: 500;
  color: var(--text-main);
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.2s ease;
}

.dropdown-item:hover {
  background-color: var(--bg-card-hover);
  color: var(--primary);
}

.dropdown-item.danger {
  color: #E53E3E;
}

.dropdown-item.danger:hover {
  background-color: rgba(229, 62, 62, 0.1);
}

.main-content {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 20px;
  display: flex;
  flex-direction: column;
  box-sizing: border-box;
}

/* User Auth Badge Styles */
.user-badge {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 10px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
}

.user-dropdown-container {
  position: relative;
}

.user-badge-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  background-color: rgba(59, 130, 246, 0.1);
  border: 1px solid rgba(59, 130, 246, 0.3);
  color: var(--primary, #3b82f6);
  padding: 4px 10px;
  border-radius: 20px;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.user-badge-btn:hover {
  background-color: rgba(59, 130, 246, 0.2);
  border-color: var(--primary, #3b82f6);
}

.chevron-icon {
  transition: transform 0.2s ease;
  color: var(--text-muted, #64748b);
}

.chevron-icon.open {
  transform: rotate(180deg);
}

.user-dropdown-menu {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  width: 170px;
  background-color: var(--bg-card, #ffffff);
  border: 1px solid var(--border-color, #e2e8f0);
  border-radius: 10px;
  box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.12), 0 8px 10px -6px rgba(0, 0, 0, 0.06);
  padding: 6px;
  z-index: 1000;
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.dropdown-header {
  padding: 6px 8px;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.dropdown-user-name {
  font-weight: 700;
  font-size: 13px;
  color: var(--text-main, #0f172a);
}

.dropdown-user-id {
  font-size: 11px;
  color: var(--text-muted, #64748b);
}

.dropdown-divider {
  height: 1px;
  background-color: var(--border-color, #e2e8f0);
  margin: 2px 0;
}

.dropdown-item {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 7px 10px;
  border-radius: 6px;
  border: none;
  background: transparent;
  color: var(--text-main, #334155);
  font-size: 12px;
  cursor: pointer;
  transition: background-color 0.15s ease, color 0.15s ease;
  text-align: left;
}

.dropdown-item:hover {
  background-color: var(--bg-hover, #f1f5f9);
  color: var(--primary, #3b82f6);
}

.dropdown-item.danger {
  color: #ef4444;
}

.dropdown-item.danger:hover {
  background-color: rgba(239, 68, 68, 0.1);
  color: #dc2626;
}

.user-name-label {
  font-weight: 700;
  max-width: 110px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.user-badge.local-mode {
  background-color: rgba(16, 185, 129, 0.1);
  border: 1px solid rgba(16, 185, 129, 0.3);
  color: #059669;
}

.mode-label {
  font-weight: 600;
}

.login-trigger-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  background-color: var(--primary, #3b82f6);
  color: #ffffff;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.login-trigger-btn:hover {
  opacity: 0.9;
  transform: translateY(-1px);
}

/* =========================================================
   Desktop OS Layout & Floating Dock Bar Styles
   ========================================================= */
.layout-nav-desktop {
  position: relative;
  height: 100vh;
  overflow: hidden;
}

.layout-nav-desktop .main-content {
  padding-bottom: 84px;
}

.desktop-dock-wrapper {
  position: fixed;
  bottom: 20px;
  left: 0;
  right: 0;
  width: 100vw;
  display: flex;
  justify-content: center;
  align-items: center;
  pointer-events: none;
  z-index: 9999;
}

.desktop-dock-bar {
  pointer-events: auto;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 8px 14px;
  background: var(--bg-surface, rgba(255, 255, 255, 0.92));
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid var(--border-color, rgba(226, 232, 240, 0.8));
  border-radius: 24px;
  box-shadow: 0 16px 36px -6px rgba(0, 0, 0, 0.18), 0 0 0 1px rgba(255, 255, 255, 0.2) inset;
  margin: 0 auto;
}

.dock-btn {
  position: relative;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  border: none;
  background: transparent;
  color: var(--text-muted, #64748b);
  cursor: pointer;
  transition: all 0.22s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.dock-btn:hover {
  transform: translateY(-4px) scale(1.18);
  color: var(--primary, #3b82f6);
  background: rgba(59, 130, 246, 0.12);
}

.dock-btn.active {
  color: #ffffff;
  background: var(--primary, #3b82f6);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
}

.dock-divider {
  width: 1px;
  height: 22px;
  background: var(--border-color, #e2e8f0);
  margin: 0 4px;
}

.dock-tooltip {
  position: absolute;
  top: -34px;
  left: 50%;
  transform: translateX(-50%);
  background: rgba(15, 23, 42, 0.88);
  color: #ffffff;
  font-size: 11px;
  font-weight: 600;
  padding: 4px 8px;
  border-radius: 6px;
  white-space: nowrap;
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.15s ease, transform 0.15s ease;
}

.dock-btn:hover .dock-tooltip {
  opacity: 1;
  transform: translateX(-50%) translateY(-2px);
}

@media (max-width: 640px) {
  .desktop-dock-wrapper {
    bottom: 12px;
  }
  .desktop-dock-bar {
    padding: 6px 10px;
    gap: 4px;
  }
  .dock-btn {
    width: 34px;
    height: 34px;
  }
}
</style>


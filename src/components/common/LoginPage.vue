<template>
  <div class="login-overlay animate-fade-in">
    <div class="login-card shadow-2xl">
      <!-- Top Brand Header -->
      <div class="login-header">
        <div class="brand-logo">
          <CheckSquare :size="32" class="logo-icon" />
        </div>
        <h1 class="brand-title">Todo Agent</h1>
        <p class="brand-subtitle">智能待办事项与个人效率 AI 助手</p>
      </div>

      <!-- Mode Switch Tabs -->
      <div class="tab-switch">
        <button
          class="tab-btn"
          :class="{ active: mode === 'login' }"
          @click="mode = 'login'"
        >
          <LogIn :size="16" /> 用户登录
        </button>
        <button
          class="tab-btn"
          :class="{ active: mode === 'register' }"
          @click="mode = 'register'"
        >
          <UserPlus :size="16" /> 新建账号
        </button>
      </div>

      <!-- Form Content: Login Mode -->
      <form v-if="mode === 'login'" class="login-form" @submit.prevent="handleLogin">
        <div class="form-group">
          <label class="input-label">选择登录账号</label>
          <div class="user-select-grid">
            <div
              v-for="item in usersList"
              :key="item.user.id"
              class="user-select-card"
              :class="{ selected: selectedUserId === item.user.id }"
              @click="selectedUserId = item.user.id"
            >
              <div
                class="avatar-circle"
                :style="{ backgroundColor: item.user.avatarColor || '#3B82F6' }"
              >
                {{ item.user.username.substring(0, 1).toUpperCase() }}
              </div>
              <div class="user-name-box">
                <span class="user-name">{{ item.user.username }}</span>
                <span class="user-id-sub">ID: {{ item.user.id }}</span>
              </div>
              <CheckCircle2 v-if="selectedUserId === item.user.id" class="check-icon" :size="18" />
            </div>
          </div>
        </div>

        <div class="form-group">
          <label class="input-label">账号密码</label>
          <div class="input-wrapper">
            <Lock :size="16" class="field-icon" />
            <input
              type="password"
              v-model="passwordInput"
              placeholder="请输入密码"
              class="form-input"
            />
          </div>
        </div>

        <div v-if="errorMessage" class="error-tip-alert">
          {{ errorMessage }}
        </div>

        <button type="submit" class="submit-btn" :disabled="!selectedUserId">
          <LogIn :size="16" /> 登录管理员 / 选中账号
        </button>
      </form>

      <!-- Form Content: Register Mode -->
      <form v-else class="login-form" @submit.prevent="handleRegister">
        <div class="form-group">
          <label class="input-label">账号用户名</label>
          <div class="input-wrapper">
            <User :size="16" class="field-icon" />
            <input
              type="text"
              v-model="registerUsername"
              placeholder="请输入您的昵称或用户名"
              class="form-input"
              required
            />
          </div>
        </div>

        <div class="form-group">
          <label class="input-label">专属主题头像配色</label>
          <div class="color-options">
            <button
              type="button"
              v-for="color in avatarColors"
              :key="color"
              class="color-pill"
              :style="{ backgroundColor: color }"
              :class="{ active: selectedColor === color }"
              @click="selectedColor = color"
            ></button>
          </div>
        </div>

        <button type="submit" class="submit-btn register-theme" :disabled="!registerUsername.trim()">
          <UserPlus :size="16" /> 创建新用户 JSON 配置
        </button>
      </form>

      <div class="login-footer">
        <span>配置格式: 独立 JSON 文件存储 ｜ Rust SQLite 驱动支撑</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { CheckSquare, LogIn, UserPlus, Lock, User, CheckCircle2 } from 'lucide-vue-next'
import {
  getAllUserAccountsMap,
  setCurrentUserId,
  createNewUser,
  verifyUserPassword,
  type UserAccountData
} from '../../utils/configManager'

const emit = defineEmits<{
  (e: 'loginSuccess'): void
}>()

const mode = ref<'login' | 'register'>('login')
const usersMap = ref<Record<string, UserAccountData>>(getAllUserAccountsMap())
const usersList = computed(() => Object.values(usersMap.value))

const selectedUserId = ref<string>('user_admin')
const passwordInput = ref('')
const errorMessage = ref('')

const registerUsername = ref('')
const registerPassword = ref('123456')
const avatarColors = ['#3B82F6', '#10B981', '#F59E0B', '#EC4899', '#8B5CF6', '#64748B']
const selectedColor = ref(avatarColors[0])

function handleLogin() {
  errorMessage.value = ''
  if (!selectedUserId.value) return

  // 验证密码
  const isValid = verifyUserPassword(selectedUserId.value, passwordInput.value)
  if (!isValid) {
    errorMessage.value = '❌ 账号或密码错误，请重新输入！'
    return
  }

  setCurrentUserId(selectedUserId.value)
  emit('loginSuccess')
}

function handleRegister() {
  errorMessage.value = ''
  if (!registerUsername.value.trim()) return
  const pass = registerPassword.value.trim() || '123456'
  const newUser = createNewUser(registerUsername.value.trim(), pass, selectedColor.value)
  setCurrentUserId(newUser.id)
  emit('loginSuccess')
}
</script>

<style scoped>
.login-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, rgba(15, 23, 42, 0.85) 0%, rgba(30, 41, 59, 0.95) 100%);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.login-card {
  width: 440px;
  max-width: 90vw;
  background-color: var(--bg-card, #ffffff);
  border: 1px solid var(--border-color, #e2e8f0);
  border-radius: 16px;
  padding: 32px;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.login-header {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
}

.brand-logo {
  width: 56px;
  height: 56px;
  border-radius: 14px;
  background: linear-gradient(135deg, #3B82F6 0%, #2563EB 100%);
  color: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 12px;
  box-shadow: 0 8px 16px -4px rgba(59, 130, 246, 0.4);
}

.brand-title {
  font-size: 22px;
  font-weight: 800;
  color: var(--text-main, #0f172a);
  margin: 0;
}

.brand-subtitle {
  font-size: 13px;
  color: var(--text-muted, #64748b);
  margin-top: 4px;
}

.tab-switch {
  display: flex;
  background-color: var(--bg-app, #f8fafc);
  border-radius: 10px;
  padding: 4px;
  gap: 4px;
}

.tab-btn {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 8px 0;
  font-size: 13px;
  font-weight: 600;
  color: var(--text-muted, #64748b);
  border: none;
  background: transparent;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.tab-btn.active {
  background-color: var(--bg-card, #ffffff);
  color: var(--primary, #3b82f6);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.input-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-main, #334155);
}

.user-select-grid {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 180px;
  overflow-y: auto;
}

.user-select-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 14px;
  border-radius: 10px;
  border: 1px solid var(--border-color, #e2e8f0);
  background-color: var(--bg-app, #f8fafc);
  cursor: pointer;
  transition: all 0.2s ease;
}

.user-select-card:hover {
  border-color: var(--primary, #3b82f6);
}

.user-select-card.selected {
  border-color: var(--primary, #3b82f6);
  background-color: rgba(59, 130, 246, 0.08);
}

.avatar-circle {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  color: #fff;
  font-size: 14px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
}

.user-name-box {
  display: flex;
  flex-direction: column;
  flex: 1;
}

.user-name {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-main, #0f172a);
}

.user-id-sub {
  font-size: 10px;
  color: var(--text-muted, #64748b);
}

.check-icon {
  color: var(--primary, #3b82f6);
}

.input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.field-icon {
  position: absolute;
  left: 12px;
  color: var(--text-muted, #94a3b8);
}

.form-input {
  width: 100%;
  padding: 10px 12px 10px 36px;
  border-radius: 8px;
  border: 1px solid var(--border-color, #cbd5e1);
  background-color: var(--bg-app, #f8fafc);
  color: var(--text-main, #0f172a);
  font-size: 13px;
  outline: none;
}

.form-input:focus {
  border-color: var(--primary, #3b82f6);
}

.color-options {
  display: flex;
  gap: 10px;
}

.color-pill {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  border: 2px solid transparent;
  cursor: pointer;
  transition: transform 0.2s ease;
}

.color-pill.active {
  transform: scale(1.15);
  border-color: var(--text-main, #0f172a);
}

.submit-btn {
  width: 100%;
  padding: 12px;
  border-radius: 8px;
  border: none;
  background-color: var(--primary, #3b82f6);
  color: #ffffff;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  transition: opacity 0.2s ease;
}

.submit-btn:hover {
  opacity: 0.9;
}

.submit-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.submit-btn.register-theme {
  background-color: #10B981;
}

.error-tip-alert {
  font-size: 12px;
  color: #ef4444;
  background-color: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.2);
  border-radius: 6px;
  padding: 8px 12px;
}

.login-footer {
  text-align: center;
  font-size: 11px;
  color: var(--text-muted, #94a3b8);
}
</style>

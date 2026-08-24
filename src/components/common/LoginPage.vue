<template>
  <div class="login-overlay animate-fade-in" @click.self="handleClose">
    <!-- 3D Perspective Card Container -->
    <div class="card-perspective">
      <div class="flip-card-inner" :class="{ 'is-flipped': isFlipped }">
        
        <!-- FRONT FACE: LOGIN CARD -->
        <div class="card-face card-front shadow-2xl">
          <!-- Close Button -->
          <button class="close-btn" @click="handleClose" title="关闭"><X :size="16" /></button>

          <!-- Header -->
          <div class="login-header">
            <div class="brand-logo">
              <CheckSquare :size="32" class="logo-icon" />
            </div>
            <h1 class="brand-title">Todo Agent</h1>
            <p class="brand-subtitle">智能待办事项与个人效率 AI 助手</p>
          </div>

          <!-- Mode Title & Flip Action Header -->
          <div class="card-mode-bar">
            <span class="mode-tag"><LogIn :size="15" /> 用户登录</span>
            <button type="button" class="flip-trigger-btn" @click="toggleFlip">
              <span>去注册账号</span> <Repeat :size="13" />
            </button>
          </div>

          <!-- Login Form -->
          <form class="login-form" @submit.prevent="handleLogin">
            <div class="form-group">
              <label class="input-label">用户名</label>
              <div class="input-wrapper">
                <User :size="16" class="field-icon" />
                <input
                  type="text"
                  v-model="loginUsername"
                  placeholder="请输入注册时的用户名"
                  class="form-input"
                  required
                />
              </div>
            </div>

            <div class="form-group">
              <label class="input-label">账号密码</label>
              <div class="input-wrapper">
                <Lock :size="16" class="field-icon" />
                <input
                  type="password"
                  v-model="loginPassword"
                  placeholder="请输入密码"
                  class="form-input"
                  required
                />
              </div>
            </div>

            <div v-if="errorMessage && !isFlipped" class="error-tip-alert">
              {{ errorMessage }}
            </div>
            <div v-if="successMessage && !isFlipped" class="success-tip-alert">
              {{ successMessage }}
            </div>

            <button type="submit" class="submit-btn" :disabled="loading">
              <span v-if="loading" class="spinner-sm"></span>
              <LogIn v-else :size="16" />
              <span>{{ loading ? '登录中...' : '立即登录' }}</span>
            </button>
          </form>

          <!-- Guest Mode Quick Entry -->
          <div class="local-mode-banner" @click="handleUseLocalMode" title="以游客身份使用全部本地功能">
            <div class="banner-left">
              <Home :size="18" class="banner-icon" />
              <div class="banner-text">
                <span class="banner-title">不登录？继续使用【游客模式】</span>
                <span class="banner-desc">无需账号，所有待办数据安全保存在本地</span>
              </div>
            </div>
            <ChevronRight :size="16" class="banner-arrow" />
          </div>

          <div class="login-footer">
            <span>SQLite 本地隔离 ｜ 点击上方“去注册账号”切换卡片背面</span>
          </div>
        </div>

        <!-- BACK FACE: REGISTER CARD -->
        <div class="card-face card-back shadow-2xl">
          <!-- Close Button -->
          <button class="close-btn" @click="handleClose" title="关闭"><X :size="16" /></button>

          <!-- Header -->
          <div class="login-header">
            <div class="brand-logo register-brand">
              <UserPlus :size="32" class="logo-icon" />
            </div>
            <h1 class="brand-title">创建新账号</h1>
            <p class="brand-subtitle">注册 Todo Agent 体验云端同步与多端联动</p>
          </div>

          <!-- Mode Title & Flip Action Header -->
          <div class="card-mode-bar">
            <span class="mode-tag register-tag"><UserPlus :size="15" /> 账号注册</span>
            <button type="button" class="flip-trigger-btn" @click="toggleFlip">
              <span>返回登录</span> <Repeat :size="13" />
            </button>
          </div>

          <!-- Register Form -->
          <form class="login-form" @submit.prevent="handleRegister">
            <div class="form-group">
              <label class="input-label">注册用户名</label>
              <div class="input-wrapper">
                <User :size="16" class="field-icon" />
                <input
                  type="text"
                  v-model="registerUsername"
                  placeholder="设置您的用户名"
                  class="form-input"
                  required
                />
              </div>
            </div>

            <div class="form-group">
              <label class="input-label">设置密码</label>
              <div class="input-wrapper">
                <Lock :size="16" class="field-icon" />
                <input
                  type="password"
                  v-model="registerPassword"
                  placeholder="设置登录密码"
                  class="form-input"
                  required
                />
              </div>
            </div>

            <div class="form-group">
              <label class="input-label">确认密码</label>
              <div class="input-wrapper">
                <Lock :size="16" class="field-icon" />
                <input
                  type="password"
                  v-model="registerPasswordConfirm"
                  placeholder="请再次输入密码"
                  class="form-input"
                  required
                />
              </div>
            </div>

            <div v-if="errorMessage && isFlipped" class="error-tip-alert">
              {{ errorMessage }}
            </div>
            <div v-if="successMessage && isFlipped" class="success-tip-alert">
              {{ successMessage }}
            </div>

            <button type="submit" class="submit-btn register-theme" :disabled="loading">
              <span v-if="loading" class="spinner-sm"></span>
              <UserPlus v-else :size="16" />
              <span>{{ loading ? '注册中...' : '注册并登录' }}</span>
            </button>
          </form>

          <!-- Guest Mode Quick Entry -->
          <div class="local-mode-banner" @click="handleUseLocalMode" title="以游客身份使用全部本地功能">
            <div class="banner-left">
              <Home :size="18" class="banner-icon" />
              <div class="banner-text">
                <span class="banner-title">跳过注册？使用【游客模式】</span>
                <span class="banner-desc">随时可以在系统界面中注册并升级离线数据</span>
              </div>
            </div>
            <ChevronRight :size="16" class="banner-arrow" />
          </div>

          <div class="login-footer">
            <span>SQLite 本地隔离 ｜ 点击上方“返回登录”翻转至登录卡片</span>
          </div>
        </div>

      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { CheckSquare, LogIn, UserPlus, Lock, User, Home, ChevronRight, Repeat, X } from 'lucide-vue-next'
import type { User as UserType } from '../../types'

const emit = defineEmits<{
  (e: 'loginSuccess', user: UserType): void
  (e: 'useLocalMode'): void
  (e: 'close'): void
}>()

const isFlipped = ref(false)
const loading = ref(false)

const loginUsername = ref('')
const loginPassword = ref('')

const registerUsername = ref('')
const registerPassword = ref('')
const registerPasswordConfirm = ref('')

const errorMessage = ref('')
const successMessage = ref('')

function toggleFlip() {
  isFlipped.value = !isFlipped.value
  errorMessage.value = ''
  successMessage.value = ''
}

async function tauriInvoke<T>(cmd: string, args: Record<string, any> = {}): Promise<T> {
  try {
    const { invoke } = await import('@tauri-apps/api/core')
    return await invoke<T>(cmd, args)
  } catch (e: any) {
    console.warn(`[Tauri Auth Fallback] ${cmd}`, args, e)
    // Web fallback implementation for browser dev testing
    if (cmd === 'register_user') {
      const usersRaw = localStorage.getItem('web_users') || '[]'
      const users = JSON.parse(usersRaw)
      if (users.find((u: any) => u.username === args.username)) {
        throw new Error('该用户名已被注册，请翻转回登录页尝试登录')
      }
      const newUser: UserType = {
        id: Date.now(),
        username: args.username,
        created_at: new Date().toISOString()
      }
      users.push({ ...newUser, password: args.password })
      localStorage.setItem('web_users', JSON.stringify(users))
      return newUser as T
    }
    if (cmd === 'login_user') {
      const usersRaw = localStorage.getItem('web_users') || '[]'
      const users = JSON.parse(usersRaw)
      const found = users.find((u: any) => u.username === args.username)
      if (!found) throw new Error('用户不存在，请点击卡片右上角注册新账号')
      if (found.password !== args.password) throw new Error('密码不正确，请重新输入')
      return { id: found.id, username: found.username, created_at: found.created_at } as T
    }
    throw e
  }
}

async function handleLogin() {
  errorMessage.value = ''
  successMessage.value = ''
  if (!loginUsername.value.trim() || !loginPassword.value) {
    errorMessage.value = '请输入完整的用户名和密码'
    return
  }

  loading.value = true
  try {
    const user = await tauriInvoke<UserType>('login_user', {
      username: loginUsername.value.trim(),
      password: loginPassword.value
    })
    successMessage.value = `🎉 登录成功，欢迎回来，${user.username}！`
    setTimeout(() => {
      emit('loginSuccess', user)
    }, 400)
  } catch (err: any) {
    errorMessage.value = `❌ ${err?.message || err}`
  } finally {
    loading.value = false
  }
}

async function handleRegister() {
  errorMessage.value = ''
  successMessage.value = ''

  if (!registerUsername.value.trim()) {
    errorMessage.value = '请输入注册用户名'
    return
  }
  if (registerPassword.value.length < 3) {
    errorMessage.value = '密码长度不能小于 3 位'
    return
  }
  if (registerPassword.value !== registerPasswordConfirm.value) {
    errorMessage.value = '两次输入的密码不一致'
    return
  }

  loading.value = true
  try {
    const user = await tauriInvoke<UserType>('register_user', {
      username: registerUsername.value.trim(),
      password: registerPassword.value
    })
    successMessage.value = `✨ 注册成功！已为您自动登录 [${user.username}]`
    setTimeout(() => {
      emit('loginSuccess', user)
    }, 400)
  } catch (err: any) {
    errorMessage.value = `❌ ${err?.message || err}`
  } finally {
    loading.value = false
  }
}

function handleUseLocalMode() {
  emit('useLocalMode')
}

function handleClose() {
  emit('close')
}
</script>

<style scoped>
.login-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(15, 23, 42, 0.75);
  backdrop-filter: blur(10px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

/* 3D Container & Perspective */
.card-perspective {
  perspective: 1200px;
  width: 440px;
  max-width: 92vw;
  min-height: 580px;
}

.flip-card-inner {
  position: relative;
  width: 100%;
  height: 100%;
  transition: transform 0.65s cubic-bezier(0.4, 0.2, 0.2, 1);
  transform-style: preserve-3d;
}

.flip-card-inner.is-flipped {
  transform: rotateY(180deg);
}

/* Card Front & Back Styling */
.card-face {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  backface-visibility: hidden;
  -webkit-backface-visibility: hidden;
  background-color: var(--bg-card, #ffffff);
  border: 1px solid var(--border-color, #e2e8f0);
  border-radius: 20px;
  padding: 28px 30px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
  box-sizing: border-box;
}

.card-front {
  transform: rotateY(0deg);
  z-index: 2;
}

.card-back {
  transform: rotateY(180deg);
}

.close-btn {
  position: absolute;
  top: 16px;
  right: 16px;
  background: transparent;
  border: none;
  font-size: 16px;
  color: var(--text-muted, #94a3b8);
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 6px;
  transition: all 0.2s;
  z-index: 10;
}

.close-btn:hover {
  background-color: rgba(0, 0, 0, 0.06);
  color: var(--text-main, #0f172a);
}

.login-header {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
}

.brand-logo {
  width: 52px;
  height: 52px;
  border-radius: 14px;
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  color: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 8px;
  box-shadow: 0 8px 16px -4px rgba(59, 130, 246, 0.4);
}

.brand-logo.register-brand {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  box-shadow: 0 8px 16px -4px rgba(16, 185, 129, 0.4);
}

.brand-title {
  font-size: 20px;
  font-weight: 800;
  color: var(--text-main, #0f172a);
  margin: 0;
}

.brand-subtitle {
  font-size: 12px;
  color: var(--text-muted, #64748b);
  margin-top: 2px;
}

/* Card Mode Bar & Flip Switch */
.card-mode-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background-color: var(--bg-app, #f8fafc);
  padding: 6px 12px;
  border-radius: 10px;
  border: 1px solid var(--border-color, #f1f5f9);
}

.mode-tag {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 700;
  color: var(--primary, #3b82f6);
}

.mode-tag.register-tag {
  color: #10b981;
}

.flip-trigger-btn {
  display: flex;
  align-items: center;
  gap: 5px;
  background: transparent;
  border: none;
  color: var(--primary, #3b82f6);
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 6px;
  transition: all 0.2s ease;
}

.flip-trigger-btn:hover {
  background-color: rgba(59, 130, 246, 0.1);
  transform: translateX(2px);
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.input-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-main, #334155);
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
  padding: 9px 12px 9px 36px;
  border-radius: 8px;
  border: 1px solid var(--border-color, #cbd5e1);
  background-color: var(--bg-app, #f8fafc);
  color: var(--text-main, #0f172a);
  font-size: 13px;
  outline: none;
  transition: border-color 0.2s, box-shadow 0.2s;
  box-sizing: border-box;
}

.form-input:focus {
  border-color: var(--primary, #3b82f6);
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.15);
}

.submit-btn {
  width: 100%;
  padding: 11px;
  border-radius: 9px;
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
  transition: all 0.2s ease;
  margin-top: 4px;
}

.submit-btn:hover {
  opacity: 0.92;
  transform: translateY(-1px);
}

.submit-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

.submit-btn.register-theme {
  background-color: #10b981;
}

.local-mode-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 14px;
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(5, 150, 105, 0.05) 100%);
  border: 1px dashed rgba(16, 185, 129, 0.4);
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.local-mode-banner:hover {
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.18) 0%, rgba(5, 150, 105, 0.12) 100%);
  transform: translateY(-1px);
}

.banner-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.banner-icon {
  color: #10b981;
}

.banner-text {
  display: flex;
  flex-direction: column;
}

.banner-title {
  font-size: 12px;
  font-weight: 700;
  color: #059669;
}

.banner-desc {
  font-size: 11px;
  color: var(--text-muted, #64748b);
}

.banner-arrow {
  color: #10b981;
}

.error-tip-alert {
  font-size: 12px;
  color: #ef4444;
  background-color: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.2);
  border-radius: 6px;
  padding: 8px 12px;
}

.success-tip-alert {
  font-size: 12px;
  color: #10b981;
  background-color: rgba(16, 185, 129, 0.1);
  border: 1px solid rgba(16, 185, 129, 0.2);
  border-radius: 6px;
  padding: 8px 12px;
}

.login-footer {
  text-align: center;
  font-size: 11px;
  color: var(--text-muted, #94a3b8);
  margin-top: -4px;
}

.spinner-sm {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>


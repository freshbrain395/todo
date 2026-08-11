<template>
  <div v-if="isOpen" class="modal-backdrop" @click.self="close">
    <div class="modal-card animate-pop">
      <div class="modal-header">
        <h3 class="modal-title">
          <ShieldCheck :size="18" class="icon-admin" /> 管理员面板 - 用户账号与 JSON 配置管理
        </h3>
        <button class="btn-close" @click="close"><X :size="16" /></button>
      </div>

      <div class="modal-body">
        <div class="user-table-container">
          <table class="user-table">
            <thead>
              <tr>
                <th>用户</th>
                <th>账号 ID</th>
                <th>角色</th>
                <th>密码</th>
                <th>JSON 配置项数</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in usersList" :key="item.user.id">
                <td>
                  <div class="user-cell">
                    <div
                      class="avatar-sm"
                      :style="{ backgroundColor: item.user.avatarColor || '#3B82F6' }"
                    >
                      {{ item.user.username.substring(0, 1).toUpperCase() }}
                    </div>
                    <span class="user-name">{{ item.user.username }}</span>
                  </div>
                </td>
                <td class="code-text">{{ item.user.id }}</td>
                <td>
                  <span class="role-badge" :class="item.user.isAdmin ? 'badge-admin' : 'badge-user'">
                    {{ item.user.isAdmin ? '👑 超级管理员' : '👤 普通用户' }}
                  </span>
                </td>
                <td>
                  <span class="password-mask">••••••</span>
                </td>
                <td>
                  <span class="config-count-badge">
                    <FileJson :size="12" /> {{ Object.keys(item.config).length }} 项
                  </span>
                </td>
                <td>
                  <div class="action-btns">
                    <button
                      class="btn-action edit-btn"
                      title="重置用户密码"
                      @click="openResetPasswordModal(item.user)"
                    >
                      <Key :size="13" /> 重置密码
                    </button>
                    <button
                      v-if="!item.user.isAdmin"
                      class="btn-action del-btn"
                      title="删除该用户及其 JSON 配置"
                      @click="handleDeleteUser(item.user)"
                    >
                      <Trash2 :size="13" /> 删除
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- 内部弹窗：重置密码 -->
        <div v-if="resetTargetUser" class="sub-modal-backdrop" @click.self="resetTargetUser = null">
          <div class="sub-modal-card">
            <h4>重置密码: {{ resetTargetUser.username }}</h4>
            <div class="form-group">
              <label>请输入新密码：</label>
              <input
                type="text"
                v-model="newPasswordInput"
                placeholder="请输入新密码"
                class="text-input"
              />
            </div>
            <div class="sub-modal-actions">
              <button class="btn btn-secondary" @click="resetTargetUser = null">取消</button>
              <button class="btn btn-primary" @click="confirmResetPassword">确认修改</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ShieldCheck, X, FileJson, Key, Trash2 } from 'lucide-vue-next'
import { showConfirm } from '../../utils/confirmState'
import {
  getAllUserAccountsMap,
  resetUserPassword,
  deleteUserAccount,
  type UserAccountData,
  type UserProfile
} from '../../utils/configManager'

defineProps<{
  isOpen: boolean
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'refresh'): void
}>()

const usersMap = ref<Record<string, UserAccountData>>(getAllUserAccountsMap())
const usersList = computed(() => Object.values(usersMap.value))

const resetTargetUser = ref<UserProfile | null>(null)
const newPasswordInput = ref('')

function refresh() {
  usersMap.value = getAllUserAccountsMap()
  emit('refresh')
}

function close() {
  emit('close')
}

function openResetPasswordModal(user: UserProfile) {
  resetTargetUser.value = user
  newPasswordInput.value = user.password || '123456'
}

function confirmResetPassword() {
  if (!resetTargetUser.value) return
  if (!newPasswordInput.value.trim()) return
  resetUserPassword(resetTargetUser.value.id, newPasswordInput.value.trim())
  resetTargetUser.value = null
  refresh()
}

async function handleDeleteUser(user: UserProfile) {
  const confirmed = await showConfirm({
    title: '删除用户账号',
    message: `确定要删除用户 "${user.username}" 及其独立 JSON 配置文件吗？`,
    detail: '删除后该账号的所有偏好与 JSON 配置将彻底抹除，且不可恢复。',
    confirmText: '彻底删除',
    cancelText: '取消',
    type: 'danger'
  })

  if (!confirmed) return
  deleteUserAccount(user.id)
  refresh()
}
</script>

<style scoped>
.modal-backdrop {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-card {
  width: 760px;
  max-width: 92vw;
  background-color: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.2);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border-color);
  background-color: var(--bg-app);
}

.modal-title {
  font-size: 15px;
  font-weight: 700;
  color: var(--text-main);
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0;
}

.icon-admin {
  color: var(--primary);
}

.btn-close {
  background: none;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
}

.modal-body {
  padding: 20px;
  position: relative;
}

.user-table-container {
  max-height: 380px;
  overflow-y: auto;
  border: 1px solid var(--border-color);
  border-radius: 8px;
}

.user-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
  text-align: left;
}

.user-table th, .user-table td {
  padding: 12px 14px;
  border-bottom: 1px solid var(--border-color);
}

.user-table th {
  background-color: var(--bg-app);
  color: var(--text-muted);
  font-weight: 600;
}

.user-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.avatar-sm {
  width: 26px;
  height: 26px;
  border-radius: 50%;
  color: #fff;
  font-size: 12px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
}

.user-name {
  font-weight: 600;
  color: var(--text-main);
}

.code-text {
  font-family: monospace;
  font-size: 11px;
  color: var(--text-muted);
}

.role-badge {
  font-size: 11px;
  padding: 3px 8px;
  border-radius: 12px;
  font-weight: 600;
}

.badge-admin {
  background-color: rgba(59, 130, 246, 0.12);
  color: #3b82f6;
}

.badge-user {
  background-color: rgba(100, 116, 139, 0.12);
  color: #64748b;
}

.password-mask {
  font-family: monospace;
  letter-spacing: 2px;
  color: var(--text-muted);
}

.config-count-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  color: var(--text-muted);
}

.action-btns {
  display: flex;
  gap: 6px;
}

.btn-action {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  padding: 4px 8px;
  border-radius: 4px;
  cursor: pointer;
  border: 1px solid var(--border-color);
  background-color: var(--bg-app);

  color: var(--text-main);
}

.btn-action:hover {
  border-color: var(--primary);
}

.del-btn {
  color: #ef4444;
  border-color: rgba(239, 68, 68, 0.3);
}

.del-btn:hover {
  background-color: rgba(239, 68, 68, 0.1);
}

.sub-modal-backdrop {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
}

.sub-modal-card {
  width: 320px;
  background-color: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 10px;
  padding: 18px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.sub-modal-card h4 {
  margin: 0;
  font-size: 14px;
  color: var(--text-main);
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-group label {
  font-size: 12px;
  color: var(--text-muted);
}

.text-input {
  padding: 6px 10px;
  border-radius: 6px;
  border: 1px solid var(--border-color);
  background-color: var(--bg-app);
  color: var(--text-main);
  font-size: 12px;
}

.sub-modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;

}

.btn {
  padding: 6px 12px;
  border-radius: 6px;
  font-size: 12px;
  cursor: pointer;
  border: none;
}

.btn-secondary {
  background-color: var(--bg-app);
  color: var(--text-main);
  border: 1px solid var(--border-color);
}

.btn-primary {
  background-color: var(--primary);
  color: #fff;
}
</style>

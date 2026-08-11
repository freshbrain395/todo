<template>
  <div v-if="isOpen" class="modal-backdrop" @click.self="close">
    <div class="modal-card animate-pop">
      <div class="modal-header">
        <h3 class="modal-title"><Users :size="18" /> 切换 / 管理多用户配置 (JSON 保存)</h3>
        <button class="btn-close" @click="close"><X :size="16" /></button>
      </div>

      <div class="modal-body">
        <div class="user-list-section">
          <label class="section-label">当前设备中的用户账号：</label>
          <div class="user-grid">
            <div
              v-for="item in usersList"
              :key="item.user.id"
              class="user-card"
              :class="{ active: item.user.id === currentUserId }"
              @click="switchUser(item.user.id)"
            >
              <div class="user-avatar">
                <User :size="20" />
              </div>
              <div class="user-info">
                <span class="user-name">{{ item.user.username }}</span>
                <span class="user-tag">{{ item.user.id === currentUserId ? '当前使用中' : '独立 JSON 配置' }}</span>
              </div>
              <CheckCircle2 v-if="item.user.id === currentUserId" class="check-icon" :size="18" />
            </div>
          </div>
        </div>

        <div class="create-user-section">
          <label class="section-label">新增用户账号：</label>
          <div class="create-form">
            <input
              type="text"
              v-model="newUsername"
              placeholder="请输入新用户名"
              class="text-input"
              @keyup.enter="handleCreateUser"
            />
            <button class="btn btn-primary" :disabled="!newUsername.trim()" @click="handleCreateUser">
              <UserPlus :size="14" /> 创建用户
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { Users, User, UserPlus, X, CheckCircle2 } from 'lucide-vue-next'
import {
  getAllUserAccountsMap,
  getCurrentUserId,
  setCurrentUserId,
  createNewUser,
  type UserAccountData
} from '../../utils/configManager'

defineProps<{
  isOpen: boolean
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'userSwitched'): void
}>()

const newUsername = ref('')

const usersMap = ref<Record<string, UserAccountData>>(getAllUserAccountsMap())
const currentUserId = ref(getCurrentUserId())

const usersList = computed(() => Object.values(usersMap.value))

function refreshUsers() {
  usersMap.value = getAllUserAccountsMap()
  currentUserId.value = getCurrentUserId()
}

function close() {
  emit('close')
}

function switchUser(userId: string) {
  setCurrentUserId(userId)
  currentUserId.value = userId
  emit('userSwitched')
  close()
}

function handleCreateUser() {
  if (!newUsername.value.trim()) return
  const newUser = createNewUser(newUsername.value.trim())
  newUsername.value = ''
  refreshUsers()
  switchUser(newUser.id)
}
</script>

<style scoped>
.modal-backdrop {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.45);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 999;
}

.modal-card {
  width: 480px;
  max-width: 90vw;
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
  font-weight: 600;
  color: var(--text-main);
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0;
}

.btn-close {
  background: none;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
}

.btn-close:hover {
  color: var(--text-main);
  background-color: rgba(0, 0, 0, 0.05);
}

.modal-body {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.section-label {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-main);
  margin-bottom: 8px;
  display: block;
}

.user-grid {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 200px;
  overflow-y: auto;
}

.user-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 14px;
  border-radius: 8px;
  border: 1px solid var(--border-color);
  background-color: var(--bg-app);
  cursor: pointer;
  transition: all 0.2s ease;
}

.user-card:hover {
  border-color: var(--primary);
  background-color: rgba(var(--primary-rgb, 59, 130, 246), 0.05);
}

.user-card.active {
  border-color: var(--primary);
  background-color: rgba(var(--primary-rgb, 59, 130, 246), 0.1);
}

.user-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background-color: var(--primary);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
}

.user-info {
  display: flex;
  flex-direction: column;
  flex: 1;
}

.user-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-main);
}

.user-tag {
  font-size: 11px;
  color: var(--text-muted);
}

.check-icon {
  color: var(--primary);
}

.create-form {
  display: flex;
  gap: 10px;
}

.text-input {
  flex: 1;
  padding: 8px 12px;
  border-radius: 6px;
  border: 1px solid var(--border-color);
  background-color: var(--bg-app);
  color: var(--text-main);
  font-size: 13px;
}

.btn-primary {
  background-color: var(--primary);
  color: #fff;
  border: none;
  border-radius: 6px;
  padding: 8px 14px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>

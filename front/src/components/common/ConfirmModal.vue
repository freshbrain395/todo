<template>
  <Teleport to="body">
    <Transition name="modal-fade">
      <div
        v-if="activeIsOpen"
        class="confirm-modal-overlay"
        @click.self="onBackdropClick"
        tabindex="-1"
        @keydown.esc="handleCancel"
        @keydown.enter="handleConfirm"
        ref="modalOverlayRef"
      >
        <div class="confirm-modal-box" :class="activeType">
          <!-- Close Icon Button -->
          <button class="modal-close-btn" @click="handleCancel" title="关闭窗口">
            <X :size="16" />
          </button>

          <div class="confirm-modal-body">
            <!-- Icon Badge -->
            <div class="confirm-icon-wrapper" :class="activeType">
              <Trash2 v-if="activeType === 'danger'" :size="24" class="icon-danger" />
              <AlertTriangle v-else-if="activeType === 'warning'" :size="24" class="icon-warning" />
              <Info v-else :size="24" class="icon-info" />
            </div>

            <!-- Text Contents -->
            <div class="confirm-text-area">
              <h3 class="confirm-title">{{ activeTitle }}</h3>
              <p class="confirm-message">{{ activeMessage }}</p>
              <p v-if="activeDetail" class="confirm-detail">{{ activeDetail }}</p>
            </div>
          </div>

          <!-- Action Buttons Footer -->
          <div class="confirm-modal-footer">
            <button class="btn btn-cancel" @click="handleCancel">
              {{ activeCancelText }}
            </button>
            <button
              class="btn btn-confirm"
              :class="activeType"
              @click="handleConfirm"
              ref="confirmBtnRef"
            >
              <Trash2 v-if="activeType === 'danger'" :size="14" />
              <span>{{ activeConfirmText }}</span>
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { computed, watch, nextTick, ref, onMounted, onUnmounted } from 'vue'
import { Trash2, AlertTriangle, Info, X } from 'lucide-vue-next'
import { confirmState, closeConfirm } from '../../utils/confirmState'

const props = defineProps<{
  isOpen?: boolean
  title?: string
  message?: string
  detail?: string
  confirmText?: string
  cancelText?: string
  type?: 'danger' | 'warning' | 'info'
}>()

const emit = defineEmits<{
  (e: 'confirm'): void
  (e: 'cancel'): void
  (e: 'update:isOpen', val: boolean): void
}>()

const modalOverlayRef = ref<HTMLElement | null>(null)
const confirmBtnRef = ref<HTMLButtonElement | null>(null)

// Direct Props vs Global State Fallback
const activeIsOpen = computed(() => confirmState.value.isOpen || props.isOpen)
const activeTitle = computed(() => props.title || confirmState.value.title)
const activeMessage = computed(() => props.message || confirmState.value.message)
const activeDetail = computed(() => props.detail || confirmState.value.detail)
const activeConfirmText = computed(() => props.confirmText || confirmState.value.confirmText)
const activeCancelText = computed(() => props.cancelText || confirmState.value.cancelText)
const activeType = computed(() => props.type || confirmState.value.type)

function handleConfirm() {
  if (confirmState.value.isOpen) {
    closeConfirm(true)
  } else {
    emit('confirm')
    emit('update:isOpen', false)
  }
}

function handleCancel() {
  if (confirmState.value.isOpen) {
    closeConfirm(false)
  } else {
    emit('cancel')
    emit('update:isOpen', false)
  }
}

function onBackdropClick() {
  handleCancel()
}

function onGlobalKeyDown(e: KeyboardEvent) {
  if (!activeIsOpen.value) return
  if (e.key === 'Escape') {
    e.preventDefault()
    handleCancel()
  }
}

watch(activeIsOpen, (val) => {
  if (val) {
    nextTick(() => {
      confirmBtnRef.value?.focus()
    })
  }
})

onMounted(() => {
  window.addEventListener('keydown', onGlobalKeyDown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', onGlobalKeyDown)
})
</script>

<style scoped>
.confirm-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background-color: rgba(15, 23, 42, 0.55);
  backdrop-filter: blur(6px);
  -webkit-backdrop-filter: blur(6px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 99999;
  padding: 20px;
}

.confirm-modal-box {
  position: relative;
  width: 100%;
  max-width: 420px;
  background-color: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 16px;
  box-shadow: 0 20px 40px -10px rgba(0, 0, 0, 0.25), 0 0 0 1px rgba(255, 255, 255, 0.05);
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 20px;
  transform-origin: center;
  overflow: hidden;
}

.modal-close-btn {
  position: absolute;
  top: 14px;
  right: 14px;
  background: transparent;
  border: none;
  color: var(--text-muted);
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.15s ease;
}

.modal-close-btn:hover {
  background-color: var(--bg-app);
  color: var(--text-main);
}

.confirm-modal-body {
  display: flex;
  align-items: flex-start;
  gap: 16px;
}

.confirm-icon-wrapper {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.confirm-icon-wrapper.danger {
  background-color: rgba(239, 68, 68, 0.12);
  color: #EF4444;
}

.confirm-icon-wrapper.warning {
  background-color: rgba(245, 158, 11, 0.12);
  color: #F59E0B;
}

.confirm-icon-wrapper.info {
  background-color: rgba(49, 130, 206, 0.12);
  color: var(--primary);
}

.confirm-text-area {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding-right: 16px;
}

.confirm-title {
  font-size: 16px;
  font-weight: 700;
  color: var(--text-main);
  margin: 0;
  line-height: 1.3;
}

.confirm-message {
  font-size: 13.5px;
  color: var(--text-main);
  opacity: 0.9;
  margin: 0;
  line-height: 1.5;
  word-break: break-word;
}

.confirm-detail {
  font-size: 12px;
  color: var(--text-muted);
  margin: 4px 0 0 0;
  line-height: 1.4;
  background-color: var(--bg-app);
  padding: 6px 10px;
  border-radius: 6px;
  border-left: 3px solid var(--border-color);
}

.confirm-modal-footer {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 10px;
  padding-top: 4px;
}

.btn-cancel {
  background-color: var(--bg-app);
  border: 1px solid var(--border-color);
  color: var(--text-main);
  font-weight: 500;
  padding: 8px 16px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.btn-cancel:hover {
  background-color: var(--bg-card-hover);
  border-color: var(--text-muted);
}

.btn-confirm {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-weight: 600;
  padding: 8px 18px;
  border-radius: 8px;
  border: none;
  cursor: pointer;
  transition: all 0.2s ease;
  color: #FFFFFF;
}

.btn-confirm.danger {
  background: linear-gradient(135deg, #EF4444 0%, #DC2626 100%);
  box-shadow: 0 4px 12px rgba(239, 68, 68, 0.3);
}

.btn-confirm.danger:hover {
  background: linear-gradient(135deg, #DC2626 0%, #B91C1C 100%);
  box-shadow: 0 6px 16px rgba(239, 68, 68, 0.45);
  transform: translateY(-1px);
}

.btn-confirm.warning {
  background: linear-gradient(135deg, #F59E0B 0%, #D97706 100%);
  box-shadow: 0 4px 12px rgba(245, 158, 11, 0.3);
}

.btn-confirm.warning:hover {
  background: linear-gradient(135deg, #D97706 0%, #B45309 100%);
  box-shadow: 0 6px 16px rgba(245, 158, 11, 0.45);
  transform: translateY(-1px);
}

.btn-confirm.info {
  background-color: var(--primary);
  box-shadow: 0 4px 12px rgba(49, 130, 206, 0.3);
}

.btn-confirm.info:hover {
  background-color: var(--primary-hover);
  transform: translateY(-1px);
}

/* Modal Transition Animation */
.modal-fade-enter-active,
.modal-fade-leave-active {
  transition: opacity 0.22s ease;
}

.modal-fade-enter-from,
.modal-fade-leave-to {
  opacity: 0;
}

.modal-fade-enter-active .confirm-modal-box {
  animation: modalPop 0.25s cubic-bezier(0.16, 1, 0.3, 1) forwards;
}

.modal-fade-leave-active .confirm-modal-box {
  animation: modalPop 0.2s cubic-bezier(0.16, 1, 0.3, 1) reverse forwards;
}

@keyframes modalPop {
  0% {
    opacity: 0;
    transform: scale(0.92) translateY(10px);
  }
  100% {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}
</style>

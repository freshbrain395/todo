<template>
  <div v-if="visible && commands.length > 0" class="slash-command-menu" ref="menuRef">
    <div class="slash-menu-header">
      <span class="slash-title">⚡ 快捷指令菜单</span>
      <span class="slash-tip">↑↓ 选择 · Enter/Tab 确认 · Esc 关闭</span>
    </div>
    <ul class="slash-menu-list">
      <li
        v-for="(cmd, index) in commands"
        :key="cmd.id"
        class="slash-menu-item"
        :class="{ active: index === selectedIndex }"
        @click="$emit('select', cmd)"
        @mouseenter="$emit('update:selectedIndex', index)"
      >
        <span class="cmd-icon">{{ cmd.icon || '⚡' }}</span>
        <div class="cmd-info">
          <div class="cmd-key-row">
            <span class="cmd-key">{{ cmd.key }}</span>
            <span class="cmd-label">{{ cmd.label }}</span>
          </div>
          <span class="cmd-desc">{{ cmd.description }}</span>
        </div>
      </li>
    </ul>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, nextTick } from 'vue'
import type { SlashCommand } from './slashCommands'

const props = defineProps<{
  visible: boolean
  selectedIndex: number
  commands: SlashCommand[]
}>()

defineEmits<{
  (e: 'select', cmd: SlashCommand): void
  (e: 'update:selectedIndex', index: number): void
}>()

const menuRef = ref<HTMLElement | null>(null)

watch(() => props.selectedIndex, () => {
  nextTick(() => {
    if (!menuRef.value) return
    const activeEl = menuRef.value.querySelector('.slash-menu-item.active') as HTMLElement
    if (activeEl) {
      activeEl.scrollIntoView({ block: 'nearest', behavior: 'smooth' })
    }
  })
})
</script>

<style scoped>
.slash-command-menu {
  position: absolute;
  bottom: calc(100% + 8px);
  left: 0;
  right: 0;
  max-height: 260px;
  background: var(--bg-surface, #ffffff);
  border: 1px solid var(--border-color, #e2e8f0);
  border-radius: 12px;
  box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.15), 0 8px 10px -6px rgba(0, 0, 0, 0.1);
  z-index: 999;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  animation: slashMenuFadeIn 0.15s ease-out;
}

@keyframes slashMenuFadeIn {
  from {
    opacity: 0;
    transform: translateY(6px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.slash-menu-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 14px;
  background: rgba(0, 0, 0, 0.03);
  border-bottom: 1px solid var(--border-color, #e2e8f0);
  font-size: 11px;
  color: var(--text-muted, #64748b);
  user-select: none;
}

.slash-title {
  font-weight: 600;
  color: var(--primary-color, #3b82f6);
}

.slash-tip {
  font-size: 10px;
  opacity: 0.8;
}

.slash-menu-list {
  list-style: none;
  margin: 0;
  padding: 4px;
  overflow-y: auto;
  max-height: 210px;
}

.slash-menu-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: background-color 0.12s ease;
}

.slash-menu-item:hover,
.slash-menu-item.active {
  background-color: var(--hover-bg, rgba(59, 130, 246, 0.12));
}

.slash-menu-item.active {
  border-left: 3px solid var(--primary-color, #3b82f6);
}

.cmd-icon {
  font-size: 16px;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.04);
  border-radius: 6px;
  flex-shrink: 0;
}

.cmd-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  overflow: hidden;
}

.cmd-key-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.cmd-key {
  font-weight: 700;
  font-family: monospace;
  font-size: 13px;
  color: var(--primary-color, #2563eb);
}

.cmd-label {
  font-weight: 600;
  font-size: 13px;
  color: var(--text-primary, #1e293b);
}

.cmd-desc {
  font-size: 11px;
  color: var(--text-muted, #64748b);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
</style>

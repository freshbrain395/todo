<template>
  <div class="settings-section-card">
    <div class="section-card-header">
      <div class="header-left">
        <Wrench :size="20" class="section-icon" />
        <h4>🛠️ Agent Tools 函数工具箱选择与控制</h4>
      </div>
      <div class="tools-header-actions">
        <button class="btn btn-xs btn-outline" @click="$emit('enable-all')">全部开启</button>
        <button class="btn btn-xs btn-outline" @click="$emit('disable-all')">全部关闭</button>
        <button class="btn btn-xs btn-outline" @click="$emit('reset-default')">重置默认</button>
      </div>
    </div>

    <p class="section-desc">在此勾选开启或关闭 AI Agent 可调用的底层 SQLite 及系统底层控制函数。</p>

    <div class="tools-settings-list">
      <div
        v-for="tool in agentTools"
        :key="tool.id"
        class="tool-setting-row"
        :class="{ disabled: !tool.enabled }"
      >
        <div class="tool-left-info">
          <label class="checkbox-container">
            <input
              type="checkbox"
              v-model="tool.enabled"
              @change="$emit('save-tools')"
            />
            <span class="checkmark"></span>
          </label>
          <div class="tool-icon-badge" :class="[tool.category, { active: tool.enabled }]">
            <component :is="tool.icon" :size="16" />
          </div>
          <div class="tool-text-meta">
            <div class="tool-title-line">
              <span class="tool-func-name">{{ tool.id }}</span>
              <span class="tool-label-text">{{ tool.label }}</span>
              <span class="tool-cat-badge" :class="tool.category">{{ tool.categoryText }}</span>
            </div>
            <p class="tool-desc">{{ tool.description }}</p>
          </div>
        </div>

        <div class="tool-right-switch">
          <span class="switch-status" :class="{ active: tool.enabled }">
            {{ tool.enabled ? '已允许 Agent 调度' : '已禁用该工具' }}
          </span>
          <label class="switch-toggle">
            <input
              type="checkbox"
              v-model="tool.enabled"
              @change="$emit('save-tools')"
            />
            <span class="switch-slider"></span>
          </label>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Wrench } from 'lucide-vue-next'

interface AgentToolItem {
  id: string
  label: string
  category: string
  categoryText: string
  description: string
  enabled: boolean
  icon: any
}

defineProps<{
  agentTools: AgentToolItem[]
}>()

defineEmits<{
  (e: 'enable-all'): void
  (e: 'disable-all'): void
  (e: 'reset-default'): void
  (e: 'save-tools'): void
}>()
</script>

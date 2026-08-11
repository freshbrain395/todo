<template>
  <div class="settings-section-card">
    <div class="section-card-header">
      <div class="header-left">
        <Sparkles :size="20" class="section-icon" />
        <h4>💬 Prompts 提示词库管理与生效选择</h4>
      </div>
      <button class="btn btn-xs btn-outline" @click="$emit('add-new-prompt')">
        <Plus :size="13" /> 新建 Prompt
      </button>
    </div>

    <p class="section-desc">编辑并勾选当前预设生效的 Prompt，大模型在分析与处理意图时将优先载入对应场景规范。</p>

    <div class="prompts-settings-grid">
      <div
        v-for="item in promptLibrary"
        :key="item.id"
        class="prompt-setting-card"
        :class="{ active: activePromptId === item.id }"
      >
        <!-- Edit mode inside card -->
        <div v-if="editingPromptId === item.id" class="card-edit-form">
          <div class="edit-row">
            <input v-model="editForm.category" class="edit-input-sm" placeholder="分类标签" />
            <input v-model="editForm.title" class="edit-input-title" placeholder="Prompt 标题" />
          </div>
          <textarea v-model="editForm.text" class="edit-textarea" rows="3" placeholder="Prompt 指令正文"></textarea>
          <textarea v-model="editForm.jsonFormat" class="edit-textarea" style="font-family: monospace; background: #2a2a2a; color: #a6e22e; margin-top: 6px;" rows="3" placeholder="可选: JSON 强制输出格式规范 (如: {&quot;result&quot;: []})"></textarea>
          <div class="edit-actions">
            <button class="btn btn-xs btn-primary" @click="$emit('save-edit-prompt', item.id)">保存修改</button>
            <button class="btn btn-xs btn-outline" @click="$emit('cancel-edit-prompt')">取消</button>
          </div>
        </div>

        <!-- Normal view mode inside card -->
        <div v-else class="card-view-content">
          <div class="card-top-row">
            <div class="badge-group">
              <span class="badge-cat">{{ item.category }}</span>
              <span v-if="activePromptId === item.id" class="badge-active-tag">🎯 当前生效预设</span>
            </div>
            <div class="card-btn-group">
              <button
                class="btn-icon-action"
                :class="{ 'is-selected': activePromptId === item.id }"
                @click="$emit('update:activePromptId', item.id)"
                title="设为当前生效 Prompt"
              >
                <Check :size="14" />
              </button>
              <button class="btn-icon-action" @click="$emit('start-edit-prompt', item)" title="编辑该 Prompt">
                <Edit3 :size="14" />
              </button>
              <button class="btn-icon-action danger" @click="$emit('delete-prompt', item.id)" title="删除该 Prompt">
                <Trash2 :size="14" />
              </button>
            </div>
          </div>

          <h5 class="card-prompt-title" @click="$emit('update:activePromptId', item.id)">{{ item.title }}</h5>
          <p class="card-prompt-text">{{ item.text }}</p>
          <div v-if="item.jsonFormat" class="card-prompt-json" style="margin-top: 8px; padding: 6px; background: #f0f0f0; border-radius: 4px;">
            <span style="font-size: 11px; color: #888; font-weight: bold;">[JSON 输出格式规范]</span>
            <pre style="margin: 4px 0 0 0; font-size: 11px; color: #333; font-family: monospace; white-space: pre-wrap;"><code>{{ item.jsonFormat }}</code></pre>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Sparkles, Plus, Check, Edit3, Trash2 } from 'lucide-vue-next'

interface PromptItem {
  id: string
  title: string
  category: string
  text: string
  jsonFormat?: string
}

defineProps<{
  promptLibrary: PromptItem[]
  activePromptId: string
  editingPromptId: string | null
  editForm: { title: string; category: string; text: string; jsonFormat: string }
}>()

defineEmits<{
  (e: 'update:activePromptId', id: string): void
  (e: 'add-new-prompt'): void
  (e: 'start-edit-prompt', item: PromptItem): void
  (e: 'save-edit-prompt', id: string): void
  (e: 'cancel-edit-prompt'): void
  (e: 'delete-prompt', id: string): void
}>()
</script>

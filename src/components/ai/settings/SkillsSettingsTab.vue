<template>
  <div class="settings-section-card">
    <div class="section-card-header">
      <div class="header-left">
        <BookOpen :size="20" class="section-icon" />
        <h4>🧩 Skills 扩展技能库选择与编辑</h4>
      </div>
      <div class="tools-header-actions">
        <button class="btn btn-xs btn-outline" @click="$emit('enable-all')">全部启用</button>
        <button class="btn btn-xs btn-outline" @click="$emit('disable-all')">全部禁用</button>
        <button class="btn btn-xs btn-outline btn-primary-outline" @click="$emit('add-new-skill')">
          <Plus :size="13" /> 添加自定义 Skill
        </button>
      </div>
    </div>

    <p class="section-desc">编辑与开启选择 Agent 拥有的专项处理 Skills，拓展智能体在专业任务场景下的思考深度。</p>

    <div class="skills-settings-grid">
      <div
        v-for="skill in skillsLibrary"
        :key="skill.id"
        class="skill-setting-card"
        :class="{ disabled: !skill.enabled }"
      >
        <!-- Edit mode inside Skill Card -->
        <div v-if="editingSkillId === skill.id" class="card-edit-form">
          <div class="edit-row">
            <input v-model="skillForm.category" class="edit-input-sm" placeholder="分类标签" />
            <input v-model="skillForm.title" class="edit-input-title" placeholder="Skill 名称" />
          </div>
          <textarea v-model="skillForm.description" class="edit-textarea" rows="2" placeholder="技能功能描述"></textarea>
          <textarea v-model="skillForm.systemPrompt" class="edit-textarea" rows="3" placeholder="Skill System Prompt 指令"></textarea>
          <div class="edit-actions">
            <button class="btn btn-xs btn-primary" @click="$emit('save-edit-skill', skill.id)">保存 Skill</button>
            <button class="btn btn-xs btn-outline" @click="$emit('cancel-edit-skill')">取消</button>
          </div>
        </div>

        <!-- Normal view mode inside Skill Card -->
        <div v-else class="skill-card-body">
          <div class="skill-card-header">
            <div class="skill-title-left">
              <label class="checkbox-container" title="勾选启用/禁用该技能">
                <input
                  type="checkbox"
                  v-model="skill.enabled"
                  @change="$emit('save-skills')"
                />
                <span class="checkmark"></span>
              </label>
              <span class="skill-cat-badge">{{ skill.category }}</span>
              <h5 class="skill-name">{{ skill.title }}</h5>
            </div>

            <div class="skill-actions">
              <button class="btn-icon-action" @click="$emit('start-edit-skill', skill)" title="编辑技能">
                <Edit3 :size="14" />
              </button>
              <button class="btn-icon-action danger" @click="$emit('delete-skill', skill.id)" title="删除技能">
                <Trash2 :size="14" />
              </button>
            </div>
          </div>

          <p class="skill-desc">{{ skill.description }}</p>
          <div class="skill-prompt-preview">
            <span class="preview-label">System Prompt:</span>
            <span class="preview-text">{{ skill.systemPrompt }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { BookOpen, Plus, Edit3, Trash2 } from 'lucide-vue-next'

interface SkillItem {
  id: string
  title: string
  category: string
  description: string
  systemPrompt: string
  enabled: boolean
}

defineProps<{
  skillsLibrary: SkillItem[]
  editingSkillId: string | null
  skillForm: { title: string; category: string; description: string; systemPrompt: string }
}>()

defineEmits<{
  (e: 'enable-all'): void
  (e: 'disable-all'): void
  (e: 'add-new-skill'): void
  (e: 'start-edit-skill', skill: SkillItem): void
  (e: 'save-edit-skill', id: string): void
  (e: 'cancel-edit-skill'): void
  (e: 'delete-skill', id: string): void
  (e: 'save-skills'): void
}>()
</script>

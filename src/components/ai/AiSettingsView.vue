<!-- src/components/ai/AiSettingsView.vue -->
<template>
  <div class="ai-settings-view">
    <!-- Sub Tabs Navigation (if activeTab is set to 'all' or default) -->
    <div v-if="showNavigation" class="ai-settings-sub-tabs">
      <button
        class="sub-tab-btn"
        :class="{ active: currentTab === 'llm' }"
        @click="currentTab = 'llm'"
      >
        <Brain :size="14" /> <span>模型设置</span>
      </button>
      <button
        class="sub-tab-btn"
        :class="{ active: currentTab === 'prompts' }"
        @click="currentTab = 'prompts'"
      >
        <Sparkles :size="14" /> <span>Prompt 提示词库</span>
      </button>
      <button
        class="sub-tab-btn"
        :class="{ active: currentTab === 'tools' }"
        @click="currentTab = 'tools'"
      >
        <Wrench :size="14" /> <span>Agent 工具链</span>
      </button>
      <button
        class="sub-tab-btn"
        :class="{ active: currentTab === 'skills' }"
        @click="currentTab = 'skills'"
      >
        <BookOpen :size="14" /> <span>Skills 技能库</span>
      </button>
    </div>

    <!-- Content Sections -->
    <div class="ai-settings-content">
      <!-- 1. LLM Settings Tab -->
      <div v-if="currentTab === 'llm'" class="settings-section">
        <div class="section-title-bar">
          <h4 style="margin: 0; display: flex; align-items: center; gap: 8px;">
            <Brain :size="20" /> 配置 AI 模型服务商
          </h4>
        </div>

        <div class="providers-grid">
          <div
            v-for="p in savedProviders"
            :key="p.id"
            class="provider-card"
            :class="{ 'is-current': localConfig.provider === p.id }"
            @click="$emit('select-provider', p)"
          >
            <div class="provider-header">
              <div class="header-name-area">
                <Cpu :size="18" class="header-icon" />
                <span class="provider-title-text">{{ p.name }}</span>
              </div>
              <span v-if="localConfig.provider === p.id" class="current-badge">
                <Target :size="13" /> 当前生效
              </span>
            </div>

            <div class="provider-form">
              <!-- Base URL -->
              <div class="field">
                <label class="field-label">接口地址 (Base URL)</label>
                <input
                  v-model="p.base_url"
                  class="form-input"
                  placeholder="https://api..."
                  @change="$emit('update-provider', p)"
                />
              </div>

              <!-- API Key -->
              <div class="field">
                <label class="field-label">API Key</label>
                <input
                  v-model="p.api_key"
                  type="password"
                  class="form-input"
                  placeholder="sk..."
                  @change="$emit('update-provider', p)"
                />
              </div>

              <!-- Model Selector -->
              <div class="field">
                <div class="label-with-actions">
                  <label class="field-label">模型名称 (Model)</label>
                  <div class="model-action-links">
                    <button
                      type="button"
                      class="btn-text-action"
                      :disabled="!!isFetchingModels[p.id]"
                      @click.stop="$emit('fetch-models', p)"
                      title="重新获取在线模型列表"
                    >
                      <RefreshCw :size="12" :class="{ 'spin-icon': !!isFetchingModels[p.id] }" />
                      {{ isFetchingModels[p.id] ? '获取中...' : '自动获取' }}
                    </button>
                    <button
                      type="button"
                      class="btn-text-action"
                      @click.stop="isManualModel[p.id] = !isManualModel[p.id]"
                      :title="isManualModel[p.id] ? '切换为下拉选择' : '切换为手动输入'"
                    >
                      {{ isManualModel[p.id] ? '切换下拉框' : '手动输入' }}
                    </button>
                  </div>
                </div>

                <div v-if="isManualModel[p.id] || !(fetchedModels[p.id] && fetchedModels[p.id].length > 0)" class="input-with-hint">
                  <input
                    v-model="p.model"
                    class="form-input"
                    placeholder="例如: gpt-4o, llama3:latest..."
                    @change="$emit('update-provider', p)"
                  />
                  <div v-if="fetchModelError[p.id]" class="field-hint error-hint">
                    ⚠️ {{ fetchModelError[p.id] }}
                  </div>
                  <div v-else-if="!isFetchingModels[p.id] && !(fetchedModels[p.id] && fetchedModels[p.id].length > 0)" class="field-hint">
                    💡 点击"自动获取"从服务器拉取，或直接手动输入模型标识
                  </div>
                </div>

                <div v-else class="select-search-wrapper">
                  <select
                    :value="p.model"
                    class="form-input"
                    @change="onSelectModel(p, ($event.target as HTMLSelectElement).value)"
                  >
                    <option v-for="m in fetchedModels[p.id]" :key="m.id" :value="m.id">
                      {{ m.id }} {{ m.name && m.name !== m.id ? '(' + m.name + ')' : '' }}
                    </option>
                  </select>
                </div>
              </div>

              <!-- Thinking Mode -->
              <div class="field">
                <label class="field-label">深度思考模式 (Thinking Mode)</label>
                <select
                  :value="localConfig.enable_thinking ? 'true' : 'false'"
                  class="form-input"
                  @change="$emit('update-thinking', ($event.target as HTMLSelectElement).value === 'true')"
                >
                  <option value="false">关闭思考模式 (默认)</option>
                  <option value="true">开启大模型深度思考</option>
                </select>
              </div>
            </div>
          </div>

          <button class="add-provider-card-btn" @click="$emit('add-custom-provider')">
            ➕ 添加新的模型服务商卡片
          </button>
        </div>
      </div>

      <!-- 2. Prompts Settings Tab -->
      <div v-else-if="currentTab === 'prompts'" class="settings-section-card">
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
            <div v-if="editingPromptId === item.id" class="card-edit-form">
              <div class="edit-row">
                <input v-model="editForm.category" class="edit-input-sm" placeholder="分类标签" />
                <input v-model="editForm.title" class="edit-input-title" placeholder="Prompt 标题" />
              </div>
              <textarea v-model="editForm.text" class="edit-textarea" rows="3" placeholder="Prompt 指令正文"></textarea>
              <textarea v-model="editForm.jsonFormat" class="edit-textarea json-textarea" rows="3" placeholder="可选: JSON 格式规范"></textarea>
              <div class="edit-actions">
                <button class="btn btn-xs btn-primary" @click="$emit('save-edit-prompt', item.id)">保存修改</button>
                <button class="btn btn-xs btn-outline" @click="$emit('cancel-edit-prompt')">取消</button>
              </div>
            </div>

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
              <div v-if="item.jsonFormat" class="card-prompt-json">
                <span class="json-label">[JSON 输出格式规范]</span>
                <pre><code>{{ item.jsonFormat }}</code></pre>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 3. Tools Settings Tab -->
      <div v-else-if="currentTab === 'tools'" class="settings-section-card">
        <div class="section-card-header">
          <div class="header-left">
            <Wrench :size="20" class="section-icon" />
            <h4>🛠️ Agent Tools 函数工具箱选择与控制</h4>
          </div>
          <div class="tools-header-actions">
            <button class="btn btn-xs btn-outline" @click="$emit('enable-all-tools')">全部开启</button>
            <button class="btn btn-xs btn-outline" @click="$emit('disable-all-tools')">全部关闭</button>
            <button class="btn btn-xs btn-outline" @click="$emit('reset-default-tools')">重置默认</button>
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
                <input type="checkbox" v-model="tool.enabled" @change="$emit('save-tools')" />
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
                <input type="checkbox" v-model="tool.enabled" @change="$emit('save-tools')" />
                <span class="switch-slider"></span>
              </label>
            </div>
          </div>
        </div>
      </div>

      <!-- 4. Skills Settings Tab -->
      <div v-else-if="currentTab === 'skills'" class="settings-section-card">
        <div class="section-card-header">
          <div class="header-left">
            <BookOpen :size="20" class="section-icon" />
            <h4>🧩 Skills 扩展技能库选择与编辑</h4>
          </div>
          <div class="tools-header-actions">
            <button class="btn btn-xs btn-outline" @click="$emit('enable-all-skills')">全部启用</button>
            <button class="btn btn-xs btn-outline" @click="$emit('disable-all-skills')">全部禁用</button>
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

            <div v-else class="skill-card-body">
              <div class="skill-card-header">
                <div class="skill-title-left">
                  <label class="checkbox-container">
                    <input type="checkbox" v-model="skill.enabled" @change="$emit('save-skills')" />
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
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import {
  Brain, Sparkles, Wrench, BookOpen, Cpu, Target, RefreshCw,
  Plus, Check, Edit3, Trash2
} from 'lucide-vue-next'

export interface CustomLlmProvider {
  id: string
  name: string
  base_url: string
  api_key: string
  model: string
  is_custom: boolean
}

export interface PromptItem {
  id: string
  title: string
  category: string
  text: string
  jsonFormat?: string
}

export interface AgentToolItem {
  id: string
  label: string
  category: string
  categoryText: string
  description: string
  enabled: boolean
  icon: any
}

export interface SkillItem {
  id: string
  title: string
  category: string
  description: string
  systemPrompt: string
  enabled: boolean
}

const props = withDefaults(
  defineProps<{
    savedProviders?: CustomLlmProvider[]
    localConfig?: any
    fetchedModels?: Record<string, { id: string; name: string }[]>
    isFetchingModels?: Record<string, boolean>
    fetchModelError?: Record<string, string>
    promptLibrary?: PromptItem[]
    activePromptId?: string
    editingPromptId?: string | null
    editForm?: { title: string; category: string; text: string; jsonFormat: string }
    agentTools?: AgentToolItem[]
    skillsLibrary?: SkillItem[]
    editingSkillId?: string | null
    skillForm?: { title: string; category: string; description: string; systemPrompt: string }
    activeTab?: 'llm' | 'prompts' | 'tools' | 'skills' | 'all'
    showNavigation?: boolean
  }>(),
  {
    savedProviders: () => [],
    localConfig: () => ({ provider: '', enable_thinking: false }),
    fetchedModels: () => ({}),
    isFetchingModels: () => ({}),
    fetchModelError: () => ({}),
    promptLibrary: () => [],
    activePromptId: '',
    editingPromptId: null,
    editForm: () => ({ title: '', category: '', text: '', jsonFormat: '' }),
    agentTools: () => [],
    skillsLibrary: () => [],
    editingSkillId: null,
    skillForm: () => ({ title: '', category: '', description: '', systemPrompt: '' }),
    activeTab: 'llm',
    showNavigation: false
  }
)

const emit = defineEmits<{
  (e: 'update:activeTab', tab: string): void
  (e: 'update-provider', p: CustomLlmProvider): void
  (e: 'select-provider', p: CustomLlmProvider): void
  (e: 'delete-provider', id: string): void
  (e: 'fetch-models', p: CustomLlmProvider): void
  (e: 'add-custom-provider'): void
  (e: 'update-thinking', val: boolean): void
  (e: 'update:activePromptId', id: string): void
  (e: 'add-new-prompt'): void
  (e: 'start-edit-prompt', item: PromptItem): void
  (e: 'save-edit-prompt', id: string): void
  (e: 'cancel-edit-prompt'): void
  (e: 'delete-prompt', id: string): void
  (e: 'enable-all-tools'): void
  (e: 'disable-all-tools'): void
  (e: 'reset-default-tools'): void
  (e: 'save-tools'): void
  (e: 'enable-all-skills'): void
  (e: 'disable-all-skills'): void
  (e: 'add-new-skill'): void
  (e: 'start-edit-skill', skill: SkillItem): void
  (e: 'save-edit-skill', id: string): void
  (e: 'cancel-edit-skill'): void
  (e: 'delete-skill', id: string): void
  (e: 'save-skills'): void
}>()

const currentTab = ref(props.activeTab === 'all' ? 'llm' : props.activeTab)
const isManualModel = ref<Record<string, boolean>>({})

watch(
  () => props.activeTab,
  (newVal) => {
    if (newVal && newVal !== 'all') {
      currentTab.value = newVal
    }
  }
)

function onSelectModel(p: CustomLlmProvider, modelId: string) {
  p.model = modelId
  emit('update-provider', p)
}
</script>

<style scoped>
.ai-settings-view {
  display: flex;
  flex-direction: column;
  gap: 16px;
  width: 100%;
}

.ai-settings-sub-tabs {
  display: flex;
  gap: 8px;
  border-bottom: 1px solid var(--border-color, #333);
  padding-bottom: 8px;
}

.sub-tab-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  background: transparent;
  border: 1px solid transparent;
  border-radius: 6px;
  color: var(--text-secondary, #888);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}

.sub-tab-btn:hover {
  background: rgba(255, 255, 255, 0.05);
  color: var(--text-main, #fff);
}

.sub-tab-btn.active {
  background: var(--bg-card, #252538);
  border-color: var(--border-color, #333);
  color: var(--primary, #3182ce);
  font-weight: 600;
}

.providers-grid {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.provider-card {
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding: 16px 18px;
  background: var(--bg-surface, #1e1e2e);
  border: 1px solid var(--border-color, #333);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease-in-out;
}

.provider-card:hover {
  border-color: var(--primary, #3182ce);
}

.provider-card.is-current {
  border-color: var(--primary, #3182ce);
  box-shadow: 0 0 15px rgba(49, 130, 206, 0.2);
}

.provider-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 10px;
  border-bottom: 1px solid var(--border-color, #333);
}

.header-name-area {
  display: flex;
  align-items: center;
  gap: 8px;
}

.header-icon {
  color: var(--primary, #3182ce);
}

.provider-title-text {
  font-size: 15px;
  font-weight: bold;
  color: var(--text-main, #fff);
}

.current-badge {
  display: flex;
  align-items: center;
  gap: 4px;
  color: var(--primary, #3182ce);
  font-size: 12px;
  font-weight: bold;
}

.provider-form {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px 16px;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.field-label {
  font-size: 12px;
  font-weight: 700;
}

.label-with-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.model-action-links {
  display: flex;
  align-items: center;
  gap: 8px;
}

.btn-text-action {
  background: transparent;
  border: none;
  color: var(--primary, #3182ce);
  font-size: 11px;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 3px;
  padding: 0;
  opacity: 0.85;
}

.btn-text-action:hover:not(:disabled) {
  opacity: 1;
  text-decoration: underline;
}

.spin-icon {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.form-input {
  width: 100%;
  height: 38px;
  box-sizing: border-box;
  padding: 8px 12px;
  font-size: 13px;
  color: var(--text-main, #fff);
  background: var(--bg-card, #252538);
  border: 1px solid var(--border-color, #333);
  border-radius: 6px;
}

.form-input:focus {
  border-color: var(--primary, #3182ce);
  outline: none;
}

.add-provider-card-btn {
  width: 100%;
  padding: 14px;
  border: 2px dashed var(--border-color, #333);
  border-radius: 8px;
  background: transparent;
  color: var(--text-secondary, #888);
  font-size: 14px;
  font-weight: bold;
  cursor: pointer;
  transition: all 0.2s ease-in-out;
  display: flex;
  align-items: center;
  justify-content: center;
}

.add-provider-card-btn:hover {
  border-color: var(--primary, #3182ce);
  color: var(--primary, #3182ce);
  background: rgba(49, 130, 206, 0.05);
}

.settings-section-card {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.section-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.section-desc {
  font-size: 12px;
  color: var(--text-secondary, #888);
  margin: 0 0 8px 0;
}

.json-textarea {
  font-family: monospace;
  background: #2a2a2a;
  color: #a6e22e;
  margin-top: 6px;
}

.card-prompt-json {
  margin-top: 8px;
  padding: 6px;
  background: #222;
  border-radius: 4px;
}

.json-label {
  font-size: 11px;
  color: #888;
  font-weight: bold;
}
</style>

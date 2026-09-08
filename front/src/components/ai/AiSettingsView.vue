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
                    <AlertTriangle :size="12" /> {{ fetchModelError[p.id] }}
                  </div>
                  <div v-else-if="!isFetchingModels[p.id] && !(fetchedModels[p.id] && fetchedModels[p.id].length > 0)" class="field-hint">
                    <Info :size="12" /> 点击"自动获取"从服务器拉取，或直接手动输入模型标识
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

              <!-- Connectivity Test Field -->
              <div class="field test-field-full">
                <div class="test-btn-row">
                  <button
                    type="button"
                    class="btn-test-connectivity"
                    :disabled="!!testResults[p.id]?.loading"
                    @click.stop="handleTestConnectivity(p)"
                  >
                    <Zap :size="14" :class="{ 'spin-icon': !!testResults[p.id]?.loading }" />
                    {{ testResults[p.id]?.loading ? '正在测试连通性...' : '测试模型连通性 (发送"你好")' }}
                  </button>
                  <span class="thinking-status-tag" :class="{ active: localConfig.enable_thinking }">
                    思考模式: {{ localConfig.enable_thinking ? '已开启' : '已关闭' }}
                  </span>
                </div>

                <!-- Connectivity Result Display Banner -->
                <div v-if="testResults[p.id]" class="test-result-banner">
                  <div v-if="testResults[p.id].loading" class="test-status loading">
                    <RefreshCw :size="14" class="spin-icon" />
                    <span>正在连接模型【{{ p.model }}】并发送“你好”测试 (思考模式: {{ localConfig.enable_thinking ? '开启' : '关闭' }})...</span>
                  </div>
                  <div v-else-if="testResults[p.id].error" class="test-status error">
                    <XCircle :size="16" />
                    <div class="test-text-content">
                      <strong class="status-title">连通性测试失败</strong>
                      <p class="status-desc">{{ testResults[p.id].error }}</p>
                    </div>
                  </div>
                  <div v-else-if="testResults[p.id].message" class="test-status success">
                    <CheckCircle2 :size="16" />
                    <div class="test-text-content">
                      <strong class="status-title">连通性测试成功！AI 回复结果：</strong>
                      <p class="status-desc ai-reply">{{ testResults[p.id].message }}</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <button class="add-provider-card-btn" @click="$emit('add-custom-provider')">
            <Plus :size="14" /> 添加新的模型服务商卡片
          </button>
        </div>
      </div>

      <!-- 2. Prompts Settings Tab (Refactored UX/UI) -->
      <div v-else-if="currentTab === 'prompts'" class="settings-section-card prompts-refactored-section">
        <div class="section-card-header">
          <div class="header-left">
            <Sparkles :size="20" class="section-icon" />
            <div>
              <h4><MessageSquare :size="16" /> Prompts 提示词库管理与生效选择</h4>
            </div>
          </div>
          <div class="prompts-header-actions">
            <button class="btn btn-xs btn-outline" @click="expandAllCategories" title="展开所有分类">
              <ChevronDown :size="13" /> 展开全部
            </button>
            <button class="btn btn-xs btn-outline" @click="collapseAllCategories" title="收起所有分类">
              <ChevronUp :size="13" /> 折叠全部
            </button>
            <button class="btn btn-xs btn-primary" @click="$emit('add-new-prompt')">
              <Plus :size="13" /> 新建 Prompt
            </button>
          </div>
        </div>

        <p class="section-desc">管理与配置系统 Prompt 提示词预设。已启用的提示词将注入至对话上下文，大模型在分析与处理意图时将优先载入对应场景规范。</p>

        <!-- Category Grouping List -->
        <div class="prompts-grouped-container">
          <div
            v-for="(prompts, catName) in groupedPrompts"
            :key="catName"
            class="prompt-category-group"
            :class="{ collapsed: collapsedCategories[catName] }"
          >
            <!-- Category Header -->
            <div class="category-header-row" @click="toggleCategoryCollapse(catName)">
              <div class="category-title-left">
                <button type="button" class="btn-toggle-arrow" aria-label="切换折叠状态">
                  <ChevronDown v-if="!collapsedCategories[catName]" :size="16" />
                  <ChevronRight v-else :size="16" />
                </button>
                <div class="category-name-badge">
                  <Folder :size="16" class="category-icon" />
                  <span class="category-name-text">{{ catName }}</span>
                  <span class="category-count-pill">{{ prompts.length }}</span>
                </div>
                <span
                  v-if="prompts.some(p => activePromptId === p.id)"
                  class="active-contained-badge"
                  title="包含当前生效的主预设"
                >
                  <Target :size="12" /> 包含生效预设
                </span>
              </div>

              <!-- Quick Add Button per Category -->
              <div class="category-actions-right" @click.stop>
                <button
                  class="btn-cat-add-prompt"
                  @click="handleAddNewPromptInCategory(catName)"
                  title="在此分类下快速新建 Prompt"
                >
                  <Plus :size="13" />
                  <span>新建 Prompt</span>
                </button>
              </div>
            </div>

            <!-- Prompts Item List in Category -->
            <div v-show="!collapsedCategories[catName]" class="category-prompts-list">
              <div
                v-for="item in prompts"
                :key="item.id"
                class="prompt-item-row"
                :class="{
                  'is-active-preset': activePromptId === item.id,
                  'is-disabled': item.enabled === false
                }"
              >
                <!-- Edit Form -->
                <div v-if="editingPromptId === item.id" class="card-edit-form prompt-row-edit-form">
                  <div class="edit-row">
                    <input v-model="editForm.category" class="edit-input-sm" placeholder="分类标签" />
                    <input v-model="editForm.title" class="edit-input-title" placeholder="Prompt 标题" />
                  </div>
                  <textarea v-model="editForm.text" class="edit-textarea" rows="3" placeholder="Prompt 指令正文"></textarea>
                  <textarea v-model="editForm.jsonFormat" class="edit-textarea json-textarea" rows="2" placeholder="可选: JSON 输出格式规范"></textarea>
                  <div class="edit-actions">
                    <button class="btn btn-xs btn-primary" @click="$emit('save-edit-prompt', item.id)">保存修改</button>
                    <button class="btn btn-xs btn-outline" @click="$emit('cancel-edit-prompt')">取消</button>
                  </div>
                </div>

                <!-- Item View Block -->
                <div v-else class="prompt-item-view">
                  <div class="prompt-item-left">
                    <!-- Switch Toggle for Enabled State -->
                    <label
                      class="switch-toggle switch-toggle-sm"
                      :title="item.enabled !== false ? '点击停用此 Prompt 注入' : '点击启用此 Prompt 注入'"
                    >
                      <input
                        type="checkbox"
                        :checked="item.enabled !== false"
                        @change="item.enabled = ($event.target as HTMLInputElement).checked; $emit('save-prompts')"
                      />
                      <span class="switch-slider"></span>
                    </label>

                    <!-- Content Group -->
                    <div class="prompt-content-main">
                      <div class="prompt-title-bar">
                        <h5 class="prompt-title-text" @click="$emit('update:activePromptId', item.id)">
                          {{ item.title }}
                        </h5>

                        <span
                          v-if="activePromptId === item.id"
                          class="badge-active-tag glow"
                        >
                          <Target :size="12" /> 当前生效预设
                        </span>
                        <button
                          v-else
                          class="btn-set-active-preset"
                          @click="$emit('update:activePromptId', item.id)"
                          title="点击设为当前主生效预设"
                        >
                          设为主预设
                        </button>
                      </div>

                      <p class="prompt-preview-text">{{ item.text }}</p>

                      <div v-if="item.jsonFormat" class="card-prompt-json sm">
                        <span class="json-label">[JSON 输出格式规范]</span>
                        <pre><code>{{ item.jsonFormat }}</code></pre>
                      </div>
                    </div>
                  </div>

                  <!-- Hover Revealed Action Buttons (Remove Visual Noise) -->
                  <div class="prompt-item-hover-actions">
                    <button
                      class="btn-icon-action"
                      @click="$emit('start-edit-prompt', item)"
                      title="编辑该 Prompt"
                    >
                      <Edit3 :size="14" />
                      <span class="action-text">编辑</span>
                    </button>
                    <button
                      class="btn-icon-action danger"
                      @click="$emit('delete-prompt', item.id)"
                      title="删除该 Prompt"
                    >
                      <Trash2 :size="14" />
                      <span class="action-text">删除</span>
                    </button>
                  </div>
                </div>
              </div>

              <div v-if="prompts.length === 0" class="category-empty-hint">
                此分类下暂无 Prompt，点击右上角快速新建
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 3. Tools Settings Tab -->
      <div v-else-if="currentTab === 'tools'" class="settings-section-card">
        <!-- Main Header & Quick Actions -->
        <div class="section-card-header tools-main-header">
          <div class="header-left">
            <Wrench :size="20" class="section-icon" />
            <div>
              <h4>🛠️ Agent Tools 函数工具箱管理</h4>
              <span class="tools-stats-badge">
                已允许调度 {{ enabledCount }} / {{ (agentTools || []).length }} 个工具
              </span>
            </div>
          </div>
          <div class="tools-header-actions">
            <button class="btn btn-xs btn-outline btn-success-light" @click="$emit('enable-all-tools')">
              ⚡ 全部开启
            </button>
            <button class="btn btn-xs btn-outline btn-danger-light" @click="$emit('disable-all-tools')">
              🚫 全部关闭
            </button>
            <button class="btn btn-xs btn-outline" @click="$emit('reset-default-tools')">
              🔄 重置默认
            </button>
          </div>
        </div>

        <p class="section-desc">在此配置与授权 AI Agent 可自主调度的底层 SQLite 数据库增删改查及系统响应函数。</p>

        <!-- Filter & Search Toolbar (Issue 1 & 6) -->
        <div class="tools-toolbar">
          <div class="tool-category-filters">
            <button
              class="filter-tab-btn"
              :class="{ active: selectedToolCategory === 'all' }"
              @click="selectedToolCategory = 'all'"
            >
              全部 ({{ (agentTools || []).length }})
            </button>
            <button
              class="filter-tab-btn"
              :class="{ active: selectedToolCategory === 'database' }"
              @click="selectedToolCategory = 'database'"
            >
              <Database :size="13" /> SQLite 数据库 ({{ dbToolsCount }})
            </button>
            <button
              class="filter-tab-btn"
              :class="{ active: selectedToolCategory === 'system' }"
              @click="selectedToolCategory = 'system'"
            >
              <Sliders :size="13" /> 系统控制 ({{ systemToolsCount }})
            </button>
            <button
              class="filter-tab-btn filter-risk-btn"
              :class="{ active: selectedToolCategory === 'high_risk' }"
              @click="selectedToolCategory = 'high_risk'"
            >
              <AlertTriangle :size="13" /> 高风险操作 ({{ highRiskCount }})
            </button>
          </div>

          <div class="tool-search-box">
            <Search :size="14" class="search-icon" />
            <input
              type="text"
              v-model="searchToolQuery"
              placeholder="搜索函数名或说明..."
              class="tool-search-input"
            />
            <button v-if="searchToolQuery" class="clear-search-btn" @click="searchToolQuery = ''">×</button>
          </div>
        </div>

        <!-- Structured Tools List (Issues 2, 3, 4, 5, 7, 8) -->
        <div class="tools-settings-list">
          <div
            v-for="tool in filteredAgentTools"
            :key="tool.id"
            class="tool-setting-card"
            :class="{
              disabled: !tool.enabled,
              'is-destructive': tool.isDestructive || tool.id === 'delete_todo'
            }"
          >
            <!-- Card Main Row -->
            <div class="tool-card-main">
              <!-- Left Icon & Main Meta -->
              <div class="tool-left-info">
                <div
                  class="tool-icon-badge"
                  :class="[
                    tool.category,
                    { active: tool.enabled, 'risk-danger': tool.isDestructive || tool.id === 'delete_todo' }
                  ]"
                >
                  <component :is="tool.icon || Wrench" :size="18" />
                </div>

                <div class="tool-text-meta">
                  <!-- Title & Badges Line (Issue 4 Structured Layout) -->
                  <div class="tool-title-line">
                    <span class="tool-func-code"><code>{{ tool.id }}</code></span>
                    <span class="tool-label-text">{{ tool.label }}</span>

                    <!-- Action Type Badge (CRUD) -->
                    <span
                      class="tool-crud-badge"
                      :class="tool.actionType || getToolActionTypeClass(tool)"
                    >
                      {{ tool.actionTypeText || getToolActionTypeText(tool) }}
                    </span>

                    <!-- Destructive / Risk Badge (Issue 3 Risk Warning) -->
                    <span
                      v-if="tool.isDestructive || tool.id === 'delete_todo'"
                      class="tool-risk-badge"
                      title="包含物理删除数据等高风险指令"
                    >
                      <AlertTriangle :size="12" /> ⚠️ 破坏性操作
                    </span>
                  </div>

                  <!-- Description (Issue 7 Visual Hierarchy) -->
                  <p class="tool-desc">{{ tool.description }}</p>
                </div>
              </div>

              <!-- Right Switch & Status Feedback (Issue 2 Status Feedback + Issue 5 Toggle Switch) -->
              <div class="tool-right-switch">
                <div class="status-feedback-wrapper">
                  <span
                    class="status-tag"
                    :class="{
                      'status-enabled-default': tool.enabled && tool.isDefaultEnabled !== false,
                      'status-enabled-user': tool.enabled && tool.isDefaultEnabled === false,
                      'status-disabled': !tool.enabled
                    }"
                  >
                    <template v-if="tool.enabled">
                      <CheckCircle2 :size="12" />
                      {{ tool.isDefaultEnabled !== false ? '默认允许调度' : '手动开启调度' }}
                    </template>
                    <template v-else>
                      <XCircle :size="12" /> 已禁用调度
                    </template>
                  </span>
                </div>

                <!-- Unified Semantic Toggle Switch -->
                <label class="switch-toggle" :title="tool.enabled ? '点击禁用该工具' : '点击允许 Agent 调度该工具'">
                  <input type="checkbox" v-model="tool.enabled" @change="$emit('save-tools')" />
                  <span class="switch-slider"></span>
                </label>
              </div>
            </div>

            <!-- Risk Alert Banner for Enabled Destructive Operations (Issue 3) -->
            <div
              v-if="(tool.isDestructive || tool.id === 'delete_todo') && tool.enabled"
              class="tool-risk-warning-banner"
            >
              <AlertTriangle :size="14" class="risk-icon" />
              <span>注意：此函数涉及强破坏性数据删除，请谨慎赋予 Agent 自动调用权限。</span>
            </div>

            <!-- Expandable Help / Specs Drawer (Issue 8 Help Entry ⓘ) -->
            <div class="tool-card-footer">
              <button
                class="btn-tool-help-toggle"
                @click="toggleToolHelp(tool.id)"
              >
                <Info :size="13" />
                <span>{{ expandedHelpMap[tool.id] ? '收起帮助说明' : '查看函数规范与参数示例 (ⓘ)' }}</span>
                <component :is="expandedHelpMap[tool.id] ? ChevronUp : ChevronDown" :size="13" />
              </button>

              <div v-if="expandedHelpMap[tool.id]" class="tool-help-expand-panel">
                <div class="help-section">
                  <span class="help-label">📥 函数入参声明:</span>
                  <code class="help-code">{{ tool.paramsInfo || getToolParamsFallback(tool) }}</code>
                </div>
                <div class="help-section">
                  <span class="help-label">🎯 典型触发场景:</span>
                  <span class="help-text">{{ tool.usageExample || getToolUsageFallback(tool) }}</span>
                </div>
              </div>
            </div>
          </div>

          <div v-if="filteredAgentTools.length === 0" class="tools-empty-state">
            <Search :size="32" class="empty-icon" />
            <p>未找到符合条件的 Agent 函数工具</p>
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
import { ref, watch, computed } from 'vue'
import {
  Brain, Sparkles, Wrench, BookOpen, Cpu, Target, RefreshCw,
  Plus, Edit3, Trash2, Zap, CheckCircle2, XCircle,
  AlertTriangle, Database, Sliders, Info, Search, ChevronDown, ChevronUp,
  Folder, ChevronRight, MessageSquare
} from 'lucide-vue-next'
import { invokeApi } from '../../utils/apiClient'
import type { LlmConfig, AiActionResult } from '../../types'

export interface CustomLlmProvider {
  id: string
  name: string
  base_url: string
  api_key: string
  model: string
  is_custom?: boolean
}

export interface PromptItem {
  id: string
  title: string
  category: string
  text: string
  jsonFormat?: string
  enabled?: boolean
}

export interface AgentToolItem {
  id: string
  label: string
  category: string
  categoryText: string
  description: string
  enabled: boolean
  icon: any
  actionType?: 'CREATE' | 'READ' | 'UPDATE' | 'DELETE' | 'EXEC'
  actionTypeText?: string
  isDestructive?: boolean
  riskLevel?: 'low' | 'medium' | 'high'
  isDefaultEnabled?: boolean
  paramsInfo?: string
  usageExample?: string
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
  (e: 'add-new-prompt-in-category', category: string): void
  (e: 'start-edit-prompt', item: PromptItem): void
  (e: 'save-edit-prompt', id: string): void
  (e: 'cancel-edit-prompt'): void
  (e: 'delete-prompt', id: string): void
  (e: 'save-prompts'): void
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

// Prompts Interactive Grouping & Collapsible State (Issues 1, 3, 4)
const collapsedCategories = ref<Record<string, boolean>>({})

function toggleCategoryCollapse(cat: string) {
  collapsedCategories.value[cat] = !collapsedCategories.value[cat]
}

function expandAllCategories() {
  collapsedCategories.value = {}
}

function collapseAllCategories() {
  const map: Record<string, boolean> = {}
  Object.keys(groupedPrompts.value).forEach(cat => {
    map[cat] = true
  })
  collapsedCategories.value = map
}

const groupedPrompts = computed(() => {
  const map: Record<string, PromptItem[]> = {}
  for (const item of props.promptLibrary || []) {
    const cat = item.category?.trim() || '未分类预设'
    if (!map[cat]) map[cat] = []
    map[cat].push(item)
  }
  return map
})

function handleAddNewPromptInCategory(catName: string) {
  emit('add-new-prompt-in-category', catName)
}

// Agent Tools Interactive State (Issue 1, 6 & 8)
const selectedToolCategory = ref<'all' | 'database' | 'system' | 'high_risk'>('all')
const searchToolQuery = ref('')
const expandedHelpMap = ref<Record<string, boolean>>({})

function toggleToolHelp(id: string) {
  expandedHelpMap.value[id] = !expandedHelpMap.value[id]
}

const enabledCount = computed(() => {
  return (props.agentTools || []).filter(t => t.enabled).length
})

const dbToolsCount = computed(() => {
  return (props.agentTools || []).filter(t => t.category === 'database').length
})

const systemToolsCount = computed(() => {
  return (props.agentTools || []).filter(t => t.category === 'system').length
})

const highRiskCount = computed(() => {
  return (props.agentTools || []).filter(t => t.isDestructive || t.id === 'delete_todo').length
})

const filteredAgentTools = computed(() => {
  let list = props.agentTools || []
  if (selectedToolCategory.value === 'database') {
    list = list.filter(t => t.category === 'database')
  } else if (selectedToolCategory.value === 'system') {
    list = list.filter(t => t.category === 'system')
  } else if (selectedToolCategory.value === 'high_risk') {
    list = list.filter(t => t.isDestructive || t.id === 'delete_todo')
  }

  const q = searchToolQuery.value.trim().toLowerCase()
  if (q) {
    list = list.filter(
      t =>
        t.id.toLowerCase().includes(q) ||
        t.label.toLowerCase().includes(q) ||
        t.description.toLowerCase().includes(q)
    )
  }
  return list
})

function getToolActionTypeClass(tool: AgentToolItem) {
  if (tool.id.startsWith('add')) return 'CREATE'
  if (tool.id.startsWith('get')) return 'READ'
  if (tool.id.startsWith('update')) return 'UPDATE'
  if (tool.id.startsWith('delete')) return 'DELETE'
  return 'EXEC'
}

function getToolActionTypeText(tool: AgentToolItem) {
  if (tool.id.startsWith('add')) return 'CREATE · 增'
  if (tool.id.startsWith('get')) return 'READ · 查'
  if (tool.id.startsWith('update')) return 'UPDATE · 改'
  if (tool.id.startsWith('delete')) return 'DELETE · 删'
  return 'EXEC · 执行'
}

function getToolParamsFallback(tool: AgentToolItem) {
  if (tool.id === 'delete_todo') return '(id_or_keyword: string)'
  if (tool.id === 'add_todo') return '(title: string, category?: string, priority?: string)'
  if (tool.id === 'update_todo_status') return '(id_or_title: string, completed: boolean)'
  if (tool.id === 'get_todos') return '(query?: string, status?: string)'
  if (tool.id === 'set_alarm') return '(time: string, label: string)'
  if (tool.id === 'start_countdown') return '(minutes: number, title?: string)'
  return '(params: Record<string, any>)'
}

function getToolUsageFallback(tool: AgentToolItem) {
  if (tool.id === 'delete_todo') return '例如：“彻底删除关于草稿的待办”'
  if (tool.id === 'add_todo') return '例如：“新建明天上午10点开会的任务”'
  if (tool.id === 'update_todo_status') return '例如：“把周报标记为已完成”'
  if (tool.id === 'get_todos') return '例如：“查找所有工作类待办”'
  if (tool.id === 'set_alarm') return '例如：“设个明早 8:00 的闹钟”'
  if (tool.id === 'start_countdown') return '例如：“开启 25 分钟专注番茄钟”'
  return '根据 Agent 的对话意图自动识别并调用'
}

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

interface TestResultState {
  loading: boolean
  message?: string
  error?: string
}

const testResults = ref<Record<string, TestResultState>>({})

async function handleTestConnectivity(p: CustomLlmProvider) {
  testResults.value[p.id] = { loading: true }
  try {
    const isThinking = !!props.localConfig?.enable_thinking
    const config: LlmConfig = {
      provider: p.id,
      base_url: p.base_url,
      api_key: p.api_key || '',
      model: p.model,
      enable_thinking: isThinking
    }

    const res = await invokeApi<AiActionResult>('execute_ai_command', {
      input: '你好',
      config: config,
      user_id: 0
    })

    testResults.value[p.id] = {
      loading: false,
      message: res.message
    }
  } catch (err: any) {
    testResults.value[p.id] = {
      loading: false,
      error: err?.message || String(err)
    }
  }
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

.test-field-full {
  grid-column: 1 / -1;
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 6px;
  padding-top: 10px;
  border-top: 1px dashed var(--border-color, #333);
}

.test-btn-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.btn-test-connectivity {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 7px 14px;
  background: var(--primary-bg, rgba(49, 130, 206, 0.12));
  border: 1px solid var(--primary, #3182ce);
  border-radius: 6px;
  color: var(--primary, #3182ce);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease-in-out;
}

.btn-test-connectivity:hover:not(:disabled) {
  background: var(--primary, #3182ce);
  color: #fff;
  box-shadow: 0 0 10px rgba(49, 130, 206, 0.3);
}

.btn-test-connectivity:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.thinking-status-tag {
  font-size: 12px;
  padding: 3px 8px;
  border-radius: 4px;
  background: var(--bg-card, #252538);
  border: 1px solid var(--border-color, #444);
  color: var(--text-secondary, #aaa);
}

.thinking-status-tag.active {
  background: rgba(138, 43, 226, 0.15);
  border-color: #8a2be2;
  color: #b197fc;
  font-weight: bold;
}

.test-result-banner {
  margin-top: 4px;
  padding: 10px 12px;
  border-radius: 6px;
  font-size: 13px;
  animation: fadeIn 0.2s ease-in-out;
}

.test-status {
  display: flex;
  align-items: flex-start;
  gap: 8px;
}

.test-status.loading {
  background: rgba(49, 130, 206, 0.08);
  border: 1px solid rgba(49, 130, 206, 0.25);
  color: var(--primary, #3182ce);
}

.test-status.error {
  background: rgba(229, 62, 62, 0.08);
  border: 1px solid rgba(229, 62, 62, 0.25);
  color: #feb2b2;
}

.test-status.success {
  background: rgba(72, 187, 120, 0.08);
  border: 1px solid rgba(72, 187, 120, 0.25);
  color: #9ae6b4;
}

.test-text-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.status-title {
  font-weight: bold;
  font-size: 13px;
}

.status-desc {
  margin: 0;
  font-size: 12px;
  line-height: 1.4;
  word-break: break-all;
}

.status-desc.ai-reply {
  color: var(--text-main, #e2e8f0);
  background: rgba(0, 0, 0, 0.2);
  padding: 6px 10px;
  border-radius: 4px;
  margin-top: 4px;
}

.spin-icon {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(-4px); }
  to { opacity: 1; transform: translateY(0); }
}

/* Agent Tools Refactored UI Styles */
.tools-main-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.tools-stats-badge {
  display: inline-block;
  margin-top: 4px;
  font-size: 12px;
  color: var(--primary, #3182ce);
  background: rgba(49, 130, 206, 0.12);
  padding: 2px 8px;
  border-radius: 4px;
  font-weight: 500;
}

.btn-success-light {
  color: #38a169;
  border-color: rgba(56, 161, 105, 0.4);
}
.btn-success-light:hover {
  background: rgba(56, 161, 105, 0.15);
}

.btn-danger-light {
  color: #e53e3e;
  border-color: rgba(229, 62, 62, 0.4);
}
.btn-danger-light:hover {
  background: rgba(229, 62, 62, 0.15);
}

/* Toolbar & Filters */
.tools-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin: 16px 0;
  flex-wrap: wrap;
}

.tool-category-filters {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}

.filter-tab-btn {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 6px 12px;
  font-size: 12px;
  border-radius: 6px;
  border: 1px solid var(--border-color, rgba(255, 255, 255, 0.1));
  background: var(--bg-card-subtle, rgba(255, 255, 255, 0.03));
  color: var(--text-secondary, #a0aec0);
  cursor: pointer;
  transition: all 0.2s ease;
}

.filter-tab-btn:hover {
  background: var(--bg-card-hover, rgba(255, 255, 255, 0.08));
  color: var(--text-main, #edf2f7);
}

.filter-tab-btn.active {
  background: var(--primary, #3182ce);
  border-color: var(--primary, #3182ce);
  color: #fff;
  font-weight: 600;
}

.filter-risk-btn.active {
  background: #e53e3e;
  border-color: #e53e3e;
  color: #fff;
}

.tool-search-box {
  position: relative;
  display: flex;
  align-items: center;
}

.search-icon {
  position: absolute;
  left: 10px;
  color: var(--text-secondary, #718096);
  pointer-events: none;
}

.tool-search-input {
  padding: 6px 28px 6px 30px;
  font-size: 12px;
  border-radius: 6px;
  border: 1px solid var(--border-color, rgba(255, 255, 255, 0.12));
  background: var(--bg-input, rgba(0, 0, 0, 0.2));
  color: var(--text-main, #edf2f7);
  width: 200px;
  transition: width 0.2s ease, border-color 0.2s ease;
}

.tool-search-input:focus {
  outline: none;
  border-color: var(--primary, #3182ce);
  width: 240px;
}

.clear-search-btn {
  position: absolute;
  right: 8px;
  background: none;
  border: none;
  color: var(--text-secondary, #a0aec0);
  cursor: pointer;
  font-size: 14px;
}

/* Tool Setting Cards */
.tools-settings-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.tool-setting-card {
  background: var(--bg-card, rgba(30, 30, 45, 0.6));
  border: 1px solid var(--border-color, rgba(255, 255, 255, 0.08));
  border-radius: 8px;
  padding: 14px 16px;
  transition: all 0.2s ease;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.tool-setting-card:hover {
  border-color: rgba(49, 130, 206, 0.4);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.tool-setting-card.disabled {
  opacity: 0.7;
  background: rgba(20, 20, 30, 0.4);
}

.tool-setting-card.is-destructive {
  border-left: 3px solid #e53e3e;
}

.tool-card-main {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.tool-left-info {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  flex: 1;
}

.tool-icon-badge {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.05);
  color: var(--text-secondary, #a0aec0);
  flex-shrink: 0;
  transition: all 0.2s ease;
}

.tool-icon-badge.active {
  background: rgba(49, 130, 206, 0.15);
  color: var(--primary, #3182ce);
}

.tool-icon-badge.risk-danger.active {
  background: rgba(229, 62, 62, 0.15);
  color: #e53e3e;
}

.tool-text-meta {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.tool-title-line {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.tool-func-code code {
  font-family: 'Fira Code', 'Cascadia Code', Consolas, monospace;
  font-size: 13px;
  font-weight: 600;
  color: #63b3ed;
  background: rgba(99, 179, 237, 0.1);
  padding: 2px 6px;
  border-radius: 4px;
  border: 1px solid rgba(99, 179, 237, 0.2);
}

.tool-label-text {
  font-weight: 600;
  font-size: 14px;
  color: var(--text-main, #edf2f7);
}

.tool-crud-badge {
  font-size: 11px;
  padding: 1px 6px;
  border-radius: 4px;
  font-weight: 600;
  letter-spacing: 0.5px;
}

.tool-crud-badge.CREATE {
  background: rgba(72, 187, 120, 0.15);
  color: #68d391;
  border: 1px solid rgba(72, 187, 120, 0.3);
}

.tool-crud-badge.READ {
  background: rgba(66, 153, 225, 0.15);
  color: #63b3ed;
  border: 1px solid rgba(66, 153, 225, 0.3);
}

.tool-crud-badge.UPDATE {
  background: rgba(236, 201, 75, 0.15);
  color: #f6e05e;
  border: 1px solid rgba(236, 201, 75, 0.3);
}

.tool-crud-badge.DELETE {
  background: rgba(229, 62, 62, 0.15);
  color: #fc8181;
  border: 1px solid rgba(229, 62, 62, 0.3);
}

.tool-crud-badge.EXEC {
  background: rgba(159, 122, 234, 0.15);
  color: #b794f4;
  border: 1px solid rgba(159, 122, 234, 0.3);
}

.tool-risk-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  padding: 1px 6px;
  border-radius: 4px;
  background: rgba(229, 62, 62, 0.2);
  color: #feb2b2;
  border: 1px solid rgba(229, 62, 62, 0.4);
  font-weight: bold;
}

.tool-desc {
  font-size: 12.5px;
  color: var(--text-secondary, #a0aec0);
  line-height: 1.45;
  margin: 2px 0 0 0;
}

/* Status Feedback & Switch */
.tool-right-switch {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
}

.status-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  padding: 3px 8px;
  border-radius: 4px;
  font-weight: 500;
}

.status-enabled-default {
  background: rgba(56, 178, 172, 0.12);
  color: #4fd1c5;
  border: 1px solid rgba(56, 178, 172, 0.25);
}

.status-enabled-user {
  background: rgba(66, 153, 225, 0.12);
  color: #63b3ed;
  border: 1px solid rgba(66, 153, 225, 0.25);
}

.status-disabled {
  background: rgba(113, 128, 150, 0.12);
  color: #a0aec0;
  border: 1px solid rgba(113, 128, 150, 0.2);
}

/* Risk Warning Banner */
.tool-risk-warning-banner {
  display: flex;
  align-items: center;
  gap: 8px;
  background: rgba(229, 62, 62, 0.08);
  border: 1px solid rgba(229, 62, 62, 0.25);
  padding: 8px 12px;
  border-radius: 6px;
  color: #feb2b2;
  font-size: 12px;
}

/* Expandable Footer Help Drawer */
.tool-card-footer {
  border-top: 1px solid var(--border-color, rgba(255, 255, 255, 0.05));
  padding-top: 8px;
  margin-top: 2px;
}

.btn-tool-help-toggle {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: transparent;
  border: none;
  color: var(--text-secondary, #718096);
  font-size: 11.5px;
  cursor: pointer;
  padding: 2px 4px;
  border-radius: 4px;
  transition: color 0.2s ease;
}

.btn-tool-help-toggle:hover {
  color: var(--primary, #63b3ed);
}

.tool-help-expand-panel {
  margin-top: 8px;
  padding: 10px 12px;
  background: var(--bg-card-subtle, rgba(0, 0, 0, 0.25));
  border-radius: 6px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-size: 12px;
}

.help-section {
  display: flex;
  align-items: baseline;
  gap: 8px;
}

.help-label {
  font-weight: 600;
  color: var(--text-secondary, #a0aec0);
  flex-shrink: 0;
}

.help-code {
  font-family: 'Fira Code', Consolas, monospace;
  color: #9ae6b4;
  background: rgba(0, 0, 0, 0.3);
  padding: 2px 6px;
  border-radius: 4px;
}

.help-text {
  color: var(--text-main, #e2e8f0);
}

.tools-empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 36px 16px;
  color: var(--text-secondary, #718096);
  gap: 12px;
}

/* ==========================================================================
   Refactored Prompts Library UI (Issues 1, 2, 3, 4, 5 Fixes)
   ========================================================================== */

.prompts-refactored-section {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.prompts-header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.prompts-grouped-container {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: 6px;
}

/* Category Group Panel */
.prompt-category-group {
  background: var(--bg-card, rgba(25, 25, 38, 0.6));
  border: 1px solid var(--border-color, rgba(255, 255, 255, 0.08));
  border-radius: 8px;
  overflow: hidden;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}

.prompt-category-group:hover {
  border-color: rgba(99, 179, 237, 0.3);
}

.prompt-category-group.collapsed {
  background: rgba(20, 20, 30, 0.4);
}

/* Category Header Row */
.category-header-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 14px;
  background: var(--bg-card-subtle, rgba(255, 255, 255, 0.03));
  border-bottom: 1px solid var(--border-color, rgba(255, 255, 255, 0.06));
  cursor: pointer;
  user-select: none;
  transition: background 0.15s ease;
}

.prompt-category-group.collapsed .category-header-row {
  border-bottom: none;
}

.category-header-row:hover {
  background: rgba(255, 255, 255, 0.06);
}

.category-title-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.btn-toggle-arrow {
  background: none;
  border: none;
  color: var(--text-secondary, #a0aec0);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2px;
  cursor: pointer;
}

.category-name-badge {
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 600;
  font-size: 14px;
  color: var(--text-main, #edf2f7);
}

.category-icon {
  color: var(--primary, #63b3ed);
}

.category-count-pill {
  font-size: 11px;
  padding: 1px 7px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.1);
  color: var(--text-secondary, #a0aec0);
  font-weight: 500;
}

.active-contained-badge {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 4px;
  background: rgba(49, 130, 206, 0.15);
  border: 1px solid rgba(49, 130, 206, 0.3);
  color: #63b3ed;
  font-weight: 500;
}

.btn-cat-add-prompt {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  font-size: 12px;
  border-radius: 5px;
  border: 1px dashed rgba(99, 179, 237, 0.4);
  background: rgba(99, 179, 237, 0.08);
  color: #63b3ed;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-cat-add-prompt:hover {
  background: rgba(99, 179, 237, 0.2);
  border-color: #63b3ed;
}

/* Category Prompts List (Indented Layout) */
.category-prompts-list {
  display: flex;
  flex-direction: column;
  padding: 8px 12px 10px 24px;
  gap: 8px;
}

.category-empty-hint {
  font-size: 12px;
  color: var(--text-secondary, #718096);
  padding: 12px 0;
  text-align: center;
  font-style: italic;
}

/* Prompt Item Row */
.prompt-item-row {
  background: var(--bg-card-subtle, rgba(0, 0, 0, 0.2));
  border: 1px solid var(--border-color, rgba(255, 255, 255, 0.06));
  border-left: 3px solid rgba(255, 255, 255, 0.15);
  border-radius: 6px;
  padding: 10px 14px;
  transition: all 0.2s ease;
  position: relative;
}

.prompt-item-row:hover {
  border-color: rgba(99, 179, 237, 0.3);
  background: rgba(255, 255, 255, 0.03);
}

.prompt-item-row.is-active-preset {
  border-left-color: #3182ce;
  background: rgba(49, 130, 206, 0.06);
}

.prompt-item-row.is-disabled {
  opacity: 0.6;
}

.prompt-item-view {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.prompt-item-left {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  flex: 1;
}

.switch-toggle-sm {
  margin-top: 2px;
}

.prompt-content-main {
  display: flex;
  flex-direction: column;
  gap: 4px;
  flex: 1;
}

.prompt-title-bar {
  display: flex;
  align-items: center;
  gap: 10px;
}

.prompt-title-text {
  margin: 0;
  font-size: 13.5px;
  font-weight: 600;
  color: var(--text-main, #edf2f7);
  cursor: pointer;
  transition: color 0.15s ease;
}

.prompt-title-text:hover {
  color: #63b3ed;
}

.badge-active-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 4px;
  background: rgba(49, 130, 206, 0.2);
  border: 1px solid #3182ce;
  color: #63b3ed;
  font-weight: bold;
}

.badge-active-tag.glow {
  box-shadow: 0 0 8px rgba(49, 130, 206, 0.3);
}

.btn-set-active-preset {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid var(--border-color, rgba(255, 255, 255, 0.15));
  color: var(--text-secondary, #a0aec0);
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-set-active-preset:hover {
  background: rgba(49, 130, 206, 0.15);
  border-color: #3182ce;
  color: #63b3ed;
}

.prompt-preview-text {
  margin: 2px 0 0 0;
  font-size: 12.5px;
  color: var(--text-secondary, #a0aec0);
  line-height: 1.5;
}

.card-prompt-json.sm {
  margin-top: 6px;
  padding: 4px 8px;
  font-size: 11px;
}

/* Hover Revealed Action Buttons (Issue 2 Solution) */
.prompt-item-hover-actions {
  display: flex;
  align-items: center;
  gap: 6px;
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.2s ease, transform 0.2s ease;
  transform: translateX(4px);
  flex-shrink: 0;
}

.prompt-item-row:hover .prompt-item-hover-actions {
  opacity: 1;
  pointer-events: auto;
  transform: translateX(0);
}

.btn-icon-action {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  border-radius: 4px;
  border: 1px solid var(--border-color, rgba(255, 255, 255, 0.12));
  background: rgba(255, 255, 255, 0.05);
  color: var(--text-secondary, #a0aec0);
  font-size: 11.5px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.btn-icon-action:hover {
  background: rgba(255, 255, 255, 0.12);
  color: var(--text-main, #fff);
}

.btn-icon-action.danger:hover {
  background: rgba(229, 62, 62, 0.2);
  border-color: rgba(229, 62, 62, 0.5);
  color: #fc8181;
}

.action-text {
  font-size: 11px;
}

.prompt-row-edit-form {
  width: 100%;
}
</style>

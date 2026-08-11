<template>
  <div class="ai-sidebar" :class="{ collapsed: isCollapsed }">
    <!-- Collapsed Toggle Floating Tab -->
    <button
      v-if="!hideToggleBtn"
      class="sidebar-toggle-btn"
      @click="isCollapsed = !isCollapsed"
      :title="isCollapsed ? '展开 AI 智能助手侧边栏' : '收起侧边栏'"
    >
      <span v-if="isCollapsed" class="btn-flex"><Bot :size="15" /> AI 助手</span>
      <span v-else class="btn-flex"><PanelRightClose :size="15" /></span>
    </button>

    <!-- Sidebar Main Content -->
    <div v-show="!isCollapsed" class="sidebar-inner">
      <!-- 1. Header Bar -->
      <div class="sidebar-header">
        <div class="header-title">
          <Bot :size="20" class="ai-avatar-icon" />
          <div class="title-group">
            <h3>AI 智能助手</h3>
            <span class="status-dot-online">在线 - {{ config.model }}</span>
          </div>
        </div>

        <div class="header-actions">
          <button class="icon-btn-sm" @click="clearMessages" title="清空对话历史">
            <Trash2 :size="14" />
          </button>
          <button class="icon-btn-sm" @click="handleClose" title="收起/关闭侧边栏">
            <X :size="14" />
          </button>
        </div>
      </div>

      <!-- 1.5 Mode Switcher Tabs -->
      <div class="sidebar-mode-tabs">
        <button
          class="mode-tab-btn"
          :class="{ active: currentSidebarMode === 'chat' }"
          @click="currentSidebarMode = 'chat'"
        >
          <MessageSquare :size="13" /> Chat
        </button>
        <button
          class="mode-tab-btn"
          :class="{ active: currentSidebarMode === 'prompts' }"
          @click="currentSidebarMode = 'prompts'"
        >
          <Sparkles :size="13" /> Prompts
        </button>
        <button
          class="mode-tab-btn"
          :class="{ active: currentSidebarMode === 'agent' }"
          @click="currentSidebarMode = 'agent'"
        >
          <Cpu :size="13" /> Agent
        </button>
        <button
          class="mode-tab-btn"
          :class="{ active: currentSidebarMode === 'settings' }"
          @click="currentSidebarMode = 'settings'"
        >
          <Settings :size="13" /> 设置
        </button>
      </div>

      <!-- Prompts Library Panel -->
      <div v-if="currentSidebarMode === 'prompts'" class="prompts-library-panel animate-fade-in">
        <h4 class="panel-title"><Sparkles :size="15" /> 常用 AI 提示词库 (Prompts Library)</h4>
        <p class="panel-desc">点击下方卡片即可快捷使用针对待办管理预设的专业 Prompts：</p>

        <div class="prompts-grid">
          <div
            v-for="(item, idx) in promptLibrary"
            :key="idx"
            class="prompt-card"
            @click="usePromptCard(item.text)"
          >
            <div class="card-head">
              <span class="card-category">{{ item.category }}</span>
              <span class="card-title-text">{{ item.title }}</span>
            </div>
            <p class="card-body-text">{{ item.text }}</p>
          </div>
        </div>
      </div>

      <!-- Agent Chain Panel -->
      <div v-else-if="currentSidebarMode === 'agent'" class="agent-chain-panel animate-fade-in">
        <div class="agent-intro-card">
          <Cpu :size="24" class="agent-icon" />
          <h4>AI 智能体工具链 (Autonomous Agent)</h4>
          <p>当前智能体已绑定 **SQLite 数据库增删改查工具链**，能根据自然语言意图自动分析并自治执行。</p>
        </div>

        <div class="agent-tools-list">
          <span class="tools-title">🛠️ 已挂载工具链 (Registered Tools):</span>
          <div class="tool-tag">🔹 add_todo (写入数据库待办事项)</div>
          <div class="tool-tag">🔹 update_todo_status (标记完成/还原)</div>
          <div class="tool-tag">🔹 delete_todo (物理删除指定 ID 待办)</div>
          <div class="tool-tag">🔹 get_todos (智能检索与多维度筛选)</div>
        </div>
      </div>

      <!-- 2. Chat Messages Area (Default Chat Mode) -->
      <div v-else-if="currentSidebarMode === 'chat'" ref="chatContainerRef" class="chat-messages-container">
        <!-- Welcome Banner if empty -->
        <div v-if="messages.length === 0" class="chat-welcome-card">
          <div class="welcome-icon"><Sparkles :size="28" /></div>
          <h4>我是 Gemini 3.6 Flash 智能助手</h4>
          <p>您可以直接与我对话，或者让我帮您创建、标记与管理待办任务！</p>

          <div class="quick-prompts">
            <span class="prompt-title">💡 试着问我:</span>
            <button
              v-for="(prompt, idx) in defaultPrompts"
              :key="idx"
              class="prompt-chip"
              @click="sendPresetPrompt(prompt)"
            >
              {{ prompt }}
            </button>
          </div>
        </div>

        <!-- Chat Bubble List -->
        <div
          v-for="msg in messages"
          :key="msg.id"
          class="chat-bubble-wrapper"
          :class="['sender-' + msg.sender]"
        >
          <div class="bubble-avatar">
            <User v-if="msg.sender === 'user'" :size="14" />
            <Bot v-else-if="msg.sender === 'ai'" :size="14" />
            <Settings v-else :size="14" />
          </div>

          <div class="bubble-content">
            <div class="bubble-meta">
              <span class="sender-name">{{ msg.sender === 'user' ? '您' : 'AI 智能体' }}</span>
              <span class="timestamp">{{ msg.timestamp }}</span>
            </div>

            <div class="bubble-text">
              {{ msg.text }}
            </div>

            <!-- Action Executed Card if AI performed a DB action -->
            <div v-if="msg.actionResult && msg.actionResult.action !== 'chat'" class="action-badge-card">
              <span class="action-icon">
                <PlusCircle v-if="msg.actionResult.action === 'add'" :size="12" />
                <CheckCircle2 v-else-if="msg.actionResult.action === 'complete'" :size="12" />
                <Trash2 v-else :size="12" />
                {{ msg.actionResult.action === 'add' ? '新建待办' : msg.actionResult.action === 'complete' ? '完成任务' : '删除任务' }}
              </span>
              <span class="action-msg">{{ msg.actionResult.message }}</span>
            </div>
          </div>
        </div>

        <!-- Thinking Animation -->
        <div v-if="isProcessing" class="chat-bubble-wrapper sender-ai animate-fade-in">
          <div class="bubble-avatar"><Bot :size="14" /></div>
          <div class="bubble-content">
            <div class="thinking-dots">
              <span></span>
              <span></span>
              <span></span>
            </div>
          </div>
        </div>
      </div>

      <!-- 4. Settings Panel -->
      <div v-else-if="currentSidebarMode === 'settings'" class="sidebar-settings-panel animate-fade-in">
        <div class="sidebar-setting-item">
          <label class="form-label">服务商 (Provider)</label>
          <select v-model="localConfig.provider" class="select-input" @change="onProviderChange">
            <option value="siliconflow">SiliconFlow (云端)</option>
            <option value="ollama">Ollama (本地)</option>
          </select>
        </div>

        <div class="sidebar-setting-item">
          <label class="form-label">接口地址 (Base URL)</label>
          <input type="text" v-model="localConfig.base_url" class="text-input" />
        </div>

        <div class="sidebar-setting-item">
          <label class="form-label">API Key</label>
          <input type="password" v-model="localConfig.api_key" class="text-input" placeholder="sk-..." :disabled="localConfig.provider === 'ollama'" />
        </div>

        <div class="sidebar-setting-item">
          <label class="form-label">模型名称 (Model)</label>
          <input type="text" v-model="localConfig.model" class="text-input" />
        </div>

        <button class="btn btn-primary btn-sm btn-save-sidebar" @click="saveLlmSettings">
          <Check :size="13" /> 保存模型配置
        </button>
      </div>

      <!-- 3. Bottom Input Box -->
      <div class="chat-input-area">
        <textarea
          v-model="inputQuery"
          class="chat-textarea"
          placeholder="✨ 发送消息或给 AI 下达待办指令..."
          rows="2"
          @keydown.enter.exact.prevent="handleSend"
          :disabled="isProcessing"
        ></textarea>

        <div class="input-actions">
          <span class="input-tip">Shift+Enter 换行，Enter 发送</span>
          <button
            class="btn btn-ai-send"
            @click="handleSend"
            :disabled="isProcessing || !inputQuery.trim()"
          >
            <span v-if="isProcessing" class="spinner-sm"></span>
            <span v-else class="btn-flex">发送 <Send :size="12" /></span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, nextTick } from 'vue'
import {
  Bot, Sparkles, Trash2, X, User, Settings, Send,
  PanelRightClose, CheckCircle2, PlusCircle, MessageSquare, Cpu, Check
} from 'lucide-vue-next'
import type { ChatMessage, LlmConfig, AiActionResult } from '../../types'
import { showConfirm } from '../../utils/confirmState'

const props = withDefaults(
  defineProps<{
    config: LlmConfig
    isProcessing: boolean
    hideToggleBtn?: boolean
  }>(),
  {
    hideToggleBtn: false
  }
)

const emit = defineEmits<{
  (e: 'send', text: string): void
  (e: 'update:config', config: LlmConfig): void
  (e: 'close'): void
}>()

function handleClose() {
  isCollapsed.value = true
  emit('close')
}

type SidebarMode = 'chat' | 'prompts' | 'agent' | 'settings'
const currentSidebarMode = ref<SidebarMode>('chat')

const localConfig = ref<LlmConfig>({ ...props.config })
watch(() => props.config, (newVal) => {
  localConfig.value = { ...newVal }
}, { deep: true })

function onProviderChange() {
  if (localConfig.value.provider === 'siliconflow') {
    localConfig.value.base_url = 'https://api.siliconflow.cn/v1'
  } else {
    localConfig.value.base_url = 'http://localhost:11434'
  }
}

function saveLlmSettings() {
  localStorage.setItem('siliconflow_api_key', localConfig.value.api_key)
  emit('update:config', { ...localConfig.value })
  alert('✅ 大语言模型 (LLM) 参数设置保存成功！')
}

interface PromptItem {
  category: string
  title: string
  text: string
}

const promptLibrary: PromptItem[] = [
  {
    category: '时间管理',
    title: '高效工作日程划分',
    text: '请帮我规划今天的工作日程，把重要且紧急的任务安排在上午最清醒的时候。'
  },
  {
    category: '任务拆解',
    title: '复杂大项目细化',
    text: '帮我把"完成项目上线"拆解为 5 个具体的、可落地的子待办事项。'
  },
  {
    category: '周报生成',
    title: '工作总结整理',
    text: '请根据我已完成的待办事项，帮我撰写一份简明扼要的本周工作总结。'
  },
  {
    category: '优先级评估',
    title: '待办四象限排序',
    text: '分析我现有的待办列表，并给出最推荐优先处理的前 3 项任务建议。'
  }
]

function usePromptCard(promptText: string) {
  currentSidebarMode.value = 'chat'
  sendPresetPrompt(promptText)
}

const isCollapsed = ref(false)
const inputQuery = ref('')
const chatContainerRef = ref<HTMLElement | null>(null)

const messages = ref<ChatMessage[]>([])

const defaultPrompts = [
  '帮我安排明天上午 10 点团队周会',
  '提醒我今晚 8 点给客户回复邮件',
  '显示所有高优先级的待办事项',
  '你能为我做些什么？'
]

function scrollToBottom() {
  nextTick(() => {
    if (chatContainerRef.value) {
      chatContainerRef.value.scrollTop = chatContainerRef.value.scrollHeight
    }
  })
}

watch(messages, () => {
  scrollToBottom()
}, { deep: true })

function handleSend() {
  const text = inputQuery.value.trim()
  if (!text || props.isProcessing) return

  // Add User Message
  messages.value.push({
    id: String(Date.now()),
    sender: 'user',
    text: text,
    timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  })

  inputQuery.value = ''
  emit('send', text)
  scrollToBottom()
}

function sendPresetPrompt(promptText: string) {
  inputQuery.value = promptText
  handleSend()
}

// Called by parent component when AI responds
function appendAiResponse(result: AiActionResult) {
  messages.value.push({
    id: String(Date.now()),
    sender: 'ai',
    text: result.message,
    timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    actionResult: result
  })
  scrollToBottom()
}

function appendSystemError(errorMsg: string) {
  messages.value.push({
    id: String(Date.now()),
    sender: 'system',
    text: `❌ ${errorMsg}`,
    timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  })
  scrollToBottom()
}

async function clearMessages() {
  const confirmed = await showConfirm({
    title: '清空侧栏对话',
    message: '确定要清空侧边栏的 AI 对话记录吗？',
    confirmText: '清空历史',
    cancelText: '取消',
    type: 'warning'
  })
  if (!confirmed) return
  messages.value = []
}

defineExpose({
  appendAiResponse,
  appendSystemError,
  isCollapsed
})
</script>

<style scoped>
.ai-sidebar {
  position: relative;
  width: 360px;
  height: 100%;
  background-color: var(--bg-surface);
  border-left: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  transition: width 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  z-index: 20;
}

.btn-flex {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
}

.ai-sidebar.collapsed {
  width: 48px;
}

.sidebar-toggle-btn {
  position: absolute;
  top: 12px;
  left: -36px;
  background-color: var(--bg-surface);
  border: 1px solid var(--border-color);
  border-right: none;
  border-radius: 8px 0 0 8px;
  padding: 8px 10px;
  cursor: pointer;
  color: var(--primary);
  font-weight: 600;
  font-size: 12px;
  box-shadow: -2px 2px 8px rgba(0, 0, 0, 0.08);
  transition: all 0.2s;
  z-index: 21;
}

.sidebar-toggle-btn:hover {
  background-color: var(--bg-card-hover);
  color: var(--ai-purple);
}

.sidebar-inner {
  display: flex;
  flex-direction: column;
  height: 100%;
  width: 100%;
  overflow: hidden;
}

.sidebar-mode-tabs {
  display: flex;
  background-color: var(--bg-app);
  padding: 4px;
  gap: 4px;
  border-bottom: 1px solid var(--border-color);
}

.mode-tab-btn {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  padding: 6px 8px;
  border-radius: 4px;
  border: none;
  background: transparent;
  color: var(--text-muted);
  font-size: 11px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.mode-tab-btn.active {
  background-color: var(--bg-surface);
  color: var(--primary);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
}

/* Prompts & Agent Panels */
.prompts-library-panel, .agent-chain-panel {
  flex: 1;
  padding: 16px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 12px;
  background-color: var(--bg-app);
}

.panel-title {
  font-size: 13px;
  font-weight: 700;
  color: var(--primary);
  display: flex;
  align-items: center;
  gap: 6px;
  margin: 0;
}

.panel-desc {
  font-size: 11px;
  color: var(--text-muted);
  margin: 0;
}

.prompts-grid {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.prompt-card {
  background-color: var(--bg-surface);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.prompt-card:hover {
  border-color: var(--primary);
  transform: translateY(-1px);
}

.card-head {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.card-category {
  font-size: 10px;
  background-color: rgba(66, 153, 225, 0.15);
  color: var(--primary);
  padding: 2px 6px;
  border-radius: 4px;
  font-weight: 600;
}

.card-title-text {
  font-size: 12px;
  font-weight: 700;
  color: var(--text-main);
}

.card-body-text {
  font-size: 11px;
  color: var(--text-muted);
  line-height: 1.4;
  margin: 0;
}

.agent-intro-card {
  padding: 16px;
  background-color: var(--bg-surface);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  text-align: center;
}

.agent-icon {
  color: var(--ai-purple);
  margin-bottom: 6px;
}

.agent-intro-card h4 {
  font-size: 13px;
  color: var(--primary);
  margin-bottom: 4px;
}

.agent-intro-card p {
  font-size: 11px;
  color: var(--text-muted);
  margin: 0;
  line-height: 1.4;
}

.agent-tools-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.tools-title {
  font-size: 11px;
  font-weight: 700;
  color: var(--text-muted);
}

.tool-tag {
  font-size: 11px;
  font-family: monospace;
  padding: 6px 10px;
  background-color: var(--bg-surface);
  border: 1px solid var(--border-color);
  border-radius: 6px;
  color: var(--text-main);
}

/* Header */
.sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 16px;
  border-bottom: 1px solid var(--border-color);
  background-color: var(--bg-app);
}

.header-title {
  display: flex;
  align-items: center;
  gap: 10px;
}

.ai-avatar {
  font-size: 22px;
}

.title-group h3 {
  font-size: 14px;
  font-weight: 700;
  color: var(--text-main);
  margin: 0;
}

.status-dot-online {
  font-size: 11px;
  color: #38a169;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 6px;
}

.icon-btn-sm {
  background: transparent;
  border: none;
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
  font-size: 13px;
  color: var(--text-muted);
}

.icon-btn-sm:hover {
  background-color: var(--border-color);
}

/* Messages Area */
.chat-messages-container {
  flex: 1;
  padding: 16px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 14px;
  background-color: var(--bg-app);
}

.chat-welcome-card {
  text-align: center;
  padding: 20px 14px;
  background-color: var(--bg-surface);
  border: 1px dashed var(--border-color);
  border-radius: var(--radius-md);
  margin-top: 10px;
}

.welcome-icon {
  font-size: 32px;
  margin-bottom: 6px;
}

.chat-welcome-card h4 {
  font-size: 14px;
  color: var(--primary);
  margin-bottom: 6px;
}

.chat-welcome-card p {
  font-size: 12px;
  color: var(--text-muted);
  line-height: 1.5;
  margin-bottom: 14px;
}

.quick-prompts {
  display: flex;
  flex-direction: column;
  gap: 6px;
  align-items: stretch;
}

.prompt-title {
  font-size: 11px;
  color: var(--text-muted);
  font-weight: 600;
  text-align: left;
}

.prompt-chip {
  background-color: var(--bg-app);
  border: 1px solid var(--border-color);
  border-radius: 6px;
  padding: 6px 10px;
  font-size: 11px;
  color: var(--text-main);
  text-align: left;
  cursor: pointer;
  transition: all 0.2s;
}

.prompt-chip:hover {
  border-color: var(--primary);
  color: var(--primary);
}

/* Bubble Wrapper */
.chat-bubble-wrapper {
  display: flex;
  gap: 10px;
  align-items: flex-start;
}

.chat-bubble-wrapper.sender-user {
  flex-direction: row-reverse;
}

.bubble-avatar {
  font-size: 18px;
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: var(--bg-surface);
  border: 1px solid var(--border-color);
  border-radius: 50%;
  flex-shrink: 0;
}

.bubble-content {
  max-width: 80%;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.bubble-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 10px;
  color: var(--text-muted);
}

.sender-user .bubble-meta {
  justify-content: flex-end;
}

.bubble-text {
  padding: 10px 14px;
  border-radius: 12px;
  font-size: 13px;
  line-height: 1.6;
  word-break: break-word;
  white-space: pre-wrap;
}

.sender-user .bubble-text {
  background-color: var(--primary);
  color: #ffffff;
  border-top-right-radius: 2px;
}

.sender-ai .bubble-text {
  background-color: var(--bg-surface);
  color: var(--text-main);
  border: 1px solid var(--border-color);
  border-top-left-radius: 2px;
}

.sender-system .bubble-text {
  background-color: rgba(229, 62, 62, 0.1);
  color: #e53e3e;
  border: 1px solid rgba(229, 62, 62, 0.3);
  font-size: 12px;
}

.action-badge-card {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 6px 10px;
  background-color: rgba(128, 90, 213, 0.1);
  border: 1px solid rgba(128, 90, 213, 0.3);
  border-radius: 6px;
  margin-top: 4px;
  font-size: 11px;
}

.action-icon {
  font-weight: 700;
  color: var(--ai-purple);
}

.action-msg {
  color: var(--text-main);
}

/* Thinking animation */
.thinking-dots {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 10px 14px;
  background-color: var(--bg-surface);
  border-radius: 12px;
  border: 1px solid var(--border-color);
}

.thinking-dots span {
  width: 6px;
  height: 6px;
  background-color: var(--primary);
  border-radius: 50%;
  animation: bounce 1.4s infinite ease-in-out both;
}

.thinking-dots span:nth-child(1) { animation-delay: -0.32s; }
.thinking-dots span:nth-child(2) { animation-delay: -0.16s; }

@keyframes bounce {
  0%, 80%, 100% { transform: scale(0); }
  40% { transform: scale(1); }
}

/* Input Area */
.chat-input-area {
  padding: 12px;
  background-color: var(--bg-surface);
  border-top: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.chat-textarea {
  width: 100%;
  padding: 8px 10px;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  background-color: var(--bg-app);
  color: var(--text-main);
  font-family: inherit;
  font-size: 12px;
  resize: none;
  outline: none;
  box-sizing: border-box;
}

.chat-textarea:focus {
  border-color: var(--primary);
}

.input-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.input-tip {
  font-size: 10px;
  color: var(--text-muted);
}

.btn-ai-send {
  background-color: var(--ai-purple);
  color: #ffffff;
  font-size: 12px;
  padding: 6px 14px;
  border-radius: 6px;
  border: none;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-ai-send:hover:not(:disabled) {
  opacity: 0.9;
  transform: translateY(-1px);
}

.sidebar-setting-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
  width: 100%;
}

.sidebar-setting-item .select-input,
.sidebar-setting-item .text-input {
  width: 100% !important;
  box-sizing: border-box !important;
}</style>

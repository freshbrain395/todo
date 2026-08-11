<!-- src/components/ai/settings/ProviderCard.vue -->

<template>
  <div
    class="provider-card"
    :class="{ 'is-current': isCurrent }"
    @click="$emit('select', provider)"
  >

    <div class="provider-header">

      <div class="header-name-area">

        <Cpu :size="18" class="header-icon" />

        <span class="provider-title-text">{{ provider.name }}</span>

      </div>


      <span v-if="isCurrent" class="current-badge">
        <Target :size="13" />
        当前生效
      </span>


    </div>



    <div class="provider-form">


      <!-- Base URL -->

      <div class="field">

        <label class="field-label">
          接口地址 (Base URL)
        </label>


        <input v-model="provider.base_url" class="form-input" placeholder="https://api..."
          @change="$emit('update', provider)" />

      </div>




      <!-- API KEY -->

      <div class="field">

        <label class="field-label">
          API Key
        </label>


        <input v-model="provider.api_key" type="password" class="form-input" placeholder="sk..."
          @change="$emit('update', provider)" />

      </div>






      <!-- Model -->

      <div class="field">

        <div class="label-with-actions">
          <label class="field-label">
            模型名称 (Model)
          </label>

          <div class="model-action-links">
            <button
              type="button"
              class="btn-text-action"
              :disabled="isFetching"
              @click.stop="$emit('fetch-models', provider)"
              title="重新获取在线模型列表"
            >
              <RefreshCw :size="12" :class="{ 'spin-icon': isFetching }" />
              {{ isFetching ? '获取中...' : '自动获取' }}
            </button>
            <button
              type="button"
              class="btn-text-action"
              @click.stop="$emit('toggle-manual', provider.id)"
              :title="isManual ? '切换为下拉选择' : '切换为手动输入'"
            >
              {{ isManual ? '切换下拉框' : '手动输入' }}
            </button>
          </div>
        </div>


        <!-- 手动输入模式 / 获取失败或模式被切换为手动 -->
        <div v-if="isManual || modelsList.length === 0" class="input-with-hint">
          <input
            v-model="provider.model"
            class="form-input"
            placeholder="例如: gpt-4o, llama3:latest..."
            @change="$emit('update', provider)"
          />
          <div v-if="fetchError" class="field-hint error-hint">
            ⚠️ {{ fetchError }} (已自动切换为手动输入)
          </div>
          <div v-else-if="!isFetching && modelsList.length === 0" class="field-hint">
            💡 点击"自动获取"从服务器拉取，或直接手动输入模型标识
          </div>
        </div>

        <!-- 下拉搜索选择模式 -->
        <div v-else class="select-search-wrapper">
          <div class="custom-select-box" @click.stop="toggleModelDropdown">
            <input
              v-model="searchQuery"
              class="form-input search-input"
              :placeholder="provider.model || '搜索或选择模型...'"
              @focus="isDropdownOpen = true"
              @input="onSearchInput"
              @change="$emit('update', provider)"
            />
            <ChevronDown :size="14" class="dropdown-arrow" :class="{ 'is-open': isDropdownOpen }" />
          </div>

          <!-- 下拉菜单列表 -->
          <div v-if="isDropdownOpen" class="model-dropdown-menu">
            <div class="dropdown-header">
              <span>共 {{ filteredModels.length }} 个可用模型</span>
            </div>
            <div class="dropdown-list">
              <div
                v-for="m in filteredModels"
                :key="m.id"
                class="dropdown-item"
                :class="{ selected: provider.model === m.id }"
                @click.stop="selectModel(m.id)"
              >
                <div class="model-item-info">
                  <span class="model-item-id">{{ m.id }}</span>
                  <span v-if="m.name && m.name !== m.id" class="model-item-name">{{ m.name }}</span>
                </div>
                <Check v-if="provider.model === m.id" :size="14" class="check-icon" />
              </div>
              <div v-if="filteredModels.length === 0" class="dropdown-empty">
                未找到匹配的模型 "{{ searchQuery }}"
              </div>
            </div>
          </div>
        </div>


      </div>







      <!-- Thinking -->

      <div class="field">


        <label class="field-label">
          深度思考模式 (Thinking Mode)
        </label>


        <select :value="enableThinking" class="form-input" @change="
          $emit(
            'update-thinking',
            ($event.target as HTMLSelectElement).value === 'true'
          )
          ">

          <option value="false">
            关闭思考模式 (默认)
          </option>


          <option value="true">
            开启大模型深度思考
          </option>


        </select>


      </div>



    </div>


  </div>

</template>



<script setup lang="ts">

import {
  ref,
  computed,
  onMounted,
  onUnmounted,
  watch
} from 'vue'


import {
  Cpu,
  Target,
  RefreshCw,
  ChevronDown,
  Check
} from 'lucide-vue-next'



export interface CustomLlmProvider {

  id: string

  name: string

  base_url: string

  api_key: string

  model: string

  is_custom: boolean

}



const props = withDefaults(defineProps<{

  provider: CustomLlmProvider

  isCurrent: boolean


  modelsList?: {
    id: string
    name: string
  }[]

  isFetching?: boolean
  fetchError?: string
  isManual?: boolean


  enableThinking: boolean

}>(), {
  modelsList: () => [],
  isFetching: false,
  fetchError: '',
  isManual: false
})



const emit = defineEmits<{

  (
    e: 'update',
    provider: CustomLlmProvider
  ): void

  (
    e: 'select',
    provider: CustomLlmProvider
  ): void

  (
    e: 'fetch-models',
    provider: CustomLlmProvider
  ): void

  (
    e: 'toggle-manual',
    providerId: string
  ): void

  (
    e: 'update-thinking',
    enabled: boolean
  ): void

}>()

const isDropdownOpen = ref(false)
const searchQuery = ref('')

watch(() => props.provider.model, (newVal) => {
  if (!isDropdownOpen.value) {
    searchQuery.value = newVal || ''
  }
}, { immediate: true })

const filteredModels = computed(() => {
  if (!props.modelsList) return []
  if (!searchQuery.value.trim()) return props.modelsList
  const query = searchQuery.value.toLowerCase()
  return props.modelsList.filter(
    m => m.id.toLowerCase().includes(query) || m.name.toLowerCase().includes(query)
  )
})

function toggleModelDropdown() {
  isDropdownOpen.value = !isDropdownOpen.value
}

function onSearchInput() {
  props.provider.model = searchQuery.value
  emit('update', props.provider)
}

function selectModel(modelId: string) {
  props.provider.model = modelId
  searchQuery.value = modelId
  isDropdownOpen.value = false
  emit('update', props.provider)
}

function handleOutsideClick(e: MouseEvent) {
  const target = e.target as HTMLElement
  if (!target.closest('.select-search-wrapper')) {
    isDropdownOpen.value = false
  }
}

// 组件加载自动获取模型
onMounted(() => {
  document.addEventListener('click', handleOutsideClick)
  emit('fetch-models', props.provider)
})

onUnmounted(() => {
  document.removeEventListener('click', handleOutsideClick)
})


</script>




<style scoped>
.provider-card {

  display: flex;

  flex-direction: column;

  gap: 14px;

  padding: 16px 18px;

  height: 100%;

  background: var(--bg-surface);

  border: 1px solid var(--border-color);

  border-radius: 8px;

  cursor: pointer;

  transition: all 0.2s ease-in-out;

}

.provider-card:hover {

  border-color: var(--primary);

}

.provider-card.is-current {

  border-color: var(--primary);

  box-shadow:
    0 0 15px rgba(49, 130, 206, .2);

}



.provider-header {

  display: flex;

  justify-content: space-between;

  align-items: center;

  padding-bottom: 10px;

  border-bottom: 1px solid var(--border-color);

}



.header-name-area {

  display: flex;

  align-items: center;

  gap: 8px;

  flex: 1;

  min-width: 0;

}



.header-icon {

  color: var(--primary);

  flex-shrink: 0;

}



.provider-title-text {

  font-size: 15px;

  font-weight: bold;

  color: var(--text-main);

  white-space: nowrap;

  overflow: hidden;

  text-overflow: ellipsis;

}



.current-badge {

  display: flex;

  align-items: center;

  gap: 4px;

  color: var(--primary);

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
  transition: opacity 0.2s;
}

.btn-text-action:hover:not(:disabled) {
  opacity: 1;
  text-decoration: underline;
}

.btn-text-action:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.spin-icon {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.input-with-hint {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.field-hint {
  font-size: 11px;
  color: var(--text-secondary, #888);
}

.error-hint {
  color: var(--danger, #e53e3e);
}

.select-search-wrapper {
  position: relative;
  width: 100%;
}

.custom-select-box {
  position: relative;
  display: flex;
  align-items: center;
}

.search-input {
  padding-right: 28px !important;
}

.dropdown-arrow {
  position: absolute;
  right: 10px;
  color: var(--text-secondary, #888);
  pointer-events: none;
  transition: transform 0.2s ease;
}

.dropdown-arrow.is-open {
  transform: rotate(180deg);
}

.model-dropdown-menu {
  position: absolute;
  top: calc(100% + 4px);
  left: 0;
  right: 0;
  z-index: 100;
  background: var(--bg-surface, #1e1e2e);
  border: 1px solid var(--border-color, #333);
  border-radius: 6px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.25);
  max-height: 220px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.dropdown-header {
  padding: 6px 10px;
  font-size: 11px;
  color: var(--text-secondary, #888);
  background: var(--bg-card, rgba(255, 255, 255, 0.03));
  border-bottom: 1px solid var(--border-color, #333);
}

.dropdown-list {
  overflow-y: auto;
  max-height: 180px;
}

.dropdown-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  font-size: 12px;
  cursor: pointer;
  transition: background 0.15s ease;
}

.dropdown-item:hover {
  background: rgba(49, 130, 206, 0.15);
}

.dropdown-item.selected {
  background: rgba(49, 130, 206, 0.25);
  color: var(--primary, #3182ce);
  font-weight: 600;
}

.model-item-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  overflow: hidden;
}

.model-item-id {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.model-item-name {
  font-size: 10px;
  opacity: 0.7;
}

.check-icon {
  color: var(--primary, #3182ce);
  flex-shrink: 0;
}

.dropdown-empty {
  padding: 12px;
  font-size: 12px;
  color: var(--text-secondary, #888);
  text-align: center;
}

.form-input {

  width: 100%;

  height: 38px;

  box-sizing: border-box;

  padding: 8px 12px;

  font-size: 13px;

  color: var(--text-main);

  background: var(--bg-card);

  border: 1px solid var(--border-color);

  border-radius: 6px;

}

.form-input:focus {

  border-color: var(--primary);

  outline: none;

}
</style>
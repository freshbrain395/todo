<template>
  <div style="display: flex; flex-direction: column; gap: 16px; margin-bottom: 24px;">
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: -8px;">
      <h4 style="margin: 0; display: flex; align-items: center; gap: 8px;">
        <Brain :size="20" /> 配置 AI 模型服务商
      </h4>
    </div>

    <!-- Provider Cards Grid: 2 Columns Layout -->
    <div class="providers-grid">
      <ProviderCard
        v-for="p in savedProviders"
        :key="p.id"
        :provider="p"
        :is-current="localConfig.provider === p.id"
        :models-list="fetchedModels[p.id] || []"
        :is-fetching="!!isFetchingModels[p.id]"
        :fetch-error="fetchModelError[p.id] || ''"
        :is-manual="!!isManualModel[p.id]"
        :enable-thinking="localConfig.enable_thinking"
        @update="$emit('update-provider', $event)"
        @select="$emit('select-provider', $event)"
        @delete="$emit('delete-provider', $event)"
        @fetch-models="$emit('fetch-models', $event)"
        @toggle-manual="(id: string) => isManualModel[id] = !isManualModel[id]"
        @update-thinking="val => localConfig.enable_thinking = val"
      />

      <button
        class="add-provider-card-btn"
        @click="$emit('add-custom-provider')"
      >
        ➕ 添加新的模型服务商卡片
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { Brain } from 'lucide-vue-next'
import ProviderCard, { type CustomLlmProvider } from './ProviderCard.vue'

defineProps<{
  savedProviders: CustomLlmProvider[]
  localConfig: any
  fetchedModels: Record<string, { id: string; name: string }[]>
  isFetchingModels: Record<string, boolean>
  fetchModelError: Record<string, string>
}>()

defineEmits<{
  (e: 'update-provider', p: CustomLlmProvider): void
  (e: 'select-provider', p: CustomLlmProvider): void
  (e: 'delete-provider', id: string): void
  (e: 'fetch-models', p: CustomLlmProvider): void
  (e: 'add-custom-provider'): void
}>()

const isManualModel = ref<Record<string, boolean>>({})
</script>

<style scoped>
.providers-grid {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.add-provider-card-btn {
  width: 100%;
  padding: 14px;
  border: 2px dashed var(--border-color);
  border-radius: 8px;
  background: transparent;
  color: var(--text-secondary);
  font-size: 14px;
  font-weight: bold;
  cursor: pointer;
  transition: all 0.2s ease-in-out;
  display: flex;
  align-items: center;
  justify-content: center;
}

.add-provider-card-btn:hover {
  border-color: var(--accent-primary);
  color: var(--accent-primary);
  background: rgba(166, 226, 46, 0.05);
}
</style>

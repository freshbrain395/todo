<template>
  <div class="pomodoro-clock-page animate-fade-in">
    <!-- Sub Tab Switcher Bar -->
    <div class="page-sub-nav">
      <div class="nav-left">
        <button
          class="sub-tab-btn"
          :class="{ active: subTab === 'pomodoro' }"
          @click="subTab = 'pomodoro'"
        >
          <Flame :size="16" />
          <span>番茄钟专注</span>
        </button>

        <button
          class="sub-tab-btn"
          :class="{ active: subTab === 'countdown' }"
          @click="subTab = 'countdown'"
        >
          <Hourglass :size="16" />
          <span>快捷倒计时与闹钟</span>
        </button>
      </div>

      <div class="nav-right">
        <span class="sub-nav-hint">
          {{ subTab === 'pomodoro' ? '🔥 提升工作效率与专注力' : '⏳ 倒计时提醒与系统定闹钟' }}
        </span>
      </div>
    </div>

    <!-- Main Workspace Container -->
    <div class="workspace-body">
      <PomodoroTimer v-if="subTab === 'pomodoro'" />
      <AlarmCountdown v-else-if="subTab === 'countdown'" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { Flame, Hourglass } from 'lucide-vue-next'
import PomodoroTimer from './PomodoroTimer.vue'
import AlarmCountdown from './AlarmCountdown.vue'

const subTab = ref<'pomodoro' | 'countdown'>('pomodoro')
</script>

<style scoped>
.pomodoro-clock-page {
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: 20px 24px;
  box-sizing: border-box;
  background: var(--bg-primary, #0f172a);
  color: var(--text-primary, #f8fafc);
  gap: 16px;
  overflow: hidden;
}

.page-sub-nav {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: rgba(30, 41, 59, 0.6);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  padding: 6px 12px;
}

.nav-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.sub-tab-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  background: transparent;
  border: none;
  color: #94a3b8;
  padding: 8px 16px;
  border-radius: 8px;
  font-size: 0.88rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.sub-tab-btn:hover {
  color: #f1f5f9;
  background: rgba(255, 255, 255, 0.05);
}

.sub-tab-btn.active {
  background: linear-gradient(135deg, rgba(56, 189, 248, 0.2), rgba(37, 99, 235, 0.2));
  color: #38bdf8;
  border: 1px solid rgba(56, 189, 248, 0.3);
}

.nav-right {
  display: flex;
  align-items: center;
}

.sub-nav-hint {
  font-size: 0.8rem;
  color: #64748b;
}

.workspace-body {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.animate-fade-in {
  animation: fadeIn 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(6px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>

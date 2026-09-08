import { describe, it, expect, beforeEach } from 'vitest'
import { api, invokeApi } from '../utils/apiClient'
import type { LlmConfig } from '../types'

// 简单的 mockStorage
const mockStorage = new Map<string, string>()
const mockLocalStorage = {
  getItem: (k: string) => mockStorage.get(k) || null,
  setItem: (k: string, v: string) => { mockStorage.set(k, String(v)) },
  removeItem: (k: string) => { mockStorage.delete(k) },
  clear: () => { mockStorage.clear() }
}

if (typeof globalThis.localStorage === 'undefined' || !globalThis.localStorage.clear) {
  Object.defineProperty(globalThis, 'localStorage', { value: mockLocalStorage, writable: true })
}

describe('前端所有 11 个 API 接口完整性与功能测试', () => {
  beforeEach(() => {
    mockStorage.clear()
  })


  // 2. 待办事项 CRUD API 测试
  describe('待办事项 API (get_todos, add_todo, update_todo_status, update_todo, delete_todo)', () => {
    it('获取初始待办列表 (get_todos)', async () => {
      const todos = await api.getTodos('all', '', 1001)
      expect(Array.isArray(todos)).toBe(true)
      expect(todos.length).toBeGreaterThan(0)
    })

    it('添加新待办任务 (add_todo)', async () => {
      const newId = await api.addTodo('测试API添加功能', 'high', '工作', null, 1001)
      expect(typeof newId).toBe('number')

      const todos = await api.getTodos('all', '', 1001)
      const added = todos.find(t => t.id === newId)
      expect(added).toBeDefined()
      expect(added?.title).toBe('测试API添加功能')
      expect(added?.priority).toBe('high')
    })

    it('更新待办完成状态 (update_todo_status)', async () => {
      const id = await api.addTodo('待更新状态任务', 'medium', '常规', null, 1001)
      const success = await api.updateTodoStatus(id, true, 1001)
      expect(success).toBe(true)

      const todos = await api.getTodos('completed', '', 1001)
      const updated = todos.find(t => t.id === id)
      expect(updated?.completed).toBe(true)
    })

    it('全量更新待办详情 (update_todo)', async () => {
      const id = await api.addTodo('原标题', 'low', '生活', null, 1001)
      const success = await api.updateTodo(id, '原标题修改后', 'high', '工作', '2026-09-01T10:00', 1001)
      expect(success).toBe(true)

      const todos = await api.getTodos('all', '', 1001)
      const updated = todos.find(t => t.id === id)
      expect(updated?.title).toBe('原标题修改后')
      expect(updated?.priority).toBe('high')
      expect(updated?.category).toBe('工作')
    })

    it('删除待办任务 (delete_todo)', async () => {
      const id = await api.addTodo('待删除任务', 'medium', '常规', null, 1001)
      const success = await api.deleteTodo(id, 1001)
      expect(success).toBe(true)

      const todos = await api.getTodos('all', '', 1001)
      const found = todos.find(t => t.id === id)
      expect(found).toBeUndefined()
    })
  })

  // 3. AI 模块 API 测试
  describe('AI API (fetch_models & execute_ai_command)', () => {
    it('获取可用 AI 模型列表 (fetch_models)', async () => {
      const models = await api.fetchModels('http://localhost:11434', '')
      expect(Array.isArray(models)).toBe(true)
      expect(models.length).toBeGreaterThan(0)
    })

    it('执行 AI 语义分析命令 (execute_ai_command)', async () => {
      const dummyConfig: LlmConfig = {
        provider: 'ollama',
        base_url: 'http://localhost:11434',
        api_key: '',
        model: 'deepseek-r1:8b',
        enable_thinking: true
      }
      const result = await api.executeAiCommand('添加高优先级工作任务：完成周报', dummyConfig, 1001)
      expect(result).toBeDefined()
      expect(result.action).toBe('add_todo')
      expect(result.message).toContain('周报')
    })
  })

  // 4. 时钟配置 API 测试
  describe('时钟配置 API (get_clock_config & save_clock_config)', () => {
    it('未保存前获取时钟配置应返回 null (get_clock_config)', async () => {
      const config = await api.getClockConfig()
      expect(config).toBeNull()
    })

    it('保存并读取时钟配置 (save_clock_config & get_clock_config)', async () => {
      const testConfig = JSON.stringify({ mode: 'pomodoro', workDuration: 25, breakDuration: 5 })
      const saveRes = await api.saveClockConfig(testConfig)
      expect(saveRes).toBe(true)

      const loadedConfig = await api.getClockConfig()
      expect(loadedConfig).toBe(testConfig)
    })
  })

  // 5. 无法识别命令异常校验
  describe('未知 API 指令测试', () => {
    it('传入未注册指令时应抛出错误', async () => {
      await expect(invokeApi('unknown_command_xyz')).rejects.toThrow('未知的 API 指令')
    })
  })
})

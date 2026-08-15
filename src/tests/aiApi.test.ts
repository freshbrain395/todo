import { describe, it, expect } from 'vitest'
import { api } from '../utils/apiClient'
import type { LlmConfig } from '../types'

describe('AI & LLM Integration API Test Suite', () => {
  it('fetch_models: 应正确列出已安装/支持的模型清单', async () => {
    const models = await api.fetchModels('http://localhost:11434', '')
    expect(models).toContain('deepseek-r1:8b')
  })

  it('execute_ai_command: 应支持连通性测试 (发送"你好"并带上思考模式配置)', async () => {
    const configWithThinking: LlmConfig = {
      provider: 'ollama',
      base_url: 'http://localhost:11434',
      api_key: '',
      model: 'deepseek-r1:8b',
      enable_thinking: true
    }
    const res = await api.executeAiCommand('你好', configWithThinking, 0)
    expect(res).toBeDefined()
    expect(res.action).toBe('chat')
    expect(res.message).toBeTruthy()
  })
})

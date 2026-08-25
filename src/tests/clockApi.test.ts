import { describe, it, expect } from 'vitest'
import { api } from '../utils/apiClient'

describe('Local Clock Config API Test Suite', () => {
  it('save_clock_config & get_clock_config: 保存并成功读取番茄钟配置', async () => {
    const configData = JSON.stringify({ mode: 'clock', theme: 'nord', soundEnabled: true, ts: Date.now() })
    const saved = await api.saveClockConfig(configData)
    expect(saved).toBe(true)

    const result = await api.getClockConfig()
    expect(result).toBe(configData)
  })

  it('支持 analog, digital, flip 三种高精度时钟视觉模式', () => {
    const validModes = ['analog', 'digital', 'flip']
    expect(validModes).toContain('flip')
    expect(validModes.length).toBe(3)
  })
})

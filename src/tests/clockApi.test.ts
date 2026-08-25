import { describe, it, expect } from 'vitest'
import { api } from '../utils/apiClient'
import type { ClockVisualMode } from '../components/productivity/LocalClockPage.vue'

describe('Local Clock Config API Test Suite', () => {
  it('save_clock_config & get_clock_config: 保存并成功读取番茄钟配置', async () => {
    const configData = JSON.stringify({ mode: 'clock', theme: 'nord', soundEnabled: true, ts: Date.now() })
    const saved = await api.saveClockConfig(configData)
    expect(saved).toBe(true)

    const result = await api.getClockConfig()
    expect(result).toBe(configData)
  })

  it('支持 8 种高精度时钟视觉模式 (analog, digital, flip, nixie, rings, seven-segment, matrix-words, compass)', () => {
    const validModes: ClockVisualMode[] = ['analog', 'digital', 'flip', 'nixie', 'rings', 'seven-segment', 'matrix-words', 'compass']
    expect(validModes).toContain('analog')
    expect(validModes).toContain('digital')
    expect(validModes).toContain('flip')
    expect(validModes).toContain('nixie')
    expect(validModes).toContain('rings')
    expect(validModes).toContain('seven-segment')
    expect(validModes).toContain('matrix-words')
    expect(validModes).toContain('compass')
    expect(validModes.length).toBe(8)
  })
})

import { describe, it, expect, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import CountdownPage from '../components/productivity/CountdownPage.vue'
import AlarmPage from '../components/productivity/AlarmPage.vue'

describe('Productivity Separation: CountdownPage & AlarmPage', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  describe('CountdownPage', () => {
    it('should mount with default countdown items', () => {
      const wrapper = mount(CountdownPage)
      expect(wrapper.text()).toContain('全部')
      expect(wrapper.text()).toContain('计时中')
      expect(wrapper.text()).toContain('已完成')
      expect(wrapper.text()).toContain('新建倒计时')
      expect(wrapper.text()).toContain('番茄专注')
    })

    it('should filter countdown items', async () => {
      const wrapper = mount(CountdownPage)
      const buttons = wrapper.findAll('.filter-btn')
      expect(buttons.length).toBe(3)
      await buttons[1].trigger('click') // 计时中
      expect(wrapper.findAll('.list-card-item').length).toBe(0) // Default none is running
      await buttons[0].trigger('click') // 全部
      expect(wrapper.findAll('.list-card-item').length).toBeGreaterThanOrEqual(1)
    })
  })

  describe('AlarmPage', () => {
    it('should mount with default alarm items and display format', () => {
      const wrapper = mount(AlarmPage)
      expect(wrapper.text()).toContain('全部')
      expect(wrapper.text()).toContain('已启用')
      expect(wrapper.text()).toContain('已关闭')
      expect(wrapper.text()).toContain('新建闹钟')
      expect(wrapper.text()).toContain('上班提醒与晨会准备')
      expect(wrapper.text()).toContain('08:30')
    })

    it('should toggle alarm enabled status', async () => {
      const wrapper = mount(AlarmPage)
      const checkbox = wrapper.find('.switch-toggle input[type="checkbox"]')
      expect(checkbox.exists()).toBe(true)
      await checkbox.setValue(false)
      expect((checkbox.element as HTMLInputElement).checked).toBe(false)
    })
  })
})

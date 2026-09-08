import { describe, it, expect, vi } from 'vitest'
import { ref } from 'vue'
import { useSlashCommands } from '../components/ai/useSlashCommands'
import { defaultSlashCommands } from '../components/ai/slashCommands'

describe('Slash Commands Menu & Keyboard Navigation Test Suite', () => {
  it('应当在输入 / 时激活菜单', () => {
    const inputQuery = ref('/')
    const { showSlashMenu, filteredSlashCommands } = useSlashCommands(inputQuery)

    expect(showSlashMenu.value).toBe(true)
    expect(filteredSlashCommands.value.length).toBe(defaultSlashCommands.length)
  })

  it('应当根据 / 后续输入的字符过滤命令列表', () => {
    const inputQuery = ref('/add')
    const { filteredSlashCommands } = useSlashCommands(inputQuery)

    expect(filteredSlashCommands.value.length).toBeGreaterThan(0)
    expect(filteredSlashCommands.value[0].key).toBe('/add')
  })

  it('应当支持 ArrowDown 和 ArrowUp 上下箭头环形选择命令', () => {
    const inputQuery = ref('/')
    const { selectedIndex, filteredSlashCommands, handleKeydown } = useSlashCommands(inputQuery)

    expect(selectedIndex.value).toBe(0)

    // 模拟按下 Down 键
    const downEvent = new KeyboardEvent('keydown', { key: 'ArrowDown' })
    const preventDefaultSpy = vi.spyOn(downEvent, 'preventDefault')
    const handledDown = handleKeydown(downEvent)

    expect(handledDown).toBe(true)
    expect(preventDefaultSpy).toHaveBeenCalled()
    expect(selectedIndex.value).toBe(1)

    // 模拟按下 Up 键，回到 0
    const upEvent = new KeyboardEvent('keydown', { key: 'ArrowUp' })
    handleKeydown(upEvent)

    expect(selectedIndex.value).toBe(0)

    // 再次向上翻页，环形到最后一个
    handleKeydown(upEvent)
    expect(selectedIndex.value).toBe(filteredSlashCommands.value.length - 1)
  })

  it('应当在按下 Enter 或 Tab 时选中选中的快捷指令', () => {
    const inputQuery = ref('/')
    const { handleKeydown, showSlashMenu } = useSlashCommands(inputQuery)

    const enterEvent = new KeyboardEvent('keydown', { key: 'Enter' })
    handleKeydown(enterEvent)

    expect(inputQuery.value).toBe('新建待办：')
    expect(showSlashMenu.value).toBe(false)
  })

  it('应当在按下 Esc 时关闭菜单', () => {
    const inputQuery = ref('/')
    const { handleKeydown, showSlashMenu } = useSlashCommands(inputQuery)

    expect(showSlashMenu.value).toBe(true)

    const escEvent = new KeyboardEvent('keydown', { key: 'Escape' })
    handleKeydown(escEvent)

    expect(showSlashMenu.value).toBe(false)
  })

  it('应当在选择清空指令 (/clear) 时触发 onClear 回调', () => {
    const inputQuery = ref('/clear')
    const onClearMock = vi.fn()
    const { selectCommand, filteredSlashCommands } = useSlashCommands(inputQuery, {
      onClear: onClearMock
    })

    const clearCmd = filteredSlashCommands.value.find(c => c.key === '/clear')
    expect(clearCmd).toBeDefined()

    if (clearCmd) {
      selectCommand(clearCmd)
      expect(onClearMock).toHaveBeenCalled()
      expect(inputQuery.value).toBe('')
    }
  })
})

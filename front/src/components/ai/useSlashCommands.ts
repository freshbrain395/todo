import { ref, computed, watch, type Ref } from 'vue'
import { defaultSlashCommands, type SlashCommand } from './slashCommands'

export function useSlashCommands(
  inputQuery: Ref<string>,
  options?: {
    onClear?: () => void
  }
) {
  const selectedIndex = ref(0)
  const isMenuDismissed = ref(false)

  // 监听输入，若清空或不以 / 开头，重置 dismiss 状态与选中索引
  watch(inputQuery, (newVal) => {
    if (!newVal.startsWith('/')) {
      isMenuDismissed.value = false
      selectedIndex.value = 0
    }
  })

  const filteredSlashCommands = computed<SlashCommand[]>(() => {
    if (!inputQuery.value.startsWith('/') || isMenuDismissed.value) {
      return []
    }
    const search = inputQuery.value.slice(1).trim().toLowerCase()
    if (!search) {
      return defaultSlashCommands
    }
    return defaultSlashCommands.filter(cmd =>
      cmd.key.toLowerCase().includes(search) ||
      cmd.label.toLowerCase().includes(search) ||
      cmd.description.toLowerCase().includes(search)
    )
  })

  // 当搜索过滤列表变化时，防止 selectedIndex 越界
  watch(filteredSlashCommands, (newList) => {
    if (selectedIndex.value >= newList.length) {
      selectedIndex.value = Math.max(0, newList.length - 1)
    }
  })

  const showSlashMenu = computed(() => {
    return inputQuery.value.startsWith('/') && !isMenuDismissed.value && filteredSlashCommands.value.length > 0
  })

  function selectCommand(cmd: SlashCommand) {
    if (cmd.action === 'clear') {
      if (options?.onClear) {
        options.onClear()
      }
      inputQuery.value = ''
    } else if (cmd.text) {
      inputQuery.value = cmd.text
    }
    isMenuDismissed.value = true
    selectedIndex.value = 0
  }

  function handleKeydown(e: KeyboardEvent): boolean {
    if (!showSlashMenu.value) return false

    const list = filteredSlashCommands.value
    if (list.length === 0) return false

    if (e.key === 'ArrowDown') {
      e.preventDefault()
      e.stopPropagation()
      selectedIndex.value = (selectedIndex.value + 1) % list.length
      return true
    }

    if (e.key === 'ArrowUp') {
      e.preventDefault()
      e.stopPropagation()
      selectedIndex.value = (selectedIndex.value - 1 + list.length) % list.length
      return true
    }

    if (e.key === 'Enter' || e.key === 'Tab') {
      e.preventDefault()
      e.stopPropagation()
      const targetCmd = list[selectedIndex.value]
      if (targetCmd) {
        selectCommand(targetCmd)
      }
      return true
    }

    if (e.key === 'Escape') {
      e.preventDefault()
      e.stopPropagation()
      isMenuDismissed.value = true
      return true
    }

    return false
  }

  return {
    showSlashMenu,
    selectedIndex,
    filteredSlashCommands,
    selectCommand,
    handleKeydown
  }
}

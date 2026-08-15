export interface SlashCommand {
  id: string
  key: string
  label: string
  description: string
  icon?: string
  action?: 'insert' | 'clear'
  text?: string
  category?: string
}

export const defaultSlashCommands: SlashCommand[] = [
  {
    id: 'cmd-todo',
    key: '/todo',
    label: '创建待办任务',
    description: '快速创建新的待办，如: /todo 准备周报',
    icon: '📌',
    action: 'insert',
    text: '新建待办：'
  },
  {
    id: 'cmd-add',
    key: '/add',
    label: '新建待办事项',
    description: '快速创建新的任务，如: /add 下午 3 点部门例会',
    icon: '➕',
    action: 'insert',
    text: '新建待办：'
  },
  {
    id: 'cmd-complete',
    key: '/complete',
    label: '标记任务完成',
    description: '快速将任务标记为完成状态，如: /complete 完成周报',
    icon: '✅',
    action: 'insert',
    text: '标记完成：'
  },
  {
    id: 'cmd-delete',
    key: '/delete',
    label: '删除待办事项',
    description: '彻底删除指定的待办任务，如: /delete 测试草稿',
    icon: '🗑️',
    action: 'insert',
    text: '删除待办：'
  },
  {
    id: 'cmd-search',
    key: '/search',
    label: '检索待办事项',
    description: '按关键字或状态查找记录，如: /search 工作',
    icon: '🔍',
    action: 'insert',
    text: '查找待办：'
  },
  {
    id: 'cmd-gtd',
    key: '/gtd',
    label: 'GTD 四象限规划',
    description: '按紧急/重要程度评估当前待办，智能安排优先顺序',
    icon: '📊',
    action: 'insert',
    text: '请将我现有的待办事项按 GTD 四象限分类规划，并给出优先处理的 3 项任务建议。'
  },
  {
    id: 'cmd-pomodoro',
    key: '/pomodoro',
    label: '番茄钟专注模式',
    description: '开启 25 分钟专注 + 5 分钟休息倒计时',
    icon: '⏱️',
    action: 'insert',
    text: '把当前任务拆分为番茄钟节奏并开启 25 分钟专注倒计时。'
  },
  {
    id: 'cmd-weekly',
    key: '/weekly',
    label: '周报总结整理',
    description: '根据已完成事项自动生成 Markdown 结构化周报',
    icon: '📝',
    action: 'insert',
    text: '根据我已完成的待办事项，帮我生成一份结构化的周报工作总结。'
  },
  {
    id: 'cmd-clear',
    key: '/clear',
    label: '清空聊天历史',
    description: '一键清空当前窗口所有的消息对话记录',
    icon: '🧹',
    action: 'clear'
  }
]

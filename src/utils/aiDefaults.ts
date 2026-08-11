import { PlusCircle, CheckCircle2, Trash2, Search, Bell, Timer } from 'lucide-vue-next'

export interface SkillItem {
  id: string
  title: string
  category: string
  description: string
  systemPrompt: string
  enabled: boolean
}

export interface PromptItem {
  id: string
  category: string
  title: string
  text: string
  jsonFormat?: string
}

export interface AgentToolItem {
  id: string
  label: string
  description: string
  category: 'database' | 'system'
  categoryText: string
  icon: any
  enabled: boolean
}

export const defaultSkillsLibrary: SkillItem[] = [
  {
    id: 'skill-gtd',
    title: 'GTD 四象限任务规划',
    category: '时间管理',
    description: '根据紧急与重要维度自动解析待办清单，智能规划当日高效率执行顺序。',
    systemPrompt: '请将用户提交的任务按紧急/重要四象限进行分类，并给出第一优先级的 3 个具体执行建议。',
    enabled: true
  },
  {
    id: 'skill-pomodoro',
    title: '番茄工作法轮巡规划',
    category: '专注执行',
    description: '自动将大块工作时间拆解为 25 分钟专注 + 5 分钟休息的番茄钟节奏，并启动系统倒计时。',
    systemPrompt: '将大任务拆分为若干 25 分钟的番茄专注时段，并自动触发倒计时工具。',
    enabled: true
  },
  {
    id: 'skill-weekly-report',
    title: '周报与工作总结整理',
    category: '总结输出',
    description: '按完成状态、任务分类整理已完成列表，自动提炼生成结构化 Markdown 周报。',
    systemPrompt: '分析已完成待办，提炼本周核心产出、未完成风险及下周计划。',
    enabled: true
  },
  {
    id: 'skill-smart-alarm',
    title: '自然语言时间解构与提醒',
    category: '日程提醒',
    description: '精准识别模糊时间表述（如“明早八点半”、“今晚8点”）并自动联动应用闹钟提醒。',
    systemPrompt: '提取时间点与事件主体，自动调用 set_alarm 工具创建响铃提醒。',
    enabled: true
  },
  {
    id: 'skill-breakdown',
    title: '目标分解与微习惯提炼',
    category: '任务拆解',
    description: '把抽象的大目标（如“准备考试”）一键拆解为 3-5 项单日可完成的细化待办。',
    systemPrompt: '拆解复杂目标为具体、可衡量、有清晰动作的子待办事项。',
    enabled: true
  }
]

export const defaultPromptsLibrary: PromptItem[] = [
  {
    id: 'p1',
    category: '时间管理',
    title: '高效工作日程划分',
    text: '请帮我规划今天的工作日程，把重要且紧急的任务安排在上午最清醒的时候。'
  },
  {
    id: 'p2',
    category: '任务拆解',
    title: '复杂大项目细化',
    text: '帮我把"完成项目上线"拆解为 5 个具体的、可落地的子待办事项。'
  },
  {
    id: 'p3',
    category: '周报生成',
    title: '工作总结整理',
    text: '请根据我已完成的待办事项，帮我撰写一份简明扼要的本周工作总结。'
  },
  {
    id: 'p4',
    category: '优先级评估',
    title: '待办四象限排序',
    text: '分析我现有的待办列表，并给出最推荐优先处理的前 3 项任务建议。'
  }
]

export const defaultAgentTools: AgentToolItem[] = [
  {
    id: 'add_todo',
    label: '新建待办事项',
    description: '根据自然语言指令解析标题、分类、截止日期与优先级，自动写入 SQLite 数据库与本地存储。',
    category: 'database',
    categoryText: 'SQLite 增',
    icon: PlusCircle,
    enabled: true
  },
  {
    id: 'update_todo_status',
    label: '更新待办状态',
    description: '根据任务名称或 ID 匹配记录，智能将指定待办标记为已完成或取消完成。',
    category: 'database',
    categoryText: 'SQLite 改',
    icon: CheckCircle2,
    enabled: true
  },
  {
    id: 'delete_todo',
    label: '彻底删除待办',
    description: '根据指定的任务关键词或 ID 物理从 SQLite 数据库中完全删除待办事项记录。',
    category: 'database',
    categoryText: 'SQLite 删',
    icon: Trash2,
    enabled: true
  },
  {
    id: 'get_todos',
    label: '智能检索待办',
    description: '提供关键字搜索、按分类筛选和按完成状态多维度调取数据库待办记录列表。',
    category: 'database',
    categoryText: 'SQLite 查',
    icon: Search,
    enabled: true
  },
  {
    id: 'set_alarm',
    label: '设置提醒闹钟',
    description: '自动在系统闹钟模块添加指定时间（如 08:30）与备注标签的准时响铃提醒。',
    category: 'system',
    categoryText: '应用工具',
    icon: Bell,
    enabled: true
  },
  {
    id: 'start_countdown',
    label: '开启专注倒计时',
    description: '在倒计时模块中一键设置并启动指定分钟数（如 25 分钟番茄钟）的专注倒计时。',
    category: 'system',
    categoryText: '应用工具',
    icon: Timer,
    enabled: true
  }
]

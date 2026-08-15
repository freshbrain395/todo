import { describe, it, expect } from 'vitest'
import { api } from '../utils/apiClient'

describe('Todo Items CRUD API Test Suite', () => {
  const userId = Date.now()

  it('get_todos: 应成功读取待办列表', async () => {
    const todos = await api.getTodos('all', '', userId)
    expect(Array.isArray(todos)).toBe(true)
  })

  it('add_todo: 应成功新建待办任务', async () => {
    const id = await api.addTodo('测试待办任务A', 'high', '工作', null, userId)
    expect(id).toBeGreaterThan(0)

    const list = await api.getTodos('all', '', userId)
    expect(list.some(t => t.id === id && t.title === '测试待办任务A')).toBe(true)
  })

  it('update_todo_status: 应切换完成状态', async () => {
    const id = await api.addTodo('测试任务状态切换', 'medium', '常规', null, userId)
    const res = await api.updateTodoStatus(id, true, userId)
    expect(res).toBe(true)

    const completedList = await api.getTodos('completed', '', userId)
    expect(completedList.some(t => t.id === id)).toBe(true)
  })

  it('update_todo: 应更新任务属性', async () => {
    const id = await api.addTodo('原任务标题', 'low', '生活', null, userId)
    const res = await api.updateTodo(id, '新任务标题', 'high', '学习', null, userId)
    expect(res).toBe(true)

    const list = await api.getTodos('all', '', userId)
    const target = list.find(t => t.id === id)
    expect(target?.title).toBe('新任务标题')
    expect(target?.category).toBe('学习')
  })

  it('delete_todo: 应彻底移除指定任务', async () => {
    const id = await api.addTodo('准备删除的任务', 'low', '常规', null, userId)
    const delRes = await api.deleteTodo(id, userId)
    expect(delRes).toBe(true)

    const list = await api.getTodos('all', '', userId)
    expect(list.some(t => t.id === id)).toBe(false)
  })
})

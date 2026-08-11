import { describe, it, expect, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import App from './App.vue'

// Setup in-memory localStorage mock for test environment
let store: Record<string, string> = {}

const localStorageMock = {
  getItem: (key: string) => store[key] || null,
  setItem: (key: string, value: string) => { store[key] = String(value) },
  removeItem: (key: string) => { delete store[key] },
  clear: () => { store = {} }
}

Object.defineProperty(globalThis, 'localStorage', {
  value: localStorageMock,
  writable: true
})

describe('Frontend Todo List CRUD & Delete Operations', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  it('1. should seed default web todos if localStorage is empty', async () => {
    const wrapper = mount(App)
    await wrapper.vm.$nextTick()
    await new Promise(r => setTimeout(r, 50))

    const storedStr = localStorage.getItem('web_todos')
    expect(storedStr).not.toBeNull()

    const stored = JSON.parse(storedStr!)
    expect(stored.length).toBeGreaterThan(0)
    expect(stored[0]).toHaveProperty('title')
    expect(stored[0]).toHaveProperty('id')
  })

  it('2. should physically delete todo item from localStorage and component state', async () => {
    const initialData = [
      { id: 101, title: '可删除测试任务A', priority: 'high', category: '工作', completed: false, remind_at: null, created_at: new Date().toISOString(), updated_at: new Date().toISOString() },
      { id: 102, title: '保留测试任务B', priority: 'medium', category: '常规', completed: false, remind_at: null, created_at: new Date().toISOString(), updated_at: new Date().toISOString() }
    ]
    localStorage.setItem('web_todos', JSON.stringify(initialData))

    const wrapper = mount(App)
    await wrapper.vm.$nextTick()

    const vm = wrapper.vm as any
    await vm.deleteTodo(101, true)

    const afterStr = localStorage.getItem('web_todos')
    const afterData = JSON.parse(afterStr!)
    expect(afterData.length).toBe(1)
    expect(afterData[0].id).toBe(102)
    expect(afterData.find((t: any) => t.id === 101)).toBeUndefined()
  })

  it('3. should create new todo item successfully', async () => {
    const wrapper = mount(App)
    await wrapper.vm.$nextTick()

    const vm = wrapper.vm as any
    vm.todoForm.title = '单元测试新建待办任务'
    vm.todoForm.category = '工作'
    vm.todoForm.priority = 'high'

    await vm.saveTodoForm()

    const stored = JSON.parse(localStorage.getItem('web_todos') || '[]')
    const created = stored.find((t: any) => t.title === '单元测试新建待办任务')
    expect(created).toBeDefined()
    expect(created.priority).toBe('high')
  })

  it('4. should update existing todo item successfully', async () => {
    const initial = [
      { id: 201, title: '旧标题', priority: 'low', category: '常规', completed: false, remind_at: null, created_at: new Date().toISOString(), updated_at: new Date().toISOString() }
    ]
    localStorage.setItem('web_todos', JSON.stringify(initial))

    const wrapper = mount(App)
    await wrapper.vm.$nextTick()

    const vm = wrapper.vm as any
    vm.openEditModal(initial[0])
    expect(vm.editingTodo).not.toBeNull()

    vm.todoForm.title = '已更新的新标题'
    await vm.saveTodoForm()

    const stored = JSON.parse(localStorage.getItem('web_todos') || '[]')
    expect(stored[0].title).toBe('已更新的新标题')
  })

  it('5. should open confirm dialog when deleteTodo is called without skipConfirm', async () => {
    const initial = [
      { id: 301, title: '弹窗测试任务', priority: 'medium', category: '常规', completed: false, remind_at: null, created_at: new Date().toISOString(), updated_at: new Date().toISOString() }
    ]
    localStorage.setItem('web_todos', JSON.stringify(initial))

    const { confirmState, closeConfirm } = await import('./utils/confirmState')
    const wrapper = mount(App)
    await wrapper.vm.$nextTick()

    const vm = wrapper.vm as any
    // Trigger delete without skipConfirm
    const deletePromise = vm.deleteTodo(301)

    // Verify confirm modal state opened
    expect(confirmState.value.isOpen).toBe(true)
    expect(confirmState.value.title).toBe('彻底删除任务')

    // Close confirm with cancel
    closeConfirm(false)
    await deletePromise

    // Verify task is NOT deleted
    let stored = JSON.parse(localStorage.getItem('web_todos') || '[]')
    expect(stored.find((t: any) => t.id === 301)).toBeDefined()

    // Trigger delete again and confirm
    const deletePromise2 = vm.deleteTodo(301)
    expect(confirmState.value.isOpen).toBe(true)
    closeConfirm(true)
    await deletePromise2

    // Verify task IS physically deleted
    stored = JSON.parse(localStorage.getItem('web_todos') || '[]')
    expect(stored.find((t: any) => t.id === 301)).toBeUndefined()
  })
})

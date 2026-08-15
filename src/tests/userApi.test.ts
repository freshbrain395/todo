import { describe, it, expect, beforeEach } from 'vitest'
import { api } from '../utils/apiClient'

describe('User Authentication API Test Suite', () => {
  beforeEach(() => {
    // 采用 apiClient 内内置的 webFallbackHandler 对应 LocalStorage
  })

  it('register_user: 应该能够成功注册新账号', async () => {
    const username = 'alice_' + Date.now()
    const user = await api.registerUser(username, 'secret123')
    expect(user).toHaveProperty('id')
    expect(user.username).toBe(username)
  })

  it('register_user: 重复注册同名用户应该报错', async () => {
    const username = 'bob_' + Date.now()
    await api.registerUser(username, 'pass1')
    await expect(api.registerUser(username, 'pass2')).rejects.toThrow('用户名已存在')
  })

  it('login_user: 正确的用户名密码应该成功登录', async () => {
    const username = 'charlie_' + Date.now()
    await api.registerUser(username, 'password')
    const user = await api.loginUser(username, 'password')
    expect(user.username).toBe(username)
  })

  it('login_user: 错误账号尝试登录应该返回错误', async () => {
    await expect(api.loginUser('non_existent_' + Date.now(), 'any_pwd')).rejects.toThrow('用户不存在或密码错误')
  })
})

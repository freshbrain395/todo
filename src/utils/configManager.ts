import type { SoundType } from './audio';

export interface UserProfile {
  id: string;
  username: string;
  password?: string;
  avatarColor?: string;
  lastLoginTime?: string;
  isAdmin?: boolean;
}

export interface UserAppConfig {
  soundType: SoundType;
  soundVolume: number; // 0.0 ~ 1.0
  theme: 'light' | 'dark' | 'nord';
  llmConfig: {
    provider: string;
    base_url: string;
    api_key: string;
    model: string;
    enable_thinking: boolean;
  };
  categories: string[];
}

export interface UserAccountData {
  user: UserProfile;
  config: UserAppConfig;
}

const STORAGE_USERS_KEY = 'app_users_v2';
const STORAGE_CURRENT_USER_ID_KEY = 'app_current_user_id_v2';
const STORAGE_IS_LOGGED_IN_KEY = 'app_is_logged_in_v2';

export const DEFAULT_CATEGORIES = ['工作', '个人', '学习', '健康', '财务'];

export const DEFAULT_USER_CONFIG: UserAppConfig = {
  soundType: 'chime',
  soundVolume: 0.8,
  theme: 'light',
  llmConfig: {
    provider: 'siliconflow',
    base_url: 'https://api.siliconflow.cn/v1',
    api_key: '',
    model: 'Qwen/Qwen2.5-7B-Instruct',
    enable_thinking: false,
  },
  categories: [...DEFAULT_CATEGORIES],
};

const DEFAULT_ADMIN_USER: UserProfile = {
  id: 'user_admin',
  username: 'admin',
  password: '123456',
  avatarColor: '#3B82F6',
  lastLoginTime: new Date().toISOString(),
  isAdmin: true
};

// 获取所有用户账号配置映射 (以 userId 为 key 存 JSON 字典)
export function getAllUserAccountsMap(): Record<string, UserAccountData> {
  try {
    const raw = localStorage.getItem(STORAGE_USERS_KEY);
    if (raw) {
      const parsed = JSON.parse(raw);
      // 确保 admin 账号始终存在
      if (!parsed[DEFAULT_ADMIN_USER.id]) {
        parsed[DEFAULT_ADMIN_USER.id] = {
          user: DEFAULT_ADMIN_USER,
          config: JSON.parse(JSON.stringify(DEFAULT_USER_CONFIG))
        };
        saveAllUserAccountsMap(parsed);
      }
      return parsed;
    }
  } catch (e) {
    console.error('Failed to parse users config JSON', e);
  }

  const defaultMap: Record<string, UserAccountData> = {
    [DEFAULT_ADMIN_USER.id]: {
      user: DEFAULT_ADMIN_USER,
      config: JSON.parse(JSON.stringify(DEFAULT_USER_CONFIG))
    },
  };
  saveAllUserAccountsMap(defaultMap);
  return defaultMap;
}

// 保存所有用户 JSON 配置映射
export function saveAllUserAccountsMap(map: Record<string, UserAccountData>): void {
  localStorage.setItem(STORAGE_USERS_KEY, JSON.stringify(map));
}

// 获取当前登录状态
export function checkIsLoggedIn(): boolean {
  const flag = localStorage.getItem(STORAGE_IS_LOGGED_IN_KEY);
  return flag === 'true';
}

// 设置当前登录状态
export function setLoggedInState(isLoggedIn: boolean): void {
  localStorage.setItem(STORAGE_IS_LOGGED_IN_KEY, isLoggedIn ? 'true' : 'false');
}

// 获取当前登录 User ID
export function getCurrentUserId(): string {
  return localStorage.getItem(STORAGE_CURRENT_USER_ID_KEY) || DEFAULT_ADMIN_USER.id;
}

// 设置当前登录 User ID
export function setCurrentUserId(userId: string): void {
  localStorage.setItem(STORAGE_CURRENT_USER_ID_KEY, userId);
  setLoggedInState(true);
}

// 获取指定用户的 JSON 配置
export function getUserConfig(userId: string): UserAppConfig {
  const map = getAllUserAccountsMap();
  if (map[userId]) {
    return map[userId].config;
  }
  return { ...DEFAULT_USER_CONFIG };
}

// 保存指定用户的 JSON 配置
export function saveUserConfig(userId: string, newConfig: Partial<UserAppConfig>): UserAppConfig {
  const map = getAllUserAccountsMap();
  if (!map[userId]) {
    map[userId] = {
      user: { id: userId, username: userId === 'user_admin' ? 'admin' : userId },
      config: { ...DEFAULT_USER_CONFIG },
    };
  }
  map[userId].config = {
    ...map[userId].config,
    ...newConfig,
  };
  saveAllUserAccountsMap(map);
  return map[userId].config;
}

// 创建新用户并可选分配头像颜色与密码
export function createNewUser(username: string, password: string = '123456', avatarColor: string = '#10B981'): UserProfile {
  const map = getAllUserAccountsMap();
  const id = 'user_' + Date.now();
  const newUser: UserProfile = {
    id,
    username,
    password,
    avatarColor,
    lastLoginTime: new Date().toISOString(),
    isAdmin: false
  };
  map[id] = {
    user: newUser,
    config: JSON.parse(JSON.stringify(DEFAULT_USER_CONFIG)),
  };
  saveAllUserAccountsMap(map);
  return newUser;
}

// 验证用户密码
export function verifyUserPassword(userId: string, pass: string): boolean {
  const map = getAllUserAccountsMap();
  const userData = map[userId];
  if (!userData) return false;
  if (!userData.user.password) return true; // 若无密码则直接通过
  return userData.user.password === pass;
}

// 判断当前用户是否为管理员
export function isCurrentAdmin(): boolean {
  const map = getAllUserAccountsMap();
  const currentId = getCurrentUserId();
  return !!map[currentId]?.user.isAdmin;
}

// 管理员更新指定用户信息
export function updateUserProfile(userId: string, updates: Partial<UserProfile>): boolean {
  const map = getAllUserAccountsMap();
  if (!map[userId]) return false;
  map[userId].user = {
    ...map[userId].user,
    ...updates,
  };
  saveAllUserAccountsMap(map);
  return true;
}

// 管理员重置指定用户密码
export function resetUserPassword(userId: string, newPass: string): boolean {
  return updateUserProfile(userId, { password: newPass });
}

// 管理员删除指定普通用户账号
export function deleteUserAccount(userId: string): boolean {
  if (userId === 'user_admin') return false; // 禁止删除超级管理员
  const map = getAllUserAccountsMap();
  if (!map[userId]) return false;
  delete map[userId];
  saveAllUserAccountsMap(map);
  return true;
}

// 注销登录
export function logoutCurrentUser(): void {
  setLoggedInState(false);
}


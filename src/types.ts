export interface Todo {
  id: number;
  title: string;
  priority: 'high' | 'medium' | 'low';
  category: string;
  completed: boolean;
  remind_at?: string | null;
  created_at: string;
  updated_at: string;
  user_id?: number;
}

export interface User {
  id: number;
  username: string;
  created_at?: string;
}


export interface LlmConfig {
  provider: string;
  base_url: string;
  api_key: string;
  model: string;
  enable_thinking: boolean;
}

export type FilterType = 'all' | 'pending' | 'completed';
export type ThemeType = 'light' | 'dark' | 'nord';
export type NavPosition = 'top' | 'left';

export interface AiActionResult {
  action: string;
  data: any;
  message: string;
  should_refresh: boolean;
}

export interface ChatMessage {
  id: string;
  sender: 'user' | 'ai' | 'system';
  text: string;
  timestamp: string;
  actionResult?: AiActionResult;
}

export interface ChatSession {
  id: string;
  title: string;
  createdAt: number;
  updatedAt: number;
  messages: ChatMessage[];
}

export interface LlmProvider {
  id: string;
  name: string;
  base_url: string;
  api_key: string;
  model: string;
  is_custom?: boolean;
}

export interface PromptItem {
  id: string;
  category: string;
  title: string;
  text: string;
  jsonFormat?: string;
  enabled?: boolean;
  isActive?: boolean;
}

export interface SkillItem {
  id: string;
  category: string;
  title: string;
  description: string;
  systemPrompt: string;
  enabled: boolean;
}

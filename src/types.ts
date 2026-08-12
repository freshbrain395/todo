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

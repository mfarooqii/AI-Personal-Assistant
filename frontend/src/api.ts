/**
 * API client for the Aria backend.
 */

const BASE = '/api';

export interface ChatMessage {
  id?: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  agent?: string;
  model?: string;
  tool_calls?: any[];
  created_at?: string;
}

export interface Conversation {
  id: string;
  title: string;
  updated_at: string;
}

export interface TaskInfo {
  id: string;
  description: string;
  status: string;
  agent?: string;
  result?: any;
  created_at?: string;
  scheduled_for?: string;
}

export interface SystemInfo {
  app_name: string;
  version: string;
  ollama_available: boolean;
  installed_models: string[];
  configured_models: Record<string, string>;
}

// ── Chat ──

export async function sendMessage(
  message: string,
  conversationId?: string,
): Promise<{ conversation_id: string; content: string; agent: string; model: string; tool_calls?: any[] }> {
  const res = await fetch(`${BASE}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, conversation_id: conversationId }),
  });
  if (!res.ok) throw new Error(`Chat failed: ${res.statusText}`);
  return res.json();
}

export async function* streamMessage(
  message: string,
  conversationId?: string,
): AsyncGenerator<{ token?: string; done?: boolean; agent?: string }> {
  const res = await fetch(`${BASE}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, conversation_id: conversationId, stream: true }),
  });
  if (!res.ok) throw new Error(`Chat failed: ${res.statusText}`);

  const reader = res.body!.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop() || '';
    for (const line of lines) {
      if (line.startsWith('data: ')) {
        yield JSON.parse(line.slice(6));
      }
    }
  }
}

export async function getConversations(): Promise<Conversation[]> {
  const res = await fetch(`${BASE}/chat/conversations`);
  return res.json();
}

export async function getMessages(conversationId: string): Promise<ChatMessage[]> {
  const res = await fetch(`${BASE}/chat/conversations/${conversationId}/messages`);
  return res.json();
}

// ── Tasks ──

export async function submitTask(description: string, scheduledFor?: string): Promise<{ task_id: string }> {
  const res = await fetch(`${BASE}/tasks`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ description, scheduled_for: scheduledFor }),
  });
  return res.json();
}

export async function getTasks(): Promise<TaskInfo[]> {
  const res = await fetch(`${BASE}/tasks`);
  return res.json();
}

export async function getTask(taskId: string): Promise<TaskInfo> {
  const res = await fetch(`${BASE}/tasks/${taskId}`);
  return res.json();
}

// ── Voice ──

export async function speechToText(audioBlob: Blob): Promise<{ text: string }> {
  const form = new FormData();
  form.append('audio', audioBlob, 'recording.wav');
  const res = await fetch(`${BASE}/voice/stt`, { method: 'POST', body: form });
  return res.json();
}

export async function textToSpeech(text: string): Promise<Blob> {
  const res = await fetch(`${BASE}/voice/tts`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text }),
  });
  return res.blob();
}

// ── Settings ──

export async function getSystemInfo(): Promise<SystemInfo> {
  const res = await fetch(`${BASE}/settings/system`);
  return res.json();
}

export async function getProfile(): Promise<any> {
  const res = await fetch(`${BASE}/settings/profile`);
  return res.json();
}

export async function updateProfile(data: any): Promise<any> {
  const res = await fetch(`${BASE}/settings/profile`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  return res.json();
}

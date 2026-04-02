/**
 * API client for the Aria backend.
 */

const BASE = '/api';

// ── Layout Types ──

export type LayoutType =
  | 'chat'
  | 'news_article'
  | 'email_inbox'
  | 'browser'
  | 'calendar'
  | 'finance'
  | 'search_results'
  | 'kanban'
  | 'data_table'
  | 'document'
  | 'map'
  | 'code'
  | 'media_gallery'
  | 'comparison'
  | 'timeline'
  | 'form'
  | 'dashboard';

export interface LayoutDirective {
  layout: LayoutType;
  title: string;
  data: any;
}

export interface ChatMessage {
  id?: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  agent?: string;
  model?: string;
  tool_calls?: any[];
  layout?: LayoutDirective;
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

export interface WorkflowInfo {
  id: string;
  name: string;
  description: string;
  category: string;
  trigger_keywords: string[];
  output_layout: string;
  steps: { id: string; name: string; type: string; description: string }[];
}

// ── Chat ──

export async function sendMessage(
  message: string,
  conversationId?: string,
): Promise<{
  conversation_id: string;
  content: string;
  agent: string;
  model: string;
  tool_calls?: any[];
  layout?: LayoutDirective;
}> {
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
): AsyncGenerator<{ token?: string; done?: boolean; agent?: string; layout?: LayoutDirective }> {
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

// ── Workflows ──

export async function getWorkflows(): Promise<WorkflowInfo[]> {
  const res = await fetch(`${BASE}/workflows`);
  return res.json();
}

export async function getLayoutTypes(): Promise<Record<string, string>> {
  const res = await fetch(`${BASE}/workflows/layouts`);
  return res.json();
}

// ── Onboarding ──

export interface OnboardingOption {
  id: string;
  label: string;
  description: string;
}

export interface OnboardingStep {
  id: number;
  field: string | null;
  message: string;
  placeholder: string;
  type: 'text' | 'multi_select' | 'complete';
  options?: OnboardingOption[];
}

export interface OnboardingStatus {
  completed: boolean;
  step: number;
  total_steps: number;
}

export interface OnboardingStepResponse {
  completed: boolean;
  step: OnboardingStep;
  message: string;
  profile?: { name: string; profession: string; priorities: string[] };
}

export async function getOnboardingStatus(): Promise<OnboardingStatus> {
  const res = await fetch(`${BASE}/onboarding/status`);
  return res.json();
}

export async function submitOnboardingStep(
  answer?: string,
  selections?: string[],
): Promise<OnboardingStepResponse> {
  const res = await fetch(`${BASE}/onboarding/step`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ answer, selections }),
  });
  return res.json();
}

// ── Integrations ──

export interface IntegrationStatus {
  gmail: { configured: boolean; connected: boolean };
}

export interface EmailMessage {
  id: string;
  thread_id: string;
  subject: string;
  from: string;
  to: string;
  date: string;
  snippet: string;
  body: string;
  is_unread: boolean;
  labels: string[];
}

export async function getIntegrationStatus(): Promise<IntegrationStatus> {
  const res = await fetch(`${BASE}/integrations/status`);
  return res.json();
}

export async function connectGmail(): Promise<{ auth_url: string } | { error: string }> {
  const res = await fetch(`${BASE}/integrations/gmail/connect`);
  return res.json();
}

export async function disconnectGmail(): Promise<{ status: string }> {
  const res = await fetch(`${BASE}/integrations/gmail/disconnect`);
  return res.json();
}

export async function listEmails(
  query?: string,
  maxResults?: number,
  label?: string,
): Promise<{ emails: EmailMessage[]; total: number }> {
  const params = new URLSearchParams();
  if (query) params.set('q', query);
  if (maxResults) params.set('max_results', String(maxResults));
  if (label) params.set('label', label);
  const res = await fetch(`${BASE}/integrations/gmail/emails?${params}`);
  return res.json();
}

export async function readEmail(emailId: string): Promise<EmailMessage> {
  const res = await fetch(`${BASE}/integrations/gmail/emails/${encodeURIComponent(emailId)}`);
  return res.json();
}

export async function sendGmail(to: string, subject: string, body: string): Promise<{ sent: boolean }> {
  const res = await fetch(`${BASE}/integrations/gmail/send`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ to, subject, body }),
  });
  return res.json();
}

// ── Browser Agent ──

export interface BrowserPlan {
  website: string;
  needs_login: boolean;
  plan: string[];
  extract_to_app: boolean;
  reasoning: string;
}

export interface BrowserSessionResponse {
  status: string;
  task: string;
  plan: BrowserPlan;
  message: string;
}

export async function startBrowserSession(
  task: string,
  provider?: string,
): Promise<BrowserSessionResponse> {
  const res = await fetch(`${BASE}/browser/session`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ task, provider: provider || '' }),
  });
  return res.json();
}

export async function resumeBrowserSession(): Promise<{ status: string }> {
  const res = await fetch(`${BASE}/browser/session/resume`, { method: 'POST' });
  return res.json();
}

export async function closeBrowser(): Promise<{ status: string }> {
  const res = await fetch(`${BASE}/browser/close`, { method: 'POST' });
  return res.json();
}

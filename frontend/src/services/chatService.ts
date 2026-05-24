import { api } from './api'
import type { ChatRequest, ChatResponse } from '@/types/chat'

export async function askQuestion(payload: ChatRequest): Promise<ChatResponse> {
  const response = await api.post<ChatResponse>('/chat/ask', payload)
  return response.data
}

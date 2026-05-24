import { api } from './api'
import type { RagAnswerResponse } from '@/types/rag'

export async function answerWithRag(question: string, topK: number): Promise<RagAnswerResponse> {
  const response = await api.post<RagAnswerResponse>('/rag/answer', {
    question,
    top_k: topK,
  })
  return response.data
}


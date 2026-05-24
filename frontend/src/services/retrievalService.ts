import { api } from './api'
import type { RetrievalSearchResponse } from '@/types/retrieval'

export async function searchDocumentChunks(query: string, topK: number): Promise<RetrievalSearchResponse> {
  const response = await api.post<RetrievalSearchResponse>('/retrieval/search', {
    query,
    top_k: topK,
  })
  return response.data
}


export interface ChatRequest {
  question: string
  conversation_id?: string | null
  document_ids: string[]
}

export interface Citation {
  document_id: string
  title: string
  page?: number | null
  snippet: string
}

export interface ChatResponse {
  answer: string
  citations: Citation[]
}

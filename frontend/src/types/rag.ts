import type { RetrievalResult } from './retrieval'

export interface RagSource {
  document_id: string
  document_filename: string
  page_number: number
  chunk_index: number
  chunk_id: string
  similarity: number
  distance: number
  text_preview: string
}

export interface RagAnswerResponse {
  answer: string
  used_sources: RagSource[]
  retrieved_chunks: RetrievalResult[]
  insufficient_evidence: boolean
  provider: string
  model: string
  created_at: string
}


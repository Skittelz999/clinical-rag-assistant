export interface RetrievalResult {
  chunk_id: string
  document_id: string
  document_filename: string
  page_number: number
  chunk_index: number
  text: string
  distance: number
  similarity: number
  embedding_model: string | null
  created_at: string
}

export interface RetrievalSearchResponse {
  query: string
  top_k: number
  results: RetrievalResult[]
}


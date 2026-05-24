export type DocumentStatus = 'uploaded' | 'processing' | 'ready' | 'failed'
export type EmbeddingStatus = 'not_started' | 'pending' | 'processing' | 'embedded' | 'failed'

export interface DocumentItem {
  id: string
  filename: string
  status: DocumentStatus
  size_bytes: number
  created_at: string
  page_count: number
  chunk_count: number
  extracted_char_count: number
  error_message: string | null
  embedding_status: EmbeddingStatus
  embedded_chunk_count: number
  embedding_model: string | null
  embedding_error: string | null
  embedded_at: string | null
}

export interface DocumentChunk {
  id: string
  document_id: string
  chunk_index: number
  page_number: number
  text: string
  char_count: number
  created_at: string
  embedding_status: EmbeddingStatus
  embedding_model: string | null
  embedding_error: string | null
  embedded_at: string | null
}

export interface DocumentChunksResponse {
  document_id: string
  chunks: DocumentChunk[]
}

import { api } from './api'
import type { DocumentChunksResponse, DocumentItem } from '@/types/document'

export async function uploadDocument(file: File): Promise<DocumentItem> {
  const formData = new FormData()
  formData.append('file', file)
  const response = await api.post<DocumentItem>('/documents/upload', formData)
  return response.data
}

export async function listDocuments(): Promise<DocumentItem[]> {
  const response = await api.get<DocumentItem[]>('/documents')
  return response.data
}

export async function getDocument(documentId: string): Promise<DocumentItem> {
  const response = await api.get<DocumentItem>(`/documents/${documentId}`)
  return response.data
}

export async function listDocumentChunks(documentId: string): Promise<DocumentChunksResponse> {
  const response = await api.get<DocumentChunksResponse>(`/documents/${documentId}/chunks`)
  return response.data
}

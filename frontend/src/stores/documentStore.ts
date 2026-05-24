import { defineStore } from 'pinia'
import axios from 'axios'
import { listDocumentChunks, listDocuments, uploadDocument } from '@/services/documentService'
import type { DocumentChunk, DocumentItem } from '@/types/document'

interface DocumentsState {
  documents: DocumentItem[]
  loading: boolean
  uploading: boolean
  listError: string | null
  uploadError: string | null
  successMessage: string | null
  selectedDocumentId: string | null
  chunks: DocumentChunk[]
  chunksLoading: boolean
  chunksError: string | null
}

function getErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail
    if (typeof detail === 'string') return detail
    return error.message
  }

  if (error instanceof Error) return error.message
  return 'Something went wrong. Please try again.'
}

export const useDocumentsStore = defineStore('documents', {
  state: (): DocumentsState => ({
    documents: [],
    loading: false,
    uploading: false,
    listError: null,
    uploadError: null,
    successMessage: null,
    selectedDocumentId: null,
    chunks: [],
    chunksLoading: false,
    chunksError: null,
  }),
  actions: {
    async fetchDocuments() {
      this.loading = true
      this.listError = null

      try {
        this.documents = await listDocuments()
      } catch (error) {
        this.listError = getErrorMessage(error)
      } finally {
        this.loading = false
      }
    },
    async upload(file: File) {
      this.uploading = true
      this.uploadError = null
      this.successMessage = null

      try {
        const uploaded = await uploadDocument(file)
        this.successMessage =
          uploaded.status === 'ready'
            ? `${uploaded.filename} uploaded, processed, and embedded successfully.`
            : `${uploaded.filename} uploaded, but processing failed.`
        await this.fetchDocuments()
        if (uploaded.status === 'ready') {
          await this.loadChunks(uploaded.id)
        } else {
          this.selectedDocumentId = null
          this.chunks = []
        }
      } catch (error) {
        this.uploadError = getErrorMessage(error)
      } finally {
        this.uploading = false
      }
    },
    async toggleChunkPreview(documentId: string) {
      if (this.selectedDocumentId === documentId) {
        this.selectedDocumentId = null
        this.chunks = []
        this.chunksError = null
        return
      }

      await this.loadChunks(documentId)
    },
    async loadChunks(documentId: string) {
      this.selectedDocumentId = documentId
      this.chunksLoading = true
      this.chunksError = null
      this.chunks = []

      try {
        const response = await listDocumentChunks(documentId)
        this.chunks = response.chunks
      } catch (error) {
        this.chunksError = getErrorMessage(error)
      } finally {
        this.chunksLoading = false
      }
    },
  },
})

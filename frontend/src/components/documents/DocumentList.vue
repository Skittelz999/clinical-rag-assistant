<script setup lang="ts">
import type { DocumentChunk, DocumentItem, DocumentStatus, EmbeddingStatus } from '@/types/document'
import { formatDate } from '@/utils/formatDate'
import { cleanPreviewText } from '@/utils/previewText'

defineProps<{
  documents: DocumentItem[]
  loading: boolean
  error: string | null
  selectedDocumentId: string | null
  chunks: DocumentChunk[]
  chunksLoading: boolean
  chunksError: string | null
}>()

defineEmits<{
  refresh: []
  viewChunks: [documentId: string]
}>()

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}

function formatInteger(value: number): string {
  return new Intl.NumberFormat('en').format(value)
}

function statusLabel(status: DocumentStatus): string {
  const labels: Record<DocumentStatus, string> = {
    uploaded: 'Uploaded',
    processing: 'Processing',
    ready: 'Ready',
    failed: 'Failed',
  }
  return labels[status]
}

function statusClass(status: DocumentStatus): string {
  const classes: Record<DocumentStatus, string> = {
    uploaded: 'bg-slate-50 text-slate-700 ring-slate-200',
    processing: 'bg-sky-50 text-sky-700 ring-sky-200',
    ready: 'bg-emerald-50 text-emerald-700 ring-emerald-200',
    failed: 'bg-red-50 text-red-700 ring-red-200',
  }
  return classes[status]
}

function embeddingStatusLabel(status: EmbeddingStatus): string {
  const labels: Record<EmbeddingStatus, string> = {
    not_started: 'Not started',
    pending: 'Pending',
    processing: 'Embedding',
    embedded: 'Embedded',
    failed: 'Failed',
  }
  return labels[status]
}

function embeddingStatusClass(status: EmbeddingStatus): string {
  const classes: Record<EmbeddingStatus, string> = {
    not_started: 'bg-slate-100 text-slate-600 ring-slate-200',
    pending: 'bg-slate-100 text-slate-600 ring-slate-200',
    processing: 'bg-sky-50 text-sky-700 ring-sky-200',
    embedded: 'bg-teal-50 text-teal-700 ring-teal-200',
    failed: 'bg-red-50 text-red-700 ring-red-200',
  }
  return classes[status]
}

function previewText(text: string): string {
  return cleanPreviewText(text, 500)
}
</script>

<template>
  <section class="rounded-2xl border border-slate-200 bg-white shadow-sm">
    <div class="flex flex-wrap items-center justify-between gap-3 border-b border-slate-200 px-5 py-4">
      <div>
        <h3 class="text-lg font-semibold text-slate-950">Uploaded knowledge base</h3>
        <p class="mt-1 text-sm text-slate-600">{{ documents.length }} uploaded documents</p>
      </div>
      <button
        class="rounded-xl border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700 transition hover:bg-slate-50 disabled:opacity-60"
        type="button"
        :disabled="loading"
        @click="$emit('refresh')"
      >
        {{ loading ? 'Refreshing...' : 'Refresh' }}
      </button>
    </div>

    <div v-if="loading" class="space-y-3 p-5">
      <div v-for="item in 3" :key="item" class="h-28 animate-pulse rounded-xl bg-slate-100" />
    </div>

    <div v-else-if="error" class="p-5">
      <div class="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm font-medium text-red-700">
        {{ error }}
      </div>
    </div>

    <div
      v-else-if="documents.length === 0"
      class="flex min-h-72 flex-col items-center justify-center px-6 py-10 text-center"
    >
      <div class="flex h-14 w-14 items-center justify-center rounded-2xl bg-slate-100 text-sm font-bold text-slate-500">
        PDF
      </div>
      <h4 class="mt-4 text-base font-semibold text-slate-950">No documents yet</h4>
      <p class="mt-2 max-w-sm text-sm text-slate-600">
        Upload a guideline PDF to start building the demo clinical knowledge base.
      </p>
    </div>

    <div v-else class="divide-y divide-slate-100">
      <article v-for="document in documents" :key="document.id" class="p-5 transition hover:bg-slate-50">
        <div class="flex items-start justify-between gap-4">
          <div class="min-w-0">
            <p class="truncate font-semibold text-slate-950">{{ document.filename }}</p>
            <p class="mt-1 truncate text-xs text-slate-500">{{ document.id }}</p>
          </div>
          <span
            class="shrink-0 rounded-full px-3 py-1 text-xs font-semibold ring-1 ring-inset"
            :class="statusClass(document.status)"
          >
            {{ statusLabel(document.status) }}
          </span>
        </div>

        <dl class="mt-4 grid gap-3 text-sm sm:grid-cols-2 lg:grid-cols-3">
          <div class="rounded-xl bg-slate-50 px-3 py-2">
            <dt class="text-xs font-semibold uppercase tracking-wide text-slate-500">Uploaded</dt>
            <dd class="mt-1 text-slate-700">{{ formatDate(document.created_at) }}</dd>
          </div>
          <div class="rounded-xl bg-slate-50 px-3 py-2">
            <dt class="text-xs font-semibold uppercase tracking-wide text-slate-500">Size</dt>
            <dd class="mt-1 text-slate-700">{{ formatFileSize(document.size_bytes) }}</dd>
          </div>
          <div class="rounded-xl bg-slate-50 px-3 py-2">
            <dt class="text-xs font-semibold uppercase tracking-wide text-slate-500">Pages</dt>
            <dd class="mt-1 text-slate-700">{{ formatInteger(document.page_count) }}</dd>
          </div>
          <div class="rounded-xl bg-slate-50 px-3 py-2">
            <dt class="text-xs font-semibold uppercase tracking-wide text-slate-500">Chunks</dt>
            <dd class="mt-1 text-slate-700">{{ formatInteger(document.chunk_count) }}</dd>
          </div>
          <div class="rounded-xl bg-slate-50 px-3 py-2">
            <dt class="text-xs font-semibold uppercase tracking-wide text-slate-500">Embeddings</dt>
            <dd class="mt-1 flex flex-wrap items-center gap-2 text-slate-700">
              <span
                class="rounded-full px-2.5 py-1 text-xs font-semibold ring-1 ring-inset"
                :class="embeddingStatusClass(document.embedding_status)"
              >
                {{ embeddingStatusLabel(document.embedding_status) }}
              </span>
              <span class="text-xs text-slate-500">
                {{ formatInteger(document.embedded_chunk_count) }} / {{ formatInteger(document.chunk_count) }}
              </span>
            </dd>
          </div>
          <div class="rounded-xl bg-slate-50 px-3 py-2 sm:col-span-2">
            <dt class="text-xs font-semibold uppercase tracking-wide text-slate-500">Extracted characters</dt>
            <dd class="mt-1 text-slate-700">{{ formatInteger(document.extracted_char_count) }}</dd>
          </div>
        </dl>

        <div
          v-if="document.status === 'uploaded' || document.status === 'processing' || document.embedding_status === 'processing'"
          class="mt-4 flex items-center gap-3 rounded-xl border border-sky-200 bg-sky-50 px-4 py-3 text-sm font-medium text-sky-800"
        >
          <span class="h-4 w-4 animate-spin rounded-full border-2 border-sky-600 border-t-transparent" aria-hidden="true" />
          Processing document: extracting text, creating chunks, and storing embeddings.
        </div>

        <div
          v-if="document.status === 'failed'"
          class="mt-4 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm font-medium text-red-700"
        >
          {{ document.error_message ?? 'Document processing failed.' }}
          <p v-if="document.embedding_error" class="mt-2 text-xs font-medium text-red-600">
            {{ document.embedding_error }}
          </p>
        </div>

        <div v-if="document.status === 'ready'" class="mt-4">
          <button
            class="rounded-xl border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700 transition hover:bg-white disabled:opacity-60"
            type="button"
            :disabled="chunksLoading && selectedDocumentId === document.id"
            @click="$emit('viewChunks', document.id)"
          >
            {{ selectedDocumentId === document.id ? 'Hide chunks' : 'View chunks' }}
          </button>
        </div>

        <div v-if="selectedDocumentId === document.id" class="mt-4 rounded-2xl border border-slate-200 bg-white p-4">
          <div v-if="chunksLoading" class="space-y-3">
            <div v-for="item in 2" :key="item" class="h-24 animate-pulse rounded-xl bg-slate-100" />
          </div>

          <div
            v-else-if="chunksError"
            class="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm font-medium text-red-700"
          >
            {{ chunksError }}
          </div>

          <div v-else-if="chunks.length === 0" class="rounded-xl bg-slate-50 px-4 py-3 text-sm text-slate-600">
            No chunks stored for this document.
          </div>

          <div v-else class="max-h-96 space-y-3 overflow-y-auto pr-1">
            <article v-for="chunk in chunks" :key="chunk.id" class="rounded-xl border border-slate-200 p-4">
              <div class="flex flex-wrap items-center justify-between gap-2">
                <p class="text-sm font-semibold text-slate-950">Chunk {{ chunk.chunk_index }}</p>
                <div class="flex flex-wrap items-center gap-2 text-xs font-medium text-slate-500">
                  <span>Page {{ chunk.page_number }} - {{ formatInteger(chunk.char_count) }} chars</span>
                  <span
                    class="rounded-full px-2 py-0.5 font-semibold ring-1 ring-inset"
                    :class="embeddingStatusClass(chunk.embedding_status)"
                  >
                    {{ embeddingStatusLabel(chunk.embedding_status) }}
                  </span>
                </div>
              </div>
              <p class="mt-3 whitespace-pre-wrap text-sm leading-6 text-slate-700">{{ previewText(chunk.text) }}</p>
            </article>
          </div>
        </div>
      </article>
    </div>
  </section>
</template>

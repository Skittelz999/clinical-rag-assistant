<script setup lang="ts">
import { onMounted } from 'vue'
import { storeToRefs } from 'pinia'
import DocumentAsk from '@/components/documents/DocumentAsk.vue'
import DocumentList from '@/components/documents/DocumentList.vue'
import DocumentSearch from '@/components/documents/DocumentSearch.vue'
import DocumentUploader from '@/components/documents/DocumentUploader.vue'
import { useDocumentsStore } from '@/stores/documentStore'

const documentsStore = useDocumentsStore()
const {
  documents,
  loading,
  uploading,
  listError,
  uploadError,
  successMessage,
  selectedDocumentId,
  chunks,
  chunksLoading,
  chunksError,
} = storeToRefs(documentsStore)

onMounted(() => {
  void documentsStore.fetchDocuments()
})
</script>

<template>
  <section class="mx-auto max-w-6xl">
    <div class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <div class="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p class="text-sm font-semibold uppercase tracking-wide text-slate-500">Knowledge base</p>
          <h2 class="mt-1 text-3xl font-bold text-slate-950">Clinical Documents</h2>
          <p class="mt-3 max-w-2xl text-slate-600">
            Upload synthetic guideline PDFs, inspect extraction and embeddings, then ask grounded questions in Chat.
            This page is the knowledge-base management and debugging area.
          </p>
        </div>
        <div class="flex flex-col items-start gap-3 sm:items-end">
          <div class="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm font-semibold text-amber-900">
            Demo only. Not for medical use.
          </div>
          <RouterLink
            class="rounded-xl border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700 transition hover:bg-slate-50"
            to="/chat"
          >
            Ask assistant
          </RouterLink>
        </div>
      </div>
    </div>

    <div class="mt-6 grid gap-3 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm md:grid-cols-3">
      <div class="rounded-xl bg-slate-50 px-4 py-3">
        <p class="text-xs font-semibold uppercase tracking-wide text-teal-700">1. Upload</p>
        <p class="mt-1 text-sm font-medium text-slate-800">Add a synthetic guideline PDF.</p>
      </div>
      <div class="rounded-xl bg-slate-50 px-4 py-3">
        <p class="text-xs font-semibold uppercase tracking-wide text-teal-700">2. Process</p>
        <p class="mt-1 text-sm font-medium text-slate-800">Wait for Ready and Embedded status.</p>
      </div>
      <div class="rounded-xl bg-slate-50 px-4 py-3">
        <p class="text-xs font-semibold uppercase tracking-wide text-teal-700">3. Ask</p>
        <p class="mt-1 text-sm font-medium text-slate-800">Use Chat for the end-user RAG experience.</p>
      </div>
    </div>

    <div class="mt-6 grid gap-6 xl:grid-cols-[420px_minmax(0,1fr)]">
      <DocumentUploader
        :uploading="uploading"
        :error="uploadError"
        :success-message="successMessage"
        @upload="documentsStore.upload"
      />
      <DocumentList
        :documents="documents"
        :loading="loading"
        :error="listError"
        :selected-document-id="selectedDocumentId"
        :chunks="chunks"
        :chunks-loading="chunksLoading"
        :chunks-error="chunksError"
        @refresh="documentsStore.fetchDocuments"
        @view-chunks="documentsStore.toggleChunkPreview"
      />
    </div>

    <div class="mt-6">
      <DocumentSearch />
    </div>

    <div class="mt-6">
      <DocumentAsk />
    </div>
  </section>
</template>

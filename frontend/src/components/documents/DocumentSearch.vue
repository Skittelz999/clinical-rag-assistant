<script setup lang="ts">
import { ref } from 'vue'
import axios from 'axios'
import { searchDocumentChunks } from '@/services/retrievalService'
import type { RetrievalResult } from '@/types/retrieval'
import { cleanPreviewText } from '@/utils/previewText'

const query = ref('')
const topK = ref(5)
const loading = ref(false)
const error = ref<string | null>(null)
const searched = ref(false)
const results = ref<RetrievalResult[]>([])

function getErrorMessage(errorValue: unknown): string {
  if (axios.isAxiosError(errorValue)) {
    const detail = errorValue.response?.data?.detail
    if (Array.isArray(detail) && detail[0]?.msg) return detail[0].msg
    if (typeof detail === 'string') return detail
    return errorValue.message
  }

  if (errorValue instanceof Error) return errorValue.message
  return 'Search failed. Please try again.'
}

function previewText(text: string): string {
  return cleanPreviewText(text, 650)
}

function formatScore(value: number): string {
  return value.toFixed(3)
}

async function runSearch() {
  const trimmedQuery = query.value.trim()
  if (!trimmedQuery) {
    error.value = 'Enter a search query.'
    results.value = []
    searched.value = false
    return
  }

  loading.value = true
  error.value = null
  searched.value = true

  try {
    const response = await searchDocumentChunks(trimmedQuery, topK.value)
    results.value = response.results
  } catch (searchError) {
    error.value = getErrorMessage(searchError)
    results.value = []
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <section class="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
    <div class="flex flex-wrap items-start justify-between gap-4">
      <div>
        <h3 class="text-lg font-semibold text-slate-950">Semantic search</h3>
        <p class="mt-1 text-sm text-slate-600">Find embedded guideline chunks without generating an answer.</p>
      </div>
      <span class="rounded-full bg-teal-50 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-teal-700">
        pgvector
      </span>
    </div>

    <form class="mt-5 grid gap-3 lg:grid-cols-[minmax(0,1fr)_120px_auto]" @submit.prevent="runSearch">
      <input
        v-model="query"
        class="h-11 rounded-xl border border-slate-300 px-4 text-sm text-slate-950 outline-none transition placeholder:text-slate-400 focus:border-slate-950"
        type="search"
        placeholder="Search embedded document chunks"
      />
      <select
        v-model.number="topK"
        class="h-11 rounded-xl border border-slate-300 bg-white px-3 text-sm font-medium text-slate-700 outline-none transition focus:border-slate-950"
      >
        <option :value="3">Top 3</option>
        <option :value="5">Top 5</option>
        <option :value="10">Top 10</option>
        <option :value="20">Top 20</option>
      </select>
      <button class="btn flex h-11 items-center justify-center gap-2 px-5" type="submit" :disabled="loading">
        <span
          v-if="loading"
          class="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent"
          aria-hidden="true"
        />
        {{ loading ? 'Searching...' : 'Search' }}
      </button>
    </form>

    <p v-if="error" class="mt-4 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm font-medium text-red-700">
      {{ error }}
    </p>

    <div v-if="loading" class="mt-5 grid gap-3 lg:grid-cols-2">
      <div v-for="item in 2" :key="item" class="h-36 animate-pulse rounded-xl bg-slate-100" />
    </div>

    <div v-else-if="searched && results.length === 0 && !error" class="mt-5 rounded-xl bg-slate-50 px-4 py-4 text-sm text-slate-600">
      No embedded chunks matched this query.
    </div>

    <div v-else-if="results.length > 0" class="mt-5 grid gap-3 lg:grid-cols-2">
      <article v-for="result in results" :key="result.chunk_id" class="rounded-xl border border-slate-200 p-4">
        <div class="flex flex-wrap items-start justify-between gap-3">
          <div class="min-w-0">
            <p class="truncate text-sm font-semibold text-slate-950">{{ result.document_filename }}</p>
            <p class="mt-1 text-xs font-medium text-slate-500">
              Page {{ result.page_number }} - Chunk {{ result.chunk_index }}
            </p>
          </div>
          <div class="text-right text-xs font-semibold text-slate-600">
            <p>Similarity {{ formatScore(result.similarity) }}</p>
            <p class="mt-1 text-slate-400">Distance {{ formatScore(result.distance) }}</p>
          </div>
        </div>
        <p class="mt-3 whitespace-pre-wrap text-sm leading-6 text-slate-700">{{ previewText(result.text) }}</p>
      </article>
    </div>
  </section>
</template>

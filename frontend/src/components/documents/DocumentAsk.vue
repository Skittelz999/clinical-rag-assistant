<script setup lang="ts">
import { ref } from 'vue'
import axios from 'axios'
import { answerWithRag } from '@/services/ragService'
import type { RagAnswerResponse } from '@/types/rag'
import { cleanPreviewText } from '@/utils/previewText'

const question = ref('')
const topK = ref(5)
const loading = ref(false)
const error = ref<string | null>(null)
const answer = ref<RagAnswerResponse | null>(null)

function getErrorMessage(errorValue: unknown): string {
  if (axios.isAxiosError(errorValue)) {
    const detail = errorValue.response?.data?.detail
    if (Array.isArray(detail) && detail[0]?.msg) return detail[0].msg
    if (typeof detail === 'string') return detail
    return errorValue.message
  }

  if (errorValue instanceof Error) return errorValue.message
  return 'Answer generation failed. Please try again.'
}

function formatScore(value: number): string {
  return value.toFixed(3)
}

function previewText(text: string): string {
  return cleanPreviewText(text, 500)
}

async function askQuestion() {
  const trimmedQuestion = question.value.trim()
  if (!trimmedQuestion) {
    error.value = 'Enter a question.'
    answer.value = null
    return
  }

  loading.value = true
  error.value = null

  try {
    answer.value = await answerWithRag(trimmedQuestion, topK.value)
  } catch (answerError) {
    error.value = getErrorMessage(answerError)
    answer.value = null
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <section class="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
    <div class="flex flex-wrap items-start justify-between gap-4">
      <div>
        <h3 class="text-lg font-semibold text-slate-950">Ask uploaded documents</h3>
        <p class="mt-1 text-sm text-slate-600">Generate a grounded demo answer from retrieved chunks.</p>
      </div>
      <span class="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-slate-600">
        RAG demo
      </span>
    </div>

    <div class="mt-5 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm font-medium text-amber-900">
      Demo only. Not medical advice. Do not use for diagnosis or treatment decisions.
    </div>

    <form class="mt-5 grid gap-3" @submit.prevent="askQuestion">
      <textarea
        v-model="question"
        class="min-h-28 rounded-xl border border-slate-300 px-4 py-3 text-sm leading-6 text-slate-950 outline-none transition placeholder:text-slate-400 focus:border-slate-950"
        placeholder="Ask a question about the uploaded guideline documents"
      />
      <div class="flex flex-wrap items-center gap-3">
        <select
          v-model.number="topK"
          class="h-11 rounded-xl border border-slate-300 bg-white px-3 text-sm font-medium text-slate-700 outline-none transition focus:border-slate-950"
        >
          <option :value="3">Top 3 sources</option>
          <option :value="5">Top 5 sources</option>
          <option :value="10">Top 10 sources</option>
        </select>
        <button class="btn flex h-11 items-center justify-center gap-2 px-5" type="submit" :disabled="loading">
          <span
            v-if="loading"
            class="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent"
            aria-hidden="true"
          />
          {{ loading ? 'Generating...' : 'Ask' }}
        </button>
      </div>
    </form>

    <p v-if="error" class="mt-4 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm font-medium text-red-700">
      {{ error }}
    </p>

    <div v-if="loading" class="mt-5 space-y-3">
      <div class="h-28 animate-pulse rounded-xl bg-slate-100" />
      <div class="h-24 animate-pulse rounded-xl bg-slate-100" />
    </div>

    <div v-else-if="answer" class="mt-5 space-y-4">
      <div
        class="rounded-xl border px-4 py-4"
        :class="answer.insufficient_evidence ? 'border-amber-200 bg-amber-50' : 'border-slate-200 bg-slate-50'"
      >
        <p v-if="answer.insufficient_evidence" class="mb-2 text-sm font-semibold text-amber-900">
          Insufficient evidence
        </p>
        <p class="whitespace-pre-wrap text-sm leading-6 text-slate-800">{{ answer.answer }}</p>
        <p class="mt-3 text-xs font-medium text-slate-500">
          {{ answer.provider }} / {{ answer.model }}
        </p>
      </div>

      <div v-if="answer.used_sources.length > 0">
        <h4 class="text-sm font-semibold text-slate-950">Sources</h4>
        <div class="mt-3 grid gap-3 lg:grid-cols-2">
          <article v-for="source in answer.used_sources" :key="source.chunk_id" class="rounded-xl border border-slate-200 p-4">
            <div class="flex flex-wrap items-start justify-between gap-3">
              <div class="min-w-0">
                <p class="truncate text-sm font-semibold text-slate-950">{{ source.document_filename }}</p>
                <p class="mt-1 text-xs font-medium text-slate-500">
                  Page {{ source.page_number }} - Chunk {{ source.chunk_index }}
                </p>
              </div>
              <div class="text-right text-xs font-semibold text-slate-600">
                <p>Similarity {{ formatScore(source.similarity) }}</p>
                <p class="mt-1 text-slate-400">Distance {{ formatScore(source.distance) }}</p>
              </div>
            </div>
            <p class="mt-3 whitespace-pre-wrap text-sm leading-6 text-slate-700">{{ previewText(source.text_preview) }}</p>
          </article>
        </div>
      </div>

      <div
        v-else-if="answer.insufficient_evidence"
        class="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm font-medium text-amber-900"
      >
        No source chunks were strong enough to support an answer.
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, ref } from 'vue'
import axios from 'axios'
import { RouterLink } from 'vue-router'
import { listDocuments } from '@/services/documentService'
import { answerWithRag } from '@/services/ragService'
import type { DocumentItem } from '@/types/document'
import type { RagAnswerResponse, RagSource } from '@/types/rag'
import { cleanPreviewText } from '@/utils/previewText'

type ChatMessageStatus = 'loading' | 'success' | 'error'

interface ChatTurn {
  id: string
  question: string
  status: ChatMessageStatus
  answer: string
  sources: RagSource[]
  insufficientEvidence: boolean
  error: string | null
  provider: string | null
  model: string | null
}

const exampleQuestions = [
  'What is the first-line management pathway for Condition G?',
  'What emergency warning signs require urgent escalation?',
  'When should follow-up happen?',
  'What are the contraindications for MetaboLite-A?',
]

const question = ref('')
const topK = ref(5)
const submitting = ref(false)
const documentsLoading = ref(false)
const documentsError = ref<string | null>(null)
const documents = ref<DocumentItem[]>([])
const chatTurns = ref<ChatTurn[]>([])
const transcriptEnd = ref<HTMLElement | null>(null)

const readyEmbeddedDocuments = computed(() =>
  documents.value.filter(
    (document) =>
      document.status === 'ready' &&
      document.embedding_status === 'embedded' &&
      document.chunk_count > 0 &&
      document.embedded_chunk_count > 0,
  ),
)

const processingDocuments = computed(() =>
  documents.value.filter(
    (document) =>
      document.status === 'uploaded' ||
      document.status === 'processing' ||
      document.embedding_status === 'pending' ||
      document.embedding_status === 'processing',
  ),
)

const failedDocuments = computed(() =>
  documents.value.filter((document) => document.status === 'failed' || document.embedding_status === 'failed'),
)

const knowledgeBaseLabel = computed(() => {
  if (documentsLoading.value) return 'Checking knowledge base'
  if (documents.value.length === 0) return 'No documents uploaded'
  if (readyEmbeddedDocuments.value.length === 0) return 'Documents not ready'
  return `${readyEmbeddedDocuments.value.length} ready document${readyEmbeddedDocuments.value.length === 1 ? '' : 's'}`
})

const readinessMessage = computed(() => {
  if (documentsLoading.value || readyEmbeddedDocuments.value.length > 0) return null
  if (documents.value.length === 0) {
    return 'Upload a synthetic guideline PDF on the Documents page before asking questions.'
  }
  if (processingDocuments.value.length > 0) {
    return 'A document is processing. Wait for Ready and Embedded status before asking questions.'
  }
  if (failedDocuments.value.length > 0) {
    return 'No ready embedded documents are available. Review the failed upload on the Documents page.'
  }
  return 'No ready embedded documents are available yet.'
})

const canAsk = computed(() => !submitting.value)

onMounted(() => {
  void refreshDocuments()
})

async function refreshDocuments() {
  documentsLoading.value = true
  documentsError.value = null

  try {
    documents.value = await listDocuments()
  } catch (error) {
    documentsError.value = getErrorMessage(error)
  } finally {
    documentsLoading.value = false
  }
}

async function submitQuestion(questionText = question.value) {
  const trimmedQuestion = questionText.trim()
  if (!trimmedQuestion || submitting.value) return

  question.value = ''
  submitting.value = true
  documentsError.value = null

  const turn: ChatTurn = {
    id: crypto.randomUUID(),
    question: trimmedQuestion,
    status: 'loading',
    answer: '',
    sources: [],
    insufficientEvidence: false,
    error: null,
    provider: null,
    model: null,
  }
  chatTurns.value.push(turn)
  await scrollToLatest()

  try {
    await refreshDocuments()
    const readinessError = getReadinessError()
    if (readinessError) {
      applyTurnError(turn.id, readinessError)
      return
    }

    const response = await answerWithRag(trimmedQuestion, topK.value)
    applyTurnAnswer(turn.id, response)
  } catch (error) {
    applyTurnError(turn.id, getErrorMessage(error))
  } finally {
    submitting.value = false
    await scrollToLatest()
  }
}

function useExample(questionText: string) {
  void submitQuestion(questionText)
}

function applyTurnAnswer(turnId: string, response: RagAnswerResponse) {
  const turn = chatTurns.value.find((item) => item.id === turnId)
  if (!turn) return

  turn.status = 'success'
  turn.answer = response.answer
  turn.sources = response.used_sources
  turn.insufficientEvidence = response.insufficient_evidence
  turn.provider = response.provider
  turn.model = response.model
}

function applyTurnError(turnId: string, message: string) {
  const turn = chatTurns.value.find((item) => item.id === turnId)
  if (!turn) return

  turn.status = 'error'
  turn.answer = ''
  turn.sources = []
  turn.error = message
  turn.insufficientEvidence = false
}

function getReadinessError(): string | null {
  if (documents.value.length === 0) {
    return 'No documents uploaded yet. Upload a synthetic guideline PDF on the Documents page first.'
  }

  if (readyEmbeddedDocuments.value.length === 0 && processingDocuments.value.length > 0) {
    return 'Documents are still processing. Wait until a document is Ready and embeddings are Embedded, then ask again.'
  }

  if (readyEmbeddedDocuments.value.length === 0 && failedDocuments.value.length > 0) {
    return 'No ready embedded documents are available. Check the failed document on the Documents page and retry the upload.'
  }

  if (readyEmbeddedDocuments.value.length === 0) {
    return 'No ready embedded documents are available yet.'
  }

  return null
}

function getErrorMessage(errorValue: unknown): string {
  if (axios.isAxiosError(errorValue)) {
    const detail = errorValue.response?.data?.detail
    const message = Array.isArray(detail) && detail[0]?.msg ? detail[0].msg : detail

    if (typeof message === 'string') {
      if (message.includes('Embedding provider failed')) {
        return 'Embedding provider failure. Check the embedding provider/API key configuration and try again.'
      }
      if (message.includes('Answer generation provider failed')) {
        return 'LLM provider failure. Check the LLM provider/API key configuration and try again.'
      }
      return message
    }

    return errorValue.message
  }

  if (errorValue instanceof Error) return errorValue.message
  return 'Answer generation failed. Please try again.'
}

function formatScore(value: number): string {
  return value.toFixed(3)
}

function previewText(text: string): string {
  return cleanPreviewText(text, 520)
}

async function scrollToLatest() {
  await nextTick()
  transcriptEnd.value?.scrollIntoView({ behavior: 'smooth', block: 'end' })
}
</script>

<template>
  <section class="mx-auto flex max-w-6xl flex-col gap-6">
    <header class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <div class="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p class="text-sm font-semibold uppercase tracking-wide text-slate-500">Clinical assistant</p>
          <h2 class="mt-1 text-3xl font-bold text-slate-950">Ask uploaded guideline documents</h2>
          <p class="mt-3 max-w-2xl text-slate-600">
            Chat with the embedded knowledge base. Answers are generated from retrieved chunks and include source cards.
          </p>
        </div>
        <div class="flex flex-col items-start gap-2 sm:items-end">
          <div class="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm font-semibold text-amber-900">
            Demo only. Not for medical use.
          </div>
          <button
            class="rounded-xl border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700 transition hover:bg-slate-50 disabled:opacity-60"
            type="button"
            :disabled="documentsLoading"
            @click="refreshDocuments"
          >
            {{ documentsLoading ? 'Checking...' : 'Refresh knowledge base' }}
          </button>
        </div>
      </div>

      <div class="mt-5 grid gap-3 text-sm sm:grid-cols-3">
        <div class="rounded-xl bg-slate-50 px-4 py-3">
          <p class="text-xs font-semibold uppercase tracking-wide text-slate-500">Status</p>
          <p class="mt-1 font-semibold text-slate-900">{{ knowledgeBaseLabel }}</p>
        </div>
        <div class="rounded-xl bg-slate-50 px-4 py-3">
          <p class="text-xs font-semibold uppercase tracking-wide text-slate-500">Embedded chunks</p>
          <p class="mt-1 font-semibold text-slate-900">
            {{ readyEmbeddedDocuments.reduce((total, document) => total + document.embedded_chunk_count, 0) }}
          </p>
        </div>
        <div class="rounded-xl bg-slate-50 px-4 py-3">
          <p class="text-xs font-semibold uppercase tracking-wide text-slate-500">Retrieval depth</p>
          <p class="mt-1 font-semibold text-slate-900">Top {{ topK }} sources</p>
        </div>
      </div>

      <p
        v-if="documentsError"
        class="mt-4 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm font-medium text-red-700"
      >
        {{ documentsError }}
      </p>

      <div
        v-else-if="readinessMessage"
        class="mt-4 flex flex-wrap items-center justify-between gap-3 rounded-xl border border-sky-200 bg-sky-50 px-4 py-3 text-sm text-sky-900"
      >
        <p class="font-medium">{{ readinessMessage }}</p>
        <RouterLink class="font-semibold underline underline-offset-2" to="/documents">Open Documents</RouterLink>
      </div>
    </header>

    <div class="grid gap-6 xl:grid-cols-[minmax(0,1fr)_320px]">
      <main class="rounded-2xl border border-slate-200 bg-white shadow-sm">
        <div class="border-b border-slate-200 px-5 py-4">
          <h3 class="text-lg font-semibold text-slate-950">Conversation</h3>
          <p class="mt-1 text-sm text-slate-600">Session-only history. Conversations are not stored.</p>
        </div>

        <div class="min-h-[520px] space-y-5 px-5 py-5">
          <div
            v-if="chatTurns.length === 0"
            class="flex min-h-[420px] flex-col items-center justify-center rounded-2xl bg-slate-50 px-6 py-10 text-center"
          >
            <div class="flex h-14 w-14 items-center justify-center rounded-2xl bg-slate-950 text-sm font-bold text-white">
              AI
            </div>
            <h3 class="mt-4 text-lg font-semibold text-slate-950">Ask a question to start</h3>
            <p class="mt-2 max-w-lg text-sm leading-6 text-slate-600">
              Use the uploaded clinical guideline PDFs as the answer source. The assistant will show sources when the
              documents contain enough evidence.
            </p>
            <RouterLink
              v-if="documents.length === 0 && !documentsLoading"
              class="mt-4 rounded-xl border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-700 transition hover:bg-slate-50"
              to="/documents"
            >
              Upload documents
            </RouterLink>
          </div>

          <article v-for="turn in chatTurns" :key="turn.id" class="space-y-4">
            <div class="flex justify-end">
              <div class="max-w-3xl rounded-2xl bg-slate-950 px-4 py-3 text-sm leading-6 text-white shadow-sm">
                {{ turn.question }}
              </div>
            </div>

            <div class="flex justify-start">
              <div class="w-full max-w-4xl rounded-2xl border border-slate-200 bg-slate-50 px-4 py-4">
                <div v-if="turn.status === 'loading'" class="flex items-center gap-3 text-sm font-medium text-slate-600">
                  <span
                    class="h-4 w-4 animate-spin rounded-full border-2 border-slate-500 border-t-transparent"
                    aria-hidden="true"
                  />
                  Retrieving sources and generating a grounded answer...
                </div>

                <div
                  v-else-if="turn.status === 'error'"
                  class="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm font-medium text-red-700"
                >
                  {{ turn.error }}
                  <RouterLink class="ml-1 underline underline-offset-2" to="/documents">
                    Open Documents
                  </RouterLink>
                </div>

                <div v-else>
                  <div
                    class="rounded-xl border px-4 py-4"
                    :class="
                      turn.insufficientEvidence
                        ? 'border-amber-200 bg-amber-50 text-amber-950'
                        : 'border-white bg-white text-slate-800'
                    "
                  >
                    <p v-if="turn.insufficientEvidence" class="mb-2 text-sm font-semibold text-amber-900">
                      Insufficient evidence
                    </p>
                    <p class="whitespace-pre-wrap text-sm leading-6">{{ turn.answer }}</p>
                    <p v-if="turn.provider && turn.model" class="mt-3 text-xs font-medium text-slate-500">
                      {{ turn.provider }} / {{ turn.model }}
                    </p>
                  </div>

                  <div v-if="turn.sources.length > 0" class="mt-4">
                    <h4 class="text-sm font-semibold text-slate-950">Sources</h4>
                    <div class="mt-3 grid gap-3 lg:grid-cols-2">
                      <article
                        v-for="(source, index) in turn.sources"
                        :key="source.chunk_id"
                        class="rounded-xl border border-slate-200 bg-white p-4"
                      >
                        <div class="flex flex-wrap items-start justify-between gap-3">
                          <div class="min-w-0">
                            <p class="text-xs font-semibold uppercase tracking-wide text-teal-700">
                              Source {{ index + 1 }}
                            </p>
                            <p class="mt-1 truncate text-sm font-semibold text-slate-950">
                              {{ source.document_filename }}
                            </p>
                            <p class="mt-1 text-xs font-medium text-slate-500">
                              Page {{ source.page_number }} - Chunk {{ source.chunk_index }}
                            </p>
                          </div>
                          <div class="text-right text-xs font-semibold text-slate-600">
                            <p>Similarity {{ formatScore(source.similarity) }}</p>
                            <p class="mt-1 text-slate-400">Distance {{ formatScore(source.distance) }}</p>
                          </div>
                        </div>
                        <p class="mt-3 whitespace-pre-wrap text-sm leading-6 text-slate-700">
                          {{ previewText(source.text_preview) }}
                        </p>
                      </article>
                    </div>
                  </div>

                  <div
                    v-else-if="turn.insufficientEvidence"
                    class="mt-4 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm font-medium text-amber-900"
                  >
                    No retrieved chunks were strong enough to support an answer.
                  </div>
                </div>
              </div>
            </div>
          </article>
          <div ref="transcriptEnd" />
        </div>

        <form class="border-t border-slate-200 p-5" @submit.prevent="submitQuestion()">
          <label class="sr-only" for="chat-question">Question</label>
          <textarea
            id="chat-question"
            v-model="question"
            class="min-h-28 w-full resize-y rounded-xl border border-slate-300 px-4 py-3 text-sm leading-6 text-slate-950 outline-none transition placeholder:text-slate-400 focus:border-slate-950"
            placeholder="Ask about uploaded guideline documents"
            @keydown.ctrl.enter.prevent="submitQuestion()"
          />
          <div class="mt-3 flex flex-wrap items-center justify-between gap-3">
            <div class="flex flex-wrap items-center gap-3">
              <select
                v-model.number="topK"
                class="h-11 rounded-xl border border-slate-300 bg-white px-3 text-sm font-medium text-slate-700 outline-none transition focus:border-slate-950"
              >
                <option :value="3">Top 3 sources</option>
                <option :value="5">Top 5 sources</option>
                <option :value="8">Top 8 sources</option>
                <option :value="10">Top 10 sources</option>
              </select>
              <p class="text-xs font-medium text-slate-500">Ctrl + Enter to send</p>
            </div>
            <button class="btn flex h-11 items-center justify-center gap-2 px-5" type="submit" :disabled="!canAsk">
              <span
                v-if="submitting"
                class="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent"
                aria-hidden="true"
              />
              {{ submitting ? 'Generating...' : 'Ask assistant' }}
            </button>
          </div>
        </form>
      </main>

      <aside class="space-y-4">
        <section class="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <h3 class="text-sm font-semibold uppercase tracking-wide text-slate-500">Example questions</h3>
          <div class="mt-4 space-y-2">
            <button
              v-for="example in exampleQuestions"
              :key="example"
              class="w-full rounded-xl border border-slate-200 px-3 py-3 text-left text-sm font-medium leading-5 text-slate-700 transition hover:border-slate-300 hover:bg-slate-50 disabled:opacity-60"
              type="button"
              :disabled="submitting"
              @click="useExample(example)"
            >
              {{ example }}
            </button>
          </div>
        </section>

        <section class="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <h3 class="text-sm font-semibold uppercase tracking-wide text-slate-500">Knowledge base</h3>
          <dl class="mt-4 space-y-3 text-sm">
            <div class="flex items-center justify-between gap-4">
              <dt class="text-slate-500">Uploaded</dt>
              <dd class="font-semibold text-slate-950">{{ documents.length }}</dd>
            </div>
            <div class="flex items-center justify-between gap-4">
              <dt class="text-slate-500">Ready + embedded</dt>
              <dd class="font-semibold text-slate-950">{{ readyEmbeddedDocuments.length }}</dd>
            </div>
            <div class="flex items-center justify-between gap-4">
              <dt class="text-slate-500">Processing</dt>
              <dd class="font-semibold text-slate-950">{{ processingDocuments.length }}</dd>
            </div>
            <div class="flex items-center justify-between gap-4">
              <dt class="text-slate-500">Failed</dt>
              <dd class="font-semibold text-slate-950">{{ failedDocuments.length }}</dd>
            </div>
          </dl>
          <RouterLink
            class="mt-5 block rounded-xl border border-slate-300 px-4 py-2 text-center text-sm font-semibold text-slate-700 transition hover:bg-slate-50"
            to="/documents"
          >
            Manage documents
          </RouterLink>
        </section>
      </aside>
    </div>
  </section>
</template>

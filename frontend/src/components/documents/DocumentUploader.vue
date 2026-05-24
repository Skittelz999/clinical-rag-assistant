<script setup lang="ts">
import { computed, ref } from 'vue'

defineProps<{
  uploading: boolean
  error: string | null
  successMessage: string | null
}>()

const emit = defineEmits<{
  upload: [file: File]
}>()

const fileInput = ref<HTMLInputElement | null>(null)
const selectedFile = ref<File | null>(null)
const isDragging = ref(false)

const selectedFileIsPdf = computed(() => {
  if (!selectedFile.value) return false
  return selectedFile.value.type === 'application/pdf' || selectedFile.value.name.toLowerCase().endsWith('.pdf')
})

const selectedFileSize = computed(() => {
  if (!selectedFile.value) return ''
  return formatFileSize(selectedFile.value.size)
})

const validationMessage = computed(() => {
  if (!selectedFile.value || selectedFileIsPdf.value) return null
  return 'Select a PDF file before uploading.'
})

function openFilePicker() {
  fileInput.value?.click()
}

function handleFileChange(event: Event) {
  const input = event.target as HTMLInputElement
  selectedFile.value = input.files?.[0] ?? null
}

function handleDrop(event: DragEvent) {
  isDragging.value = false
  selectedFile.value = event.dataTransfer?.files?.[0] ?? null
}

function uploadSelectedFile() {
  if (!selectedFile.value || !selectedFileIsPdf.value) return
  emit('upload', selectedFile.value)
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}
</script>

<template>
  <section class="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
    <div class="flex items-start justify-between gap-4">
      <div>
        <h3 class="text-lg font-semibold text-slate-950">Upload documents</h3>
        <p class="mt-1 text-sm text-slate-600">Add clinical guideline PDFs to the demo knowledge base.</p>
      </div>
      <span class="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-slate-600">
        PDF only
      </span>
    </div>

    <div class="mt-5 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm font-medium text-amber-900">
      Demo only. Not for medical use. Do not upload real patient data.
    </div>

    <input
      ref="fileInput"
      class="hidden"
      type="file"
      accept="application/pdf,.pdf"
      @change="handleFileChange"
    />

    <div
      class="mt-5 flex min-h-48 cursor-pointer flex-col items-center justify-center rounded-2xl border-2 border-dashed px-6 py-8 text-center transition"
      :class="isDragging ? 'border-slate-950 bg-slate-50' : 'border-slate-300 bg-white hover:border-slate-500'"
      role="button"
      tabindex="0"
      @click="openFilePicker"
      @keydown.enter.prevent="openFilePicker"
      @keydown.space.prevent="openFilePicker"
      @dragenter.prevent="isDragging = true"
      @dragover.prevent="isDragging = true"
      @dragleave.prevent="isDragging = false"
      @drop.prevent="handleDrop"
    >
      <div class="flex h-12 w-12 items-center justify-center rounded-2xl bg-slate-950 text-sm font-bold text-white">
        PDF
      </div>
      <p class="mt-4 text-sm font-semibold text-slate-950">Drop a PDF here or browse</p>
      <p class="mt-1 text-xs text-slate-500">Maximum demo upload size: 10 MB</p>
    </div>

    <div v-if="selectedFile" class="mt-4 rounded-xl border border-slate-200 bg-slate-50 p-4">
      <p class="truncate text-sm font-semibold text-slate-950">{{ selectedFile.name }}</p>
      <p class="mt-1 text-xs text-slate-500">{{ selectedFileSize }}</p>
      <p v-if="validationMessage" class="mt-2 text-sm font-medium text-red-700">{{ validationMessage }}</p>
    </div>

    <p v-if="error" class="mt-4 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm font-medium text-red-700">
      {{ error }}
    </p>
    <p
      v-if="successMessage"
      class="mt-4 rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm font-medium text-emerald-700"
    >
      {{ successMessage }}
    </p>

    <button
      class="btn mt-5 flex w-full items-center justify-center gap-2"
      type="button"
      :disabled="!selectedFile || !selectedFileIsPdf || uploading"
      @click="uploadSelectedFile"
    >
      <span
        v-if="uploading"
        class="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent"
        aria-hidden="true"
      />
      {{ uploading ? 'Uploading...' : 'Upload document' }}
    </button>
    <p v-if="uploading" class="mt-3 text-center text-xs font-medium text-slate-500">
      Uploading, extracting text, chunking, and embedding the document.
    </p>
  </section>
</template>

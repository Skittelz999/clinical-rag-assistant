<template>
  <section class="mx-auto max-w-6xl space-y-6">
    <header class="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
      <div class="grid gap-6 p-6 xl:grid-cols-[minmax(0,1fr)_420px]">
        <div class="flex flex-col justify-center">
          <p class="text-sm font-semibold uppercase tracking-wide text-teal-700">Clinical RAG Assistant</p>
          <h2 class="mt-3 max-w-3xl text-4xl font-bold tracking-normal text-slate-950">
            Ask grounded questions across uploaded clinical guideline PDFs.
          </h2>
          <p class="mt-4 max-w-2xl text-base leading-7 text-slate-600">
            Upload synthetic guideline documents, extract and embed page-level chunks, then ask questions with
            transparent source cards. Built as a portfolio-ready HealthTech AI SaaS prototype.
          </p>

          <div class="mt-6 flex flex-wrap gap-3">
            <RouterLink class="btn" to="/documents">Upload documents</RouterLink>
            <RouterLink
              class="rounded-xl border border-slate-300 bg-white px-5 py-3 text-sm font-semibold text-slate-700 transition hover:bg-slate-50"
              to="/chat"
            >
              Ask assistant
            </RouterLink>
          </div>

          <div class="mt-6 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm font-semibold text-amber-900">
            Demo only. Not for medical use. Do not upload real patient data.
          </div>
        </div>

        <div class="rounded-2xl border border-slate-200 bg-slate-50 p-4">
          <div class="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
            <div class="flex items-center justify-between gap-3 border-b border-slate-100 pb-3">
              <div>
                <p class="text-xs font-semibold uppercase tracking-wide text-slate-500">Answer preview</p>
                <p class="mt-1 text-sm font-semibold text-slate-950">Emergency warning signs</p>
              </div>
              <span class="rounded-full bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-700">
                grounded
              </span>
            </div>

            <p class="mt-4 text-sm leading-6 text-slate-700">
              Emergency warning signs require urgent escalation and should override routine follow-up.
            </p>

            <div class="mt-4 grid gap-3">
              <div class="rounded-xl border border-slate-200 p-3">
                <p class="text-xs font-semibold uppercase tracking-wide text-teal-700">Source 1</p>
                <p class="mt-1 truncate text-sm font-semibold text-slate-950">synthetic-clinical-guideline.pdf</p>
                <p class="mt-1 text-xs font-medium text-slate-500">Page 4 - Chunk 6 - Similarity 0.84</p>
                <p class="mt-2 text-sm leading-5 text-slate-600">
                  Severe chest pain, sudden confusion, severe shortness of breath, and rapidly worsening symptoms.
                </p>
              </div>
              <div class="rounded-xl border border-slate-200 p-3">
                <p class="text-xs font-semibold uppercase tracking-wide text-teal-700">Source 2</p>
                <p class="mt-1 truncate text-sm font-semibold text-slate-950">condition-g-demo-pathway.pdf</p>
                <p class="mt-1 text-xs font-medium text-slate-500">Page 2 - Chunk 3 - Similarity 0.79</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </header>

    <section class="grid gap-4 md:grid-cols-4">
      <div class="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
        <p class="text-sm font-semibold text-slate-950">Upload PDFs</p>
        <p class="mt-2 text-sm leading-6 text-slate-600">Manage synthetic clinical guideline documents.</p>
      </div>
      <div class="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
        <p class="text-sm font-semibold text-slate-950">Embed chunks</p>
        <p class="mt-2 text-sm leading-6 text-slate-600">Extract page text, chunk it, and store vectors.</p>
      </div>
      <div class="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
        <p class="text-sm font-semibold text-slate-950">Retrieve evidence</p>
        <p class="mt-2 text-sm leading-6 text-slate-600">Use pgvector similarity search over ready chunks.</p>
      </div>
      <div class="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
        <p class="text-sm font-semibold text-slate-950">Answer with sources</p>
        <p class="mt-2 text-sm leading-6 text-slate-600">Generate grounded answers with visible citations.</p>
      </div>
    </section>

    <section class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <div class="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p class="text-sm font-semibold uppercase tracking-wide text-slate-500">How it works</p>
          <h3 class="mt-1 text-2xl font-bold text-slate-950">A complete document-to-answer RAG flow</h3>
        </div>
        <RouterLink
          class="rounded-xl border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700 transition hover:bg-slate-50"
          to="/chat"
        >
          Try the assistant
        </RouterLink>
      </div>

      <div class="mt-6 grid gap-4 lg:grid-cols-4">
        <article class="rounded-xl bg-slate-50 p-4">
          <p class="text-xs font-semibold uppercase tracking-wide text-teal-700">Step 1</p>
          <h4 class="mt-2 font-semibold text-slate-950">Upload guideline documents</h4>
          <p class="mt-2 text-sm leading-6 text-slate-600">Add safe synthetic PDFs from the Documents page.</p>
        </article>
        <article class="rounded-xl bg-slate-50 p-4">
          <p class="text-xs font-semibold uppercase tracking-wide text-teal-700">Step 2</p>
          <h4 class="mt-2 font-semibold text-slate-950">Extract and embed chunks</h4>
          <p class="mt-2 text-sm leading-6 text-slate-600">Persist page-level chunks and embedding metadata.</p>
        </article>
        <article class="rounded-xl bg-slate-50 p-4">
          <p class="text-xs font-semibold uppercase tracking-wide text-teal-700">Step 3</p>
          <h4 class="mt-2 font-semibold text-slate-950">Retrieve relevant evidence</h4>
          <p class="mt-2 text-sm leading-6 text-slate-600">Search embedded chunks using vector similarity.</p>
        </article>
        <article class="rounded-xl bg-slate-50 p-4">
          <p class="text-xs font-semibold uppercase tracking-wide text-teal-700">Step 4</p>
          <h4 class="mt-2 font-semibold text-slate-950">Generate grounded answers</h4>
          <p class="mt-2 text-sm leading-6 text-slate-600">Answer only from retrieved context and show sources.</p>
        </article>
      </div>
    </section>

    <section class="grid gap-6 lg:grid-cols-[minmax(0,1fr)_360px]">
      <div class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <p class="text-sm font-semibold uppercase tracking-wide text-slate-500">Architecture</p>
        <h3 class="mt-1 text-2xl font-bold text-slate-950">Built like a practical SaaS MVP</h3>
        <div class="mt-5 grid gap-3 sm:grid-cols-2">
          <div class="rounded-xl bg-slate-50 px-4 py-3">
            <p class="font-semibold text-slate-950">FastAPI backend</p>
            <p class="mt-1 text-sm text-slate-600">Typed API endpoints and service/repository layers.</p>
          </div>
          <div class="rounded-xl bg-slate-50 px-4 py-3">
            <p class="font-semibold text-slate-950">PostgreSQL + pgvector</p>
            <p class="mt-1 text-sm text-slate-600">Persistent documents, chunks, and embeddings.</p>
          </div>
          <div class="rounded-xl bg-slate-50 px-4 py-3">
            <p class="font-semibold text-slate-950">Vue + TypeScript</p>
            <p class="mt-1 text-sm text-slate-600">Documents workflow and end-user chat UI.</p>
          </div>
          <div class="rounded-xl bg-slate-50 px-4 py-3">
            <p class="font-semibold text-slate-950">OpenAI-compatible AI</p>
            <p class="mt-1 text-sm text-slate-600">Provider abstractions for embeddings and LLMs.</p>
          </div>
        </div>
      </div>

      <aside class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <p class="text-sm font-semibold uppercase tracking-wide text-slate-500">Demo checklist</p>
        <ol class="mt-4 space-y-3 text-sm leading-6 text-slate-700">
          <li>1. Start Docker Compose.</li>
          <li>2. Upload a synthetic guideline PDF.</li>
          <li>3. Confirm Ready and Embedded status.</li>
          <li>4. Ask example questions in Chat.</li>
          <li>5. Inspect answer source cards.</li>
        </ol>
      </aside>
    </section>
  </section>
</template>

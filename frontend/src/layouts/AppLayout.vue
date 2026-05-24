<template>
  <div class="min-h-screen bg-slate-50 text-slate-950">
    <aside class="fixed inset-y-0 left-0 w-64 border-r bg-white p-5">
      <div class="mb-8">
        <p class="text-xs font-semibold uppercase tracking-wide text-slate-500">HealthTech SaaS</p>
        <h1 class="text-xl font-bold">Clinical RAG</h1>
      </div>
      <nav class="space-y-2 text-sm font-medium">
        <RouterLink active-class="" class="nav-link" exact-active-class="router-link-active" to="/">Home</RouterLink>
        <RouterLink active-class="" class="nav-link" exact-active-class="router-link-active" to="/chat">Chat</RouterLink>
        <RouterLink active-class="" class="nav-link" exact-active-class="router-link-active" to="/documents">
          Documents
        </RouterLink>
      </nav>
      <div class="mt-6 rounded-xl border border-slate-200 bg-slate-50 p-3 text-xs leading-5 text-slate-600">
        Upload PDFs in Documents, then ask grounded questions in Chat.
      </div>
      <div class="absolute bottom-5 left-5 right-5 rounded-xl bg-amber-50 p-3 text-xs text-amber-900">
        Demo only. Not for medical use. Do not upload real patient data.
      </div>
    </aside>
    <main class="ml-64 p-8">
      <RouterView />
    </main>
  </div>
</template>

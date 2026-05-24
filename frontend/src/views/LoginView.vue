<template>
  <main class="grid min-h-screen place-items-center bg-slate-950 px-4 text-white">
    <section class="w-full max-w-md rounded-2xl bg-white p-8 text-slate-950 shadow-xl">
      <p class="text-sm font-semibold uppercase tracking-wide text-slate-500">Demo login</p>
      <h1 class="mt-2 text-2xl font-bold">Clinical RAG Assistant</h1>
      <p class="mt-2 text-sm text-slate-600">Portfolio SaaS for grounded clinical guideline Q&A.</p>
      <form class="mt-6 space-y-4">
        <input class="input" placeholder="clinician@example.com" />
        <input class="input" placeholder="Password" type="password" />
        <RouterLink class="btn block text-center" to="/chat">Continue to demo</RouterLink>
      </form>
    </section>
  </main>
</template>

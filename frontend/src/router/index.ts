import { createRouter, createWebHistory } from 'vue-router'
import AppLayout from '@/layouts/AppLayout.vue'
import ChatView from '@/views/ChatView.vue'
import HomeView from '@/views/HomeView.vue'
import DocumentsView from '@/views/DocumentsView.vue'

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      component: AppLayout,
      children: [
        { path: '', component: HomeView },
        { path: 'chat', component: ChatView },
        { path: 'documents', component: DocumentsView },
      ],
    },
    { path: '/:pathMatch(.*)*', redirect: '/' },
  ],
})

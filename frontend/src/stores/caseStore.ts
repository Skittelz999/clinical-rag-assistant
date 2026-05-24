import { defineStore } from 'pinia'

export const useCasesStore = defineStore('cases', {
  state: () => ({ ready: true }),
})

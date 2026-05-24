import { api } from './api'

export async function createCase(title: string, note: string) {
  const response = await api.post('/cases', { title, note })
  return response.data
}

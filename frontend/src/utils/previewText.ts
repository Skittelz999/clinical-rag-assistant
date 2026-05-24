export function cleanPreviewText(text: string, maxChars = 500): string {
  const normalized = text.replace(/\s+/g, ' ').trim()

  if (normalized.length <= maxChars) return normalized

  const sentenceBoundaries = ['. ', '! ', '? '].map((boundary) =>
    normalized.lastIndexOf(boundary, maxChars),
  )
  const sentenceBoundary = Math.max(...sentenceBoundaries)
  if (sentenceBoundary >= Math.max(80, Math.floor(maxChars * 0.45))) {
    return `${normalized.slice(0, sentenceBoundary + 1).trim()}...`
  }

  const wordBoundary = normalized.lastIndexOf(' ', maxChars)
  if (wordBoundary >= Math.max(40, Math.floor(maxChars * 0.45))) {
    return `${normalized.slice(0, wordBoundary).trim()}...`
  }

  return `${normalized.slice(0, maxChars).trim()}...`
}

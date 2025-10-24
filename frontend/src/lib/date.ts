const dayFormatter = new Intl.DateTimeFormat(undefined, {
  year: 'numeric',
  month: 'short',
  day: 'numeric',
})

export function formatDay(value?: string) {
  if (!value) return '—'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '—'
  return dayFormatter.format(date)
}

export function formatRelative(value?: string, now = new Date()) {
  if (!value) return 'No activity yet'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return 'No activity yet'
  const diffMs = now.getTime() - date.getTime()
  const diffDays = Math.round(diffMs / (1000 * 60 * 60 * 24))
  if (diffDays <= 0) return 'Today'
  if (diffDays === 1) return '1 day ago'
  if (diffDays < 7) return `${diffDays} days ago`
  const diffWeeks = Math.round(diffDays / 7)
  if (diffWeeks === 1) return '1 week ago'
  if (diffWeeks < 5) return `${diffWeeks} weeks ago`
  return formatDay(value)
}

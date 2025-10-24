import { formatRelative } from '../lib/date'
import type { CourseOverview } from '../types'
import ProgressBar from './ProgressBar'

type Props = {
  overview: CourseOverview
  onSelect: (courseId: string) => void
}

export default function CourseCard({ overview, onSelect }: Props) {
  const nextLabel = overview.nextLesson ? `${overview.nextLesson.title}` : 'Next lesson'
  return (
    <div className="flex flex-col rounded-2xl border bg-white p-4 shadow-sm transition hover:shadow-md">
      <div className="flex items-center justify-between gap-2">
        <h3 className="text-lg font-semibold leading-tight">{overview.name}</h3>
        <span className="rounded-full bg-indigo-50 px-2 py-1 text-xs font-medium text-indigo-700">
          Next: {nextLabel}
        </span>
      </div>
      <div className="mt-3">
        <ProgressBar value={overview.progress} />
        <div className="mt-1 text-xs text-gray-600">Progress: {overview.progress}%</div>
      </div>
      <div className="mt-3 flex flex-wrap gap-x-4 gap-y-1 text-xs text-gray-500">
        <span>Last activity: {formatRelative(overview.lastActivity)}</span>
        <span>Attempts: {overview.attempts.length}</span>
      </div>
      {overview.tags.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-1 text-xs">
          {overview.tags.map((tag) => (
            <span key={tag} className="rounded-full bg-slate-100 px-2 py-1 text-slate-600">
              #{tag}
            </span>
          ))}
        </div>
      )}
      <button
        className="mt-4 rounded-xl bg-indigo-600 px-3 py-2 text-sm font-medium text-white hover:bg-indigo-700"
        onClick={() => onSelect(overview.id)}
      >
        View details
      </button>
    </div>
  )
}

import { useMemo, useState } from 'react'
import { analyze, type Issue } from '../ai/codeChecks'
import { formatDay, formatRelative } from '../lib/date'
import type { CourseOverview, Lesson } from '../types'
import CodeAttemptViewer from './CodeAttemptViewer'

type Props = {
  course: CourseOverview
  lessons: Lesson[]
  onClose: () => void
  studentName: string
}

type LessonWithStatus = Lesson & {
  status: 'completed' | 'up-next' | 'pending'
}

const defaultSnippet = `function reviewArray(values) {
  const total = 0
  for (let i = 0; i <= values.length; i++) {
    console.log(values[i])
  }
  if (values.length > 0) {
    console.log('done')
  } else {
    console.log('done')
  }
}`

export default function CourseDetailPanel({ course, lessons, onClose, studentName }: Props) {
  const [code, setCode] = useState(defaultSnippet)
  const [issues, setIssues] = useState<Issue[]>([])
  const [hasAnalyzed, setHasAnalyzed] = useState(false)

  const lessonRows = useMemo(() => computeLessonRows(lessons, course), [lessons, course])

  const nextLesson = lessonRows.find((lesson) => lesson.status === 'up-next')

  const runAnalysis = () => {
    setHasAnalyzed(true)
    setIssues(analyze(code))
  }

  return (
    <aside className="fixed inset-0 z-20 flex items-start justify-center bg-black/30 p-4 sm:p-10">
      <div className="relative w-full max-w-3xl rounded-3xl border bg-white p-6 shadow-2xl">
        <button
          className="absolute right-4 top-4 rounded-full border border-gray-200 bg-white px-3 py-1 text-xs font-medium text-gray-600 hover:bg-gray-50"
          onClick={onClose}
        >
          Close
        </button>
        <h2 className="text-2xl font-semibold text-gray-900">{course.name}</h2>
        <p className="mt-1 text-sm text-gray-500">
          {studentName} • Progress {course.progress}% • Last activity {formatRelative(course.lastActivity)}
        </p>
        {nextLesson && (
          <p className="mt-2 rounded-xl bg-indigo-50 px-3 py-2 text-sm text-indigo-700">
            Up next: <span className="font-semibold">{nextLesson.title}</span>
            {nextLesson.estimatedMinutes && ` • ~${nextLesson.estimatedMinutes} min`}
          </p>
        )}
        <div className="mt-5 grid gap-4 md:grid-cols-[1.2fr_1fr]">
          <div className="rounded-2xl border bg-gray-50 p-4 shadow-sm">
            <h3 className="text-sm font-semibold text-gray-800">Lessons</h3>
            {lessonRows.length === 0 ? (
              <p className="mt-3 text-xs text-gray-500">No lessons configured yet.</p>
            ) : (
              <ul className="mt-3 space-y-2 text-sm">
                {lessonRows.map((lesson) => (
                  <li
                    key={lesson.id}
                    className="flex items-start justify-between gap-2 rounded-xl bg-white p-3 text-gray-700 shadow-sm"
                  >
                    <div>
                      <p className="font-medium">{lesson.title}</p>
                      {lesson.tags && lesson.tags.length > 0 && (
                        <p className="mt-1 text-xs text-gray-400">Tags: {lesson.tags.join(', ')}</p>
                      )}
                    </div>
                    <span className={statusBadgeClass(lesson.status)}>
                      {lesson.status === 'completed' && 'Completed'}
                      {lesson.status === 'up-next' && 'Up next'}
                      {lesson.status === 'pending' && 'Pending'}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </div>
          <div className="space-y-4">
            <div className="rounded-2xl border bg-white p-4 shadow-sm">
              <h3 className="text-sm font-semibold text-gray-800">Recent Attempts</h3>
              <ul className="mt-3 space-y-2 text-xs">
                {course.attempts.slice(0, 4).map((attempt) => (
                  <li key={attempt.timestamp} className="rounded-lg bg-gray-50 p-2">
                    <p className="font-medium text-gray-800">
                      {formatDay(attempt.timestamp)} • Correctness {(attempt.correctness * 100).toFixed(0)}%
                    </p>
                    <p className="text-[11px] text-gray-500">Hints used: {attempt.hintsUsed}</p>
                  </li>
                ))}
                {course.attempts.length === 0 && <li className="text-gray-500">No attempts yet.</li>}
              </ul>
            </div>
            <CodeAttemptViewer
              code={code}
              onChange={setCode}
              onAnalyze={runAnalysis}
              issues={issues}
              hasAnalyzed={hasAnalyzed}
            />
          </div>
        </div>
      </div>
    </aside>
  )
}

function computeLessonRows(lessons: Lesson[], course: CourseOverview): LessonWithStatus[] {
  const attemptedIds = new Set(course.attempts.map((attempt) => attempt.lessonId))
  const sortedLessons = lessons.slice().sort((a, b) => a.order - b.order)
  const next = course.nextLesson?.id

  return sortedLessons.map((lesson) => {
    if (attemptedIds.has(lesson.id)) {
      return { ...lesson, status: 'completed' as const }
    }
    if (lesson.id === next) {
      return { ...lesson, status: 'up-next' as const }
    }
    return { ...lesson, status: 'pending' as const }
  })
}

function statusBadgeClass(status: LessonWithStatus['status']) {
  if (status === 'completed') {
    return 'rounded-full bg-emerald-100 px-3 py-1 text-[11px] font-semibold text-emerald-700'
  }
  if (status === 'up-next') {
    return 'rounded-full bg-indigo-100 px-3 py-1 text-[11px] font-semibold text-indigo-700'
  }
  return 'rounded-full bg-gray-200 px-3 py-1 text-[11px] font-semibold text-gray-600'
}

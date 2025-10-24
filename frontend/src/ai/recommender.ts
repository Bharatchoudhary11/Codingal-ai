import type { Attempt, Course, Lesson, Student } from '../types'

type Input = {
  student: Student
  courses: Course[]
  lessons: Lesson[]
  attempts: Attempt[]
}

export type Recommendation = {
  id: string
  title: string
  reasonFeatures: Record<string, number | string>
  confidence: number
  alternatives: { id: string; title: string; reason: string }[]
  method: 'heuristic'
}

const MS_PER_DAY = 1000 * 60 * 60 * 24

function safeDate(value?: string) {
  return value ? new Date(value) : undefined
}

export function recommendNext(input: Input): Recommendation {
  const { student, courses, lessons, attempts } = input
  const now = safeDate(student.lastActive) ?? new Date()

  const summaries = courses.map((course) => {
    const courseAttempts = attempts.filter(
      (attempt) => attempt.courseId === course.id && attempt.studentId === student.id,
    )
    const courseLessons = lessons
      .filter((lesson) => lesson.courseId === course.id)
      .sort((a, b) => a.order - b.order)

    const lastAttempt = courseAttempts
      .slice()
      .sort((a, b) => (a.timestamp === b.timestamp ? 0 : a.timestamp > b.timestamp ? -1 : 1))[0]

    const lastActivity = safeDate(lastAttempt?.timestamp ?? course.lastActivity)
    const recencyGapDays = lastActivity ? Math.max(0, (now.getTime() - lastActivity.getTime()) / MS_PER_DAY) : 21
    const progress = course.progress ?? calculateProgress(courseLessons, courseAttempts)
    const progressGap = Math.max(0, 100 - progress)
    const weakTags = new Set(student.weakTags ?? [])
    const tagOverlapCount = course.tags?.filter((tag) => weakTags.has(tag)).length ?? 0
    const tagGapRatio =
      course.tags && course.tags.length > 0 ? tagOverlapCount / course.tags.length : weakTags.size > 0 ? 0.25 : 0
    const averageHints =
      courseAttempts.reduce((total, attempt) => total + attempt.hintsUsed, 0) /
      Math.max(1, courseAttempts.length)
    const lastCorrectness = lastAttempt ? lastAttempt.correctness : 0.7
    const momentumGap = Math.max(0, 1 - lastCorrectness)

    const normalized = {
      progress: progressGap / 100,
      recency: Math.min(recencyGapDays, 30) / 30,
      tag: Math.min(tagGapRatio, 1),
      hints: Math.min(averageHints / 3, 1),
      momentum: momentumGap,
    }

    const score =
      normalized.progress * 0.4 +
      normalized.recency * 0.25 +
      normalized.tag * 0.2 +
      normalized.hints * 0.1 +
      normalized.momentum * 0.05

    const nextLesson = findNextLesson(courseLessons, courseAttempts)

    return {
      course,
      score,
      nextLessonTitle: nextLesson?.title ?? 'Next lesson',
      features: {
        progress_gap: Number(progressGap.toFixed(1)),
        recency_gap_days: Number(recencyGapDays.toFixed(1)),
        weak_tag_overlap: tagOverlapCount,
        tag_gap_ratio: Number(tagGapRatio.toFixed(2)),
        average_hints: Number(averageHints.toFixed(2)),
        last_correctness: Number(lastCorrectness.toFixed(2)),
      },
    }
  })

  const ranked = summaries
    .slice()
    .sort((a, b) => (a.score === b.score ? a.course.name.localeCompare(b.course.name) : b.score - a.score))

  const top = ranked[0]
  const confidence = toConfidence(top?.score ?? 0)

  return {
    id: top?.course.id ?? 'unknown',
    title: `Continue "${top?.course.name ?? 'Course'}" — ${top?.nextLessonTitle ?? 'next lesson'}`,
    reasonFeatures: top?.features ?? {},
    confidence,
    alternatives: ranked.slice(1, 3).map((entry) => ({
      id: entry.course.id,
      title: `Revisit "${entry.course.name}" — ${entry.nextLessonTitle}`,
      reason: highlightFeature(entry.features),
    })),
    method: 'heuristic',
  }
}

function highlightFeature(features: Record<string, number | string>): string {
  const tuples = Object.entries(features)
    .filter(([, value]) => typeof value === 'number')
    .sort(([, a], [, b]) => (Number(b) ?? 0) - (Number(a) ?? 0))
  const [top] = tuples
  if (!top) return 'Close contender'
  const [key, value] = top
  return `${key.replace(/_/g, ' ')} = ${value}`
}

function toConfidence(score: number): number {
  const clamped = Math.max(0, Math.min(1, score))
  const logistic = 1 / (1 + Math.exp(-5 * (clamped - 0.5)))
  return Number(logistic.toFixed(2))
}

function calculateProgress(lessons: Lesson[], attempts: Attempt[]): number {
  if (!lessons.length) return 0
  const completed = new Set(attempts.map((attempt) => attempt.lessonId))
  return Math.round((completed.size / lessons.length) * 100)
}

function findNextLesson(lessons: Lesson[], attempts: Attempt[]) {
  if (!lessons.length) return undefined
  const completed = new Set(attempts.map((attempt) => attempt.lessonId))
  return lessons.find((lesson) => !completed.has(lesson.id)) ?? lessons[lessons.length - 1]
}

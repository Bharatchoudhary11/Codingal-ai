import { useEffect, useMemo, useState } from 'react'
import { formatExplanation } from '../ai/explain'
import { recommendNext, type Recommendation } from '../ai/recommender'
import CoachPanel from '../components/CoachPanel'
import CourseCard from '../components/CourseCard'
import CourseDetailPanel from '../components/CourseDetailPanel'
import type { Attempt, Course, CourseOverview, Lesson, Student } from '../types'

type FetchState = 'idle' | 'loading' | 'ready' | 'error'

export default function Dashboard() {
  const [fetchState, setFetchState] = useState<FetchState>('idle')
  const [student, setStudent] = useState<Student | null>(null)
  const [courses, setCourses] = useState<Course[]>([])
  const [lessons, setLessons] = useState<Lesson[]>([])
  const [attempts, setAttempts] = useState<Attempt[]>([])
  const [overview, setOverview] = useState<CourseOverview[]>([])
  const [recommendation, setRecommendation] = useState<Recommendation | null>(null)
  const [explanation, setExplanation] = useState('')
  const [selectedCourseId, setSelectedCourseId] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    setFetchState('loading')
    Promise.all([
      fetch('/data/students.json').then((response) => response.json()),
      fetch('/data/courses.json').then((response) => response.json()),
      fetch('/data/lessons.json').then((response) => response.json()),
      fetch('/data/attempts.json').then((response) => response.json()),
    ])
      .then(([studentData, courseData, lessonData, attemptData]) => {
        if (cancelled) return
        setStudent(studentData[0])
        setCourses(courseData)
        setLessons(lessonData)
        setAttempts(attemptData)
        setFetchState('ready')
      })
      .catch(() => setFetchState('error'))
    return () => {
      cancelled = true
    }
  }, [])

  useEffect(() => {
    if (!student || !courses.length || !lessons.length) return
    const summaries = courses.map((course) => buildCourseOverview(course, lessons, attempts, student))
    setOverview(summaries)
    const next = recommendNext({ student, courses, lessons, attempts })
    setRecommendation(next)
    setExplanation(formatExplanation(next))
    setSelectedCourseId((current) => current ?? next.id)
  }, [student, courses, lessons, attempts])

  const selectedCourse = useMemo(
    () => (selectedCourseId ? overview.find((item) => item.id === selectedCourseId) ?? null : null),
    [overview, selectedCourseId],
  )

  const selectedLessons = useMemo(
    () => (selectedCourse ? lessons.filter((lesson) => lesson.courseId === selectedCourse.id) : []),
    [selectedCourse, lessons],
  )

  if (fetchState === 'loading' || fetchState === 'idle') {
    return (
      <div className="space-y-6">
        <div className="h-32 animate-pulse rounded-3xl bg-gray-200" />
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 3 }).map((_, index) => (
            <div key={index} className="h-48 animate-pulse rounded-2xl bg-gray-200" />
          ))}
        </div>
      </div>
    )
  }

  if (fetchState === 'error' || !student) {
    return <p className="rounded-2xl bg-red-50 p-4 text-sm text-red-700">Failed to load dashboard data.</p>
  }

  return (
    <div className="space-y-6">
      <section className="rounded-3xl border bg-gradient-to-r from-indigo-500 via-purple-500 to-blue-500 p-6 text-white shadow-md">
        <h2 className="text-2xl font-semibold">Hi {student.name}, welcome back 👋</h2>
        <p className="mt-2 max-w-2xl text-sm text-indigo-100">
          Your AI Course Coach looks at progress gaps, stale lessons, and hint usage to keep your learning momentum on
          track. Start with the highlighted recommendation or pick a course below to dive in.
        </p>
      </section>

      <section>
        <div className="mb-3 flex items-center justify-between">
          <h3 className="text-xl font-semibold text-gray-900">My Courses</h3>
          <span className="text-xs uppercase tracking-wide text-gray-500">Deterministic overview</span>
        </div>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {overview.map((course) => (
            <CourseCard key={course.id} overview={course} onSelect={setSelectedCourseId} />
          ))}
        </div>
      </section>

      <CoachPanel recommendation={recommendation} explanation={explanation} />

      {selectedCourse && (
        <CourseDetailPanel
          course={selectedCourse}
          lessons={selectedLessons}
          onClose={() => setSelectedCourseId(null)}
          studentName={student.name}
        />
      )}
    </div>
  )
}

function buildCourseOverview(
  course: Course,
  lessons: Lesson[],
  attempts: Attempt[],
  student: Student,
): CourseOverview {
  const courseLessons = lessons.filter((lesson) => lesson.courseId === course.id).sort((a, b) => a.order - b.order)
  const courseAttempts = attempts
    .filter((attempt) => attempt.courseId === course.id && attempt.studentId === student.id)
    .sort((a, b) => (a.timestamp === b.timestamp ? 0 : a.timestamp > b.timestamp ? -1 : 1))

  const progress = calculateProgress(courseLessons, courseAttempts)
  const nextLesson = findNextLesson(courseLessons, courseAttempts)
  const lastActivity = courseAttempts[0]?.timestamp ?? course.lastActivity

  return {
    id: course.id,
    name: course.name,
    progress,
    lastActivity,
    nextLesson,
    attempts: courseAttempts,
    tags: course.tags ?? [],
    difficulty: course.difficulty,
  }
}

function calculateProgress(lessons: Lesson[], attempts: Attempt[]): number {
  if (!lessons.length) return 0
  const attemptedIds = new Set(attempts.map((attempt) => attempt.lessonId))
  const completion = attemptedIds.size / lessons.length
  return Math.max(0, Math.min(100, Math.round(completion * 100)))
}

function findNextLesson(lessons: Lesson[], attempts: Attempt[]) {
  if (!lessons.length) return undefined
  const attemptedIds = new Set(attempts.map((attempt) => attempt.lessonId))
  return lessons.find((lesson) => !attemptedIds.has(lesson.id)) ?? lessons[lessons.length - 1]
}

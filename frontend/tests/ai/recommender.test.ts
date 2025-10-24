import { describe, expect, it } from 'vitest'
import { recommendNext } from '../../src/ai/recommender'
import type { Attempt, Course, Lesson, Student } from '../../src/types'

const baseStudent: Student = {
  id: 's1',
  name: 'Ananya',
  weakTags: ['loops', 'conditions'],
  lastActive: '2025-10-10T00:00:00Z',
}

const baseCourses: Course[] = [
  { id: 'c1', name: 'Python Basics', progress: 60, tags: ['loops'], lastActivity: '2025-10-01T00:00:00Z' },
  { id: 'c2', name: 'JS Foundations', progress: 45, tags: ['conditions'], lastActivity: '2025-10-08T00:00:00Z' },
  { id: 'c3', name: 'AI Concepts', progress: 20, tags: ['logic'], lastActivity: '2025-09-25T00:00:00Z' },
]

const baseLessons: Lesson[] = [
  { id: 'c1-l1', courseId: 'c1', title: 'Variables', order: 1, tags: ['variables'] },
  { id: 'c1-l2', courseId: 'c1', title: 'Loops', order: 2, tags: ['loops'] },
  { id: 'c2-l1', courseId: 'c2', title: 'Arrays', order: 1, tags: ['arrays'] },
  { id: 'c2-l2', courseId: 'c2', title: 'Conditions', order: 2, tags: ['conditions'] },
  { id: 'c3-l1', courseId: 'c3', title: 'Logic', order: 1, tags: ['logic'] },
]

const baseAttempts: Attempt[] = [
  { studentId: 's1', courseId: 'c1', lessonId: 'c1-l1', timestamp: '2025-10-01T00:00:00Z', correctness: 0.6, hintsUsed: 1 },
  { studentId: 's1', courseId: 'c2', lessonId: 'c2-l1', timestamp: '2025-10-08T00:00:00Z', correctness: 0.9, hintsUsed: 0 },
]

function createBaseInput() {
  return {
    student: { ...baseStudent },
    courses: baseCourses.map((course) => ({ ...course })),
    lessons: baseLessons.map((lesson) => ({ ...lesson })),
    attempts: baseAttempts.map((attempt) => ({ ...attempt })),
  }
}

describe('recommendNext', () => {
  it('returns deterministic results for the same input', () => {
    const input = createBaseInput()
    const first = recommendNext(input)
    const second = recommendNext(input)
    expect(second).toEqual(first)
    expect(first.confidence).toBeGreaterThan(0)
    expect(first.confidence).toBeLessThanOrEqual(1)
  })

  it('prioritises the course with the largest progress gap', () => {
    const input = createBaseInput()
    const recommendation = recommendNext(input)
    expect(recommendation.id).toBe('c1') // 40% gap + high tag overlap
    expect(Number(recommendation.reasonFeatures.progress_gap)).toBeGreaterThan(0)
  })

  it('boosts stale courses when recency gap is high', () => {
    const input = createBaseInput()
    input.courses = input.courses.map((course) => {
      if (course.id === 'c1') {
        return { ...course, progress: 20, lastActivity: '2025-09-15T00:00:00Z' }
      }
      if (course.id === 'c3') {
        return { ...course, progress: 20, lastActivity: '2025-10-06T00:00:00Z' }
      }
      return { ...course, progress: 20, lastActivity: '2025-10-06T00:00:00Z' }
    })
    input.attempts = input.attempts.filter((attempt) => attempt.courseId !== 'c1')

    const recommendation = recommendNext(input)
    expect(recommendation.id).toBe('c1')
    expect(Number(recommendation.reasonFeatures.recency_gap_days)).toBeGreaterThan(20)
  })

  it('factors hint usage when other features are similar', () => {
    const input = createBaseInput()
    input.courses = input.courses
      .filter((course) => course.id !== 'c3')
      .map((course) => ({ ...course, progress: 40, lastActivity: '2025-10-05T00:00:00Z' }))
    input.lessons = input.lessons.filter((lesson) => lesson.courseId !== 'c3')
    input.attempts = [
      { studentId: 's1', courseId: 'c1', lessonId: 'c1-l2', timestamp: '2025-10-05T09:00:00Z', correctness: 0.7, hintsUsed: 3 },
      { studentId: 's1', courseId: 'c2', lessonId: 'c2-l2', timestamp: '2025-10-05T09:00:00Z', correctness: 0.7, hintsUsed: 0 },
    ]

    const recommendation = recommendNext(input)
    expect(recommendation.id).toBe('c1')
    expect(Number(recommendation.reasonFeatures.average_hints)).toBeGreaterThan(0)
  })

  it('returns ranked alternatives drawn from remaining courses', () => {
    const input = createBaseInput()
    const recommendation = recommendNext(input)
    const alternativeIds = recommendation.alternatives.map((alt) => alt.id)
    expect(new Set(alternativeIds)).toEqual(new Set(['c2', 'c3']))
    expect(alternativeIds).not.toContain(recommendation.id)
    expect(recommendation.alternatives.every((alt) => alt.reason.length > 0)).toBe(true)
  })
})

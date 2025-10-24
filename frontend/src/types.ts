export type Student = {
  id: string
  name: string
  weakTags?: string[]
  lastActive?: string
}

export type Course = {
  id: string
  name: string
  description?: string
  difficulty?: number
  progress?: number
  tags?: string[]
  lastActivity?: string
}

export type Lesson = {
  id: string
  courseId: string
  title: string
  order: number
  tags?: string[]
  estimatedMinutes?: number
}

export type Attempt = {
  studentId: string
  courseId: string
  lessonId: string
  timestamp: string
  correctness: number
  hintsUsed: number
}

export type CourseOverview = {
  id: string
  name: string
  progress: number
  lastActivity?: string
  nextLesson?: Lesson
  attempts: Attempt[]
  tags: string[]
  difficulty?: number
}


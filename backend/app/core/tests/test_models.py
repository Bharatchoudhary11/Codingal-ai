from __future__ import annotations

import pytest
from django.db import IntegrityError
from django.utils import timezone

from core.models import Attempt, Course, Lesson, Student


@pytest.mark.django_db
def test_lesson_ordering_and_uniqueness():
    course = Course.objects.create(name="Course", description="", difficulty=1)
    lesson_one = Lesson.objects.create(course=course, title="One", order_index=1)
    Lesson.objects.create(course=course, title="Two", order_index=2)
    with pytest.raises(IntegrityError):
        Lesson.objects.create(course=course, title="Duplicate", order_index=1)
    ordered_titles = list(course.lessons.values_list("title", flat=True))
    assert ordered_titles == ["One", "Two"]
    assert str(lesson_one) == "Course: One"


@pytest.mark.django_db
def test_attempt_string_representation_and_ordering():
    student = Student.objects.create(name="Student", email="s@example.com")
    course = Course.objects.create(name="Course", description="", difficulty=1)
    lesson = Lesson.objects.create(course=course, title="Lesson", order_index=1)
    older = Attempt.objects.create(
        student=student,
        lesson=lesson,
        timestamp=timezone.now() - timezone.timedelta(days=1),
        correctness=0.5,
        hints_used=0,
        duration_sec=300,
    )
    newer = Attempt.objects.create(
        student=student,
        lesson=lesson,
        timestamp=timezone.now(),
        correctness=0.8,
        hints_used=1,
        duration_sec=400,
    )
    attempts = list(Attempt.objects.all())
    assert attempts == [newer, older]
    assert str(newer).startswith(f"{student.id}:{lesson.id}@")

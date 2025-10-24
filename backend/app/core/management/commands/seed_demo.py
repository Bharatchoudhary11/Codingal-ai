from __future__ import annotations

from django.core.management.base import BaseCommand
from django.utils import timezone

from core.models import Attempt, Course, Lesson, Student


class Command(BaseCommand):
    help = "Create demo data"

    def handle(self, *args, **options):
        student, _ = Student.objects.get_or_create(
            email="ananya@example.com",
            defaults={"name": "Ananya", "weak_tags": ["loops", "conditions"]},
        )

        courses = [
            (
                "Python Basics",
                "Intro to Python",
                1,
                [
                    ("Variables", ["variables"]),
                    ("Loops", ["loops"]),
                    ("Functions", ["functions"]),
                ],
                ["loops", "variables"],
            ),
            (
                "JavaScript Foundations",
                "JS core",
                2,
                [
                    ("Arrays", ["arrays"]),
                    ("Conditions", ["conditions"]),
                ],
                ["conditions", "dom"],
            ),
            (
                "Intro to AI Concepts",
                "Logic & data",
                2,
                [("What is AI?", ["logic", "data"])],
                ["logic", "data"],
            ),
        ]

        created_courses = []
        for name, description, difficulty, lessons, tags in courses:
            course, _ = Course.objects.get_or_create(
                name=name,
                defaults={"description": description, "difficulty": difficulty, "tags": tags},
            )
            for index, (title, lesson_tags) in enumerate(lessons, start=1):
                Lesson.objects.get_or_create(
                    course=course,
                    order_index=index,
                    defaults={"title": title, "tags": lesson_tags},
                )
            created_courses.append(course)

        now = timezone.now()
        for course in created_courses:
            first_lesson = course.lessons.order_by("order_index").first()
            if first_lesson is None:
                continue
            Attempt.objects.get_or_create(
                student=student,
                lesson=first_lesson,
                defaults={
                    "timestamp": now - timezone.timedelta(days=3),
                    "correctness": 0.6,
                    "hints_used": 1,
                    "duration_sec": 600,
                    "code_snapshot": "print('hello world')",
                },
            )

        self.stdout.write(self.style.SUCCESS("Seeded demo data."))


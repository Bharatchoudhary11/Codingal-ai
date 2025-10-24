from __future__ import annotations

import pytest
from django.urls import reverse
from django.utils import timezone

from core.models import Attempt, Course, Lesson, Student


@pytest.fixture
@pytest.mark.django_db
def sample_data():
    student = Student.objects.create(
        name="Ananya",
        email="ananya@example.com",
        weak_tags=["loops", "conditions"],
    )
    python = Course.objects.create(
        name="Python Basics",
        description="Intro to Python",
        difficulty=1,
        tags=["loops", "variables"],
    )
    js = Course.objects.create(
        name="JavaScript",
        description="Fundamentals",
        difficulty=2,
        tags=["conditions", "dom"],
    )
    for idx, title in enumerate(["Variables", "Loops", "Functions"], start=1):
        Lesson.objects.create(course=python, title=title, tags=[title.lower()], order_index=idx)
    for idx, title in enumerate(["Syntax", "Conditions"], start=1):
        Lesson.objects.create(course=js, title=title, tags=[title.lower()], order_index=idx)
    first_python_lesson = python.lessons.order_by("order_index").first()
    Attempt.objects.create(
        student=student,
        lesson=first_python_lesson,
        timestamp=timezone.now() - timezone.timedelta(days=3),
        correctness=0.7,
        hints_used=1,
        duration_sec=600,
    )
    return student, python, js


@pytest.mark.django_db
def test_student_overview_returns_progress(client, sample_data):
    student, python, _ = sample_data
    url = reverse("student-overview", args=[student.pk])
    response = client.get(url)
    assert response.status_code == 200
    payload = response.json()
    assert payload["student"]["email"] == student.email
    python_course = next(course for course in payload["courses"] if course["id"] == python.id)
    assert python_course["lessons_total"] == 3
    assert python_course["lessons_completed"] == 1
    assert python_course["progress"] == pytest.approx(33.33, rel=1e-2)
    assert python_course["next_up"] == "Loops"
    assert python_course["last_activity"] is not None


@pytest.mark.django_db
def test_student_recommendation_includes_confidence_and_explanation(client, sample_data):
    student, python, js = sample_data
    # Add one more attempt to provide hint activity for deterministic scoring.
    second_lesson = python.lessons.order_by("order_index")[1]
    Attempt.objects.create(
        student=student,
        lesson=second_lesson,
        timestamp=timezone.now() - timezone.timedelta(days=10),
        correctness=0.5,
        hints_used=2,
        duration_sec=900,
    )

    url = reverse("student-recommendation", args=[student.pk])
    response = client.get(url)
    assert response.status_code == 200
    payload = response.json()
    assert "recommendation" in payload
    assert payload["confidence"] <= 1.0
    assert payload["confidence"] >= 0.0
    assert payload["explanation"]
    feature_keys = set(payload["reason_features"].keys())
    # Ensure our deterministic features are surfaced.
    assert {"progress_gap", "recency_gap", "tag_alignment", "support_need"}.issubset(feature_keys)
    assert len(payload["alternatives"]) <= 2
    # Highest score should belong to a course we created.
    assert payload["recommendation"]["course_id"] in {python.id, js.id}


@pytest.mark.django_db
def test_create_attempt_validates_and_persists_attempt(client, sample_data):
    student, python, _ = sample_data
    lesson = python.lessons.order_by("order_index").last()
    payload = {
        "student": student.id,
        "lesson": lesson.id,
        "timestamp": (timezone.now() - timezone.timedelta(minutes=1)).isoformat().replace("+00:00", "Z"),
        "correctness": 0.9,
        "hints_used": 3,
        "duration_sec": 1200,
        "code_snapshot": "print('hello')",
    }
    response = client.post(reverse("attempt-create"), data=payload, format="json")
    assert response.status_code == 201
    attempt = Attempt.objects.get(pk=response.json()["id"])
    assert attempt.student == student
    assert attempt.lesson == lesson


@pytest.mark.django_db
def test_create_attempt_rejects_bad_payload(client, sample_data):
    student, python, _ = sample_data
    lesson = python.lessons.first()
    payload = {
        "student": student.id,
        "lesson": lesson.id,
        "timestamp": (timezone.now() + timezone.timedelta(days=2)).isoformat(),
        "correctness": 1.1,
        "hints_used": 100,
        "duration_sec": 0,
    }
    response = client.post(reverse("attempt-create"), data=payload, format="json")
    assert response.status_code == 400
    errors = response.json()
    assert "timestamp" in errors or "correctness" in errors
    assert "duration_sec" in errors


@pytest.mark.django_db
def test_analyze_code_reports_static_issues(client):
    code = """
try:\n    print('hello')\nexcept:\n    pass\n\n
def greet(name, unused):\n    print(name)
"""
    response = client.post(reverse("analyze-code"), data={"code": code}, format="json")
    assert response.status_code == 200
    payload = response.json()
    rules = {issue["rule"] for issue in payload["issues"]}
    assert {"bare-except", "print-call", "unused-argument"}.issubset(rules)


@pytest.mark.django_db
def test_analyze_code_rejects_empty_payload(client):
    response = client.post(reverse("analyze-code"), data={"code": ""}, format="json")
    assert response.status_code == 400
    assert "code" in response.json()


@pytest.mark.django_db
def test_analyze_code_reports_syntax_error(client):
    response = client.post(reverse("analyze-code"), data={"code": "def foo(:\n    pass"}, format="json")
    assert response.status_code == 200
    issues = response.json()["issues"]
    assert any(issue["rule"] == "syntax-error" for issue in issues)

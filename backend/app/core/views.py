from __future__ import annotations

import ast
from collections import defaultdict
from typing import Dict, Iterable, List, Optional

from django.db.models import Prefetch
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, throttle_classes
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle

from .models import Attempt, Course, Lesson, Student
from .serializers import AttemptCreateSerializer, CodeAnalysisSerializer
from .services.recommender import RecommendationResult, score_candidate


class WriteThrottle(UserRateThrottle):
    rate = "30/min"


@api_view(["GET"])
def service_root(request):
    return Response(
        {
            "service": "Codingal AI Course Coach API",
            "status": "ok",
            "endpoints": {
                "overview": "/api/students/<id>/overview/",
                "recommendation": "/api/students/<id>/recommendation/",
                "attempts": {
                    "GET": "/api/attempts/",
                    "POST": "/api/attempts/",
                },
                "analyze_code": "/api/analyze-code/",
            },
        }
    )

def _get_student(pk: int) -> Optional[Student]:
    return (
        Student.objects.prefetch_related(
            Prefetch(
                "attempts",
                queryset=Attempt.objects.select_related("lesson__course").order_by("-timestamp"),
            )
        )
        .filter(pk=pk)
        .first()
    )


def _course_queryset() -> Iterable[Course]:
    return Course.objects.prefetch_related(
        Prefetch("lessons", queryset=Lesson.objects.order_by("order_index"))
    ).order_by("name")


def _group_attempts_by_course(student: Student) -> Dict[int, List[Attempt]]:
    grouped: Dict[int, List[Attempt]] = defaultdict(list)
    for attempt in student.attempts.all():
        grouped[attempt.lesson.course_id].append(attempt)
    return grouped


@api_view(["GET"])
def student_overview(request, pk: int):
    student = _get_student(pk)
    if student is None:
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

    attempts_by_course = _group_attempts_by_course(student)
    overview = []
    for course in _course_queryset():
        lessons = list(course.lessons.all())
        total_lessons = len(lessons)
        course_attempts = attempts_by_course.get(course.id, [])
        completed_lesson_ids = {attempt.lesson_id for attempt in course_attempts}
        completed_count = len(completed_lesson_ids)
        progress_percent = (completed_count / total_lessons * 100.0) if total_lessons else 0.0
        latest_attempt = max(course_attempts, key=lambda attempt: attempt.timestamp, default=None)
        next_lesson_title = None
        for lesson in lessons:
            if lesson.id not in completed_lesson_ids:
                next_lesson_title = lesson.title
                break
        overview.append(
            {
                "id": course.id,
                "name": course.name,
                "description": course.description,
                "difficulty": course.difficulty,
                "progress": round(progress_percent, 2),
                "lessons_total": total_lessons,
                "lessons_completed": completed_count,
                "last_activity": timezone.localtime(latest_attempt.timestamp).isoformat()
                if latest_attempt
                else None,
                "next_up": next_lesson_title,
            }
        )

    payload = {
        "student": {"id": student.id, "name": student.name, "email": student.email},
        "courses": overview,
    }
    return Response(payload)


def _compute_tag_alignment(course: Course, student: Student) -> float:
    student_focus = set(student.weak_tags or [])
    course_tags = set(course.tags or [])
    if not course_tags or not student_focus:
        return 0.0
    return len(course_tags & student_focus) / len(student_focus)


def _serialize_features(result: RecommendationResult) -> Dict[str, Dict[str, float]]:
    serialized: Dict[str, Dict[str, float]] = {}
    for feature in result.features:
        serialized[feature.key] = {
            "value": feature.raw_value,
            "normalized": round(feature.normalized_value, 3),
            "weight": feature.weight,
            "contribution": round(feature.contribution, 3),
            "description": feature.description,
        }
    return serialized


@api_view(["GET"])
def student_recommendation(request, pk: int):
    student = _get_student(pk)
    if student is None:
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

    attempts_by_course = _group_attempts_by_course(student)
    now = timezone.now()
    candidates = []
    for course in _course_queryset():
        lessons = list(course.lessons.all())
        total_lessons = len(lessons)
        course_attempts = attempts_by_course.get(course.id, [])
        completed_lesson_ids = {attempt.lesson_id for attempt in course_attempts}
        progress_percent = (
            len(completed_lesson_ids) / total_lessons * 100.0 if total_lessons else 0.0
        )
        latest_attempt = max(course_attempts, key=lambda attempt: attempt.timestamp, default=None)
        if latest_attempt is None:
            recency_gap_days = float("inf")
        else:
            recency_gap_days = (now - latest_attempt.timestamp).total_seconds() / 86400.0
        hint_rate = (
            sum(attempt.hints_used for attempt in course_attempts) / len(course_attempts)
            if course_attempts
            else 0.0
        )
        tag_alignment = _compute_tag_alignment(course, student)
        recommendation = score_candidate(progress_percent, recency_gap_days, tag_alignment, hint_rate)
        candidates.append(
            {
                "course": course,
                "result": recommendation,
            }
        )

    if not candidates:
        return Response(
            {
                "recommendation": None,
                "confidence": 0.0,
                "explanation": "No courses available to recommend.",
                "reason_features": {},
                "alternatives": [],
            }
        )

    candidates.sort(key=lambda item: item["result"].score, reverse=True)
    top = candidates[0]
    alternatives = [
        {
            "course_id": candidate["course"].id,
            "title": f'Continue "{candidate["course"].name}"',
            "score": round(candidate["result"].score, 4),
        }
        for candidate in candidates[1:3]
    ]

    payload = {
        "recommendation": {
            "course_id": top["course"].id,
            "title": f'Continue "{top["course"].name}"',
            "score": round(top["result"].score, 4),
        },
        "confidence": round(top["result"].confidence, 4),
        "explanation": top["result"].explanation,
        "reason_features": _serialize_features(top["result"]),
        "alternatives": alternatives,
    }
    return Response(payload)


@api_view(["GET", "POST"])
@throttle_classes([WriteThrottle])
def attempt_collection(request):
    if request.method == "GET":
        attempts = (
            Attempt.objects.select_related("student", "lesson", "lesson__course")
            .order_by("-timestamp")[:25]
        )
        results = [
            {
                "id": attempt.id,
                "student": {"id": attempt.student_id, "name": attempt.student.name},
                "lesson": {
                    "id": attempt.lesson_id,
                    "title": attempt.lesson.title,
                    "course": attempt.lesson.course.name,
                },
                "timestamp": timezone.localtime(attempt.timestamp).isoformat(),
                "correctness": attempt.correctness,
                "hints_used": attempt.hints_used,
                "duration_sec": attempt.duration_sec,
            }
            for attempt in attempts
        ]
        return Response({"count": len(results), "results": results})

    serializer = AttemptCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    attempt = serializer.save()
    return Response({"id": attempt.id}, status=status.HTTP_201_CREATED)


def _issue(rule: str, message: str, severity: str, node: ast.AST) -> Dict[str, object]:
    return {
        "rule": rule,
        "message": message,
        "severity": severity,
        "line": getattr(node, "lineno", None),
        "column": getattr(node, "col_offset", None),
    }


@api_view(["POST"])
def analyze_code(request):
    serializer = CodeAnalysisSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    code = serializer.validated_data["code"]

    issues: List[Dict[str, object]] = []
    try:
        tree = ast.parse(code)
    except SyntaxError as exc:  # pragma: no cover - handled in tests via severity output
        issues.append(
            {
                "rule": "syntax-error",
                "message": exc.msg,
                "severity": "error",
                "line": exc.lineno,
                "column": exc.offset,
            }
        )
        return Response({"issues": issues})

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            arg_names = {arg.arg for arg in node.args.args}
            used_args = {
                child.id
                for child in ast.walk(node)
                if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Load)
            }
            for unused in sorted(arg_names - used_args):
                issues.append(
                    _issue(
                        "unused-argument",
                        f'Argument "{unused}" in function "{node.name}" is not used.',
                        "info",
                        node,
                    )
                )
        elif isinstance(node, ast.ExceptHandler) and node.type is None:
            issues.append(
                _issue("bare-except", "Avoid bare except; catch specific exceptions.", "warning", node)
            )
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id == "print":
                issues.append(
                    _issue("print-call", "Avoid print statements; use logging instead.", "info", node)
                )

    return Response({"issues": issues})

from __future__ import annotations

import ast
from collections import defaultdict
import math
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

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
        raw_value = feature.raw_value
        if isinstance(raw_value, float) and not math.isfinite(raw_value):
            serialized_value = None
        else:
            serialized_value = raw_value
        serialized[feature.key] = {
            "value": serialized_value,
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


@dataclass
class _Scope:
    label: str
    assigned: Dict[str, ast.AST] = field(default_factory=dict)
    used: Dict[str, bool] = field(default_factory=dict)


class _StaticAnalyzer(ast.NodeVisitor):
    """Lightweight deterministic Python AST checker."""

    def __init__(self) -> None:
        self.issues: List[Dict[str, object]] = []
        self._scopes: List[_Scope] = [_Scope(label="module")]
        self._block_signatures: Dict[Tuple[str, ...], Tuple[int, int]] = {}

    # ------------------------------------------------------------------
    # Scope helpers
    # ------------------------------------------------------------------
    @property
    def current_scope(self) -> _Scope:
        return self._scopes[-1]

    def _enter_scope(self, label: str) -> None:
        self._scopes.append(_Scope(label=label))

    def _leave_scope(self) -> None:
        scope = self._scopes.pop()
        for name, node in scope.assigned.items():
            if scope.used.get(name):
                continue
            self.issues.append(
                _issue(
                    "unused-variable",
                    f'Variable "{name}" is assigned but never used in {scope.label}.',
                    "info",
                    node,
                )
            )

    def _record_assignment(self, target: ast.AST) -> None:
        if isinstance(target, ast.Name):
            name = target.id
            if name.startswith("_"):
                return
            self.current_scope.assigned.setdefault(name, target)
        elif isinstance(target, (ast.Tuple, ast.List)):
            for element in target.elts:
                self._record_assignment(element)

    def _mark_used(self, name: str) -> None:
        for scope in reversed(self._scopes):
            if name in scope.assigned:
                scope.used[name] = True
                break

    # ------------------------------------------------------------------
    # Block helpers
    # ------------------------------------------------------------------
    def _record_block(self, statements: Sequence[ast.stmt]) -> None:
        if not statements:
            return
        signature = tuple(ast.dump(stmt, include_attributes=False) for stmt in statements)
        if not signature:
            return
        first = statements[0]
        location = (
            getattr(first, "lineno", None),
            getattr(first, "col_offset", None),
        )
        if signature not in self._block_signatures:
            if location[0] is not None:
                self._block_signatures[signature] = location
            return

        if location[0] is None:
            return
        dummy = statements[0]
        self.issues.append(
            _issue(
                "duplicate-block",
                "Duplicate block detected. Extract shared statements to avoid repetition.",
                "info",
                dummy,
            )
        )

    # ------------------------------------------------------------------
    # Visitor overrides
    # ------------------------------------------------------------------
    def visit_Module(self, node: ast.Module) -> None:  # pragma: no cover - exercised indirectly
        self._record_block(node.body)
        self.generic_visit(node)
        self._leave_scope()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._record_block(node.body)
        self._enter_scope(f"function {node.name}")
        for arg in (*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs):
            if arg.arg and not arg.arg.startswith("_"):
                self.current_scope.used[arg.arg] = True
        if node.args.vararg:
            self.current_scope.used[node.args.vararg.arg] = True
        if node.args.kwarg:
            self.current_scope.used[node.args.kwarg.arg] = True
        self.generic_visit(node)
        has_return_value = any(
            isinstance(child, ast.Return) and child.value is not None for child in ast.walk(node)
        )
        has_yield = any(isinstance(child, (ast.Yield, ast.YieldFrom)) for child in ast.walk(node))
        if not has_return_value and not has_yield and node.body:
            self.issues.append(
                _issue(
                    "missing-return",
                    f'Function "{node.name}" does not return a value on any path.',
                    "warning",
                    node,
                )
            )
        self._leave_scope()

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self.visit_FunctionDef(node)  # type: ignore[arg-type]

    def visit_For(self, node: ast.For) -> None:
        self._record_block(node.body)
        self._record_block(node.orelse)
        self._record_assignment(node.target)
        self._check_for_loop(node)
        self.generic_visit(node)

    def visit_AsyncFor(self, node: ast.AsyncFor) -> None:
        self.visit_For(node)  # type: ignore[arg-type]

    def visit_With(self, node: ast.With) -> None:
        self._record_block(node.body)
        for item in node.items:
            if item.optional_vars:
                self._record_assignment(item.optional_vars)
        self.generic_visit(node)

    def visit_If(self, node: ast.If) -> None:
        self._record_block(node.body)
        self._record_block(node.orelse)
        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign) -> None:
        for target in node.targets:
            self._record_assignment(target)
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        if node.target:
            self._record_assignment(node.target)
        self.generic_visit(node)

    def visit_AugAssign(self, node: ast.AugAssign) -> None:
        self._record_assignment(node.target)
        if isinstance(node.target, ast.Name):
            self._mark_used(node.target.id)
        self.generic_visit(node)

    def visit_Name(self, node: ast.Name) -> None:
        if isinstance(node.ctx, ast.Load):
            self._mark_used(node.id)
        self.generic_visit(node)

    def visit_Try(self, node: ast.Try) -> None:
        self._record_block(node.body)
        self._record_block(node.orelse)
        self._record_block(node.finalbody)
        for handler in node.handlers:
            self._record_block(handler.body)
        self.generic_visit(node)

    # ------------------------------------------------------------------
    # Rule implementations
    # ------------------------------------------------------------------
    def _check_for_loop(self, node: ast.For) -> None:
        iterator = node.iter
        if not (
            isinstance(iterator, ast.Call)
            and isinstance(iterator.func, ast.Name)
            and iterator.func.id == "range"
            and iterator.args
        ):
            return

        last_arg = iterator.args[-1]
        if isinstance(last_arg, ast.BinOp) and isinstance(last_arg.op, ast.Add):
            if self._is_len_call(last_arg.left) and self._is_one(last_arg.right):
                self.issues.append(
                    _issue(
                        "for-loop-off-by-one",
                        "Potential off-by-one: range(len(items) + 1) iterates one past the end.",
                        "warning",
                        iterator,
                    )
                )
            elif self._is_len_call(last_arg.right) and self._is_one(last_arg.left):
                self.issues.append(
                    _issue(
                        "for-loop-off-by-one",
                        "Potential off-by-one: range(len(items) + 1) iterates one past the end.",
                        "warning",
                        iterator,
                    )
                )

    @staticmethod
    def _is_len_call(node: ast.AST) -> bool:
        return (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "len"
            and len(node.args) == 1
        )

    @staticmethod
    def _is_one(node: ast.AST) -> bool:
        return isinstance(node, ast.Constant) and node.value == 1


def _analyze_python_code(code: str) -> List[Dict[str, object]]:
    tree = ast.parse(code)
    analyzer = _StaticAnalyzer()
    analyzer.visit(tree)
    return analyzer.issues


@api_view(["POST"])
def analyze_code(request):
    serializer = CodeAnalysisSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    code = serializer.validated_data["code"]

    try:
        issues = _analyze_python_code(code)
    except SyntaxError as exc:  # pragma: no cover - surfaced in API tests
        return Response(
            {
                "issues": [
                    {
                        "rule": "syntax-error",
                        "message": exc.msg,
                        "severity": "error",
                        "line": exc.lineno,
                        "column": exc.offset,
                    }
                ]
            }
        )

    return Response({"issues": issues})

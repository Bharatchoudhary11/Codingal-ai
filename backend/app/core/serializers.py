from __future__ import annotations

from datetime import timedelta

from django.utils import timezone
from rest_framework import serializers

from .models import Attempt, Course, Lesson


class LessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = ["id", "title", "tags", "order_index", "estimated_minutes"]
        read_only_fields = ["order_index"]


class CourseSerializer(serializers.ModelSerializer):
    lessons = LessonSerializer(many=True, read_only=True)

    class Meta:
        model = Course
        fields = ["id", "name", "description", "difficulty", "tags", "last_activity", "lessons"]


class AttemptCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attempt
        fields = [
            "id",
            "student",
            "lesson",
            "timestamp",
            "correctness",
            "hints_used",
            "duration_sec",
            "code_snapshot",
        ]

    def validate_correctness(self, value: float) -> float:
        if not (0.0 <= value <= 1.0):
            raise serializers.ValidationError("Correctness must be between 0 and 1.")
        return value

    def validate_timestamp(self, value):
        if value is None:
            raise serializers.ValidationError("Timestamp is required.")
        now = timezone.now() + timedelta(minutes=5)
        if value > now:
            raise serializers.ValidationError("Timestamp cannot be in the future.")
        return value

    def validate_duration_sec(self, value: int) -> int:
        if value <= 0:
            raise serializers.ValidationError("Duration must be greater than zero seconds.")
        if value > 8 * 60 * 60:
            raise serializers.ValidationError("Duration longer than 8 hours is not allowed.")
        return value

    def validate_hints_used(self, value: int) -> int:
        if value > 50:
            raise serializers.ValidationError("Hints used seems unrealistic; please review the payload.")
        return value


class CodeAnalysisSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=20_000, allow_blank=False)

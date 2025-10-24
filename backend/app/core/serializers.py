from rest_framework import serializers
from .models import Attempt, Course, Lesson, Student


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

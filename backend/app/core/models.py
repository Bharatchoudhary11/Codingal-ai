from django.db import models


class Student(models.Model):
    name = models.CharField(max_length=200)
    email = models.EmailField(unique=True)
    weak_tags = models.JSONField(default=list, blank=True)
    last_active = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Course(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    difficulty = models.PositiveSmallIntegerField(default=1)
    tags = models.JSONField(default=list, blank=True)
    last_activity = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Lesson(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="lessons")
    title = models.CharField(max_length=200)
    tags = models.JSONField(default=list, blank=True)
    order_index = models.PositiveIntegerField(default=0)
    estimated_minutes = models.PositiveSmallIntegerField(default=20)

    class Meta:
        ordering = ["order_index"]
        unique_together = ("course", "order_index")

    def __str__(self) -> str:
        return f"{self.course.name}: {self.title}"


class Attempt(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="attempts")
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="attempts")
    timestamp = models.DateTimeField()
    correctness = models.FloatField()
    hints_used = models.PositiveIntegerField(default=0)
    duration_sec = models.PositiveIntegerField(default=0)
    code_snapshot = models.TextField(blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["student", "timestamp"]),
            models.Index(fields=["lesson", "timestamp"]),
        ]
        ordering = ["-timestamp"]

    def __str__(self) -> str:
        return f"{self.student_id}:{self.lesson_id}@{self.timestamp.isoformat()}"

from django.urls import path

from . import views


urlpatterns = [
    path("students/<int:pk>/overview/", views.student_overview, name="student-overview"),
    path(
        "students/<int:pk>/recommendation/",
        views.student_recommendation,
        name="student-recommendation",
    ),
    path("attempts/", views.create_attempt, name="attempt-create"),
    path("analyze-code/", views.analyze_code, name="analyze-code"),
]

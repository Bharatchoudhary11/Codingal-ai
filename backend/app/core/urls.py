from django.urls import path

from . import views


urlpatterns = [
    path("students/<int:pk>/overview/", views.student_overview, name="student-overview"),
    path(
        "students/<int:pk>/recommendation/",
        views.student_recommendation,
        name="student-recommendation",
    ),
    path("attempts/", views.attempt_collection, name="attempt-collection"),
    path("analyze-code/", views.analyze_code, name="analyze-code"),
]

from django.urls import path
from . import views
urlpatterns=[path('students/<int:pk>/overview/',views.student_overview),path('students/<int:pk>/recommendation/',views.student_recommendation),path('attempts/',views.create_attempt),path('analyze-code/',views.analyze_code)]

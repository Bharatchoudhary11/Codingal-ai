import pytest
from core.models import Student, Course, Lesson
@pytest.mark.django_db
def test_overview(client):
    s=Student.objects.create(name='A', email='a@example.com')
    Course.objects.create(name='C', description='', difficulty=1)
    r=client.get(f'/api/students/{s.id}/overview/'); assert r.status_code==200; assert 'student' in r.json()
@pytest.mark.django_db
def test_recommendation(client):
    s=Student.objects.create(name='A', email='a2@example.com')
    c=Course.objects.create(name='C', description='', difficulty=1)
    Lesson.objects.create(course=c, title='L1', tags=['t'], order_index=1)
    r=client.get(f'/api/students/{s.id}/recommendation/'); assert r.status_code==200; j=r.json(); assert 'recommendation' in j and 'confidence' in j
@pytest.mark.django_db
def test_analyze_code(client):
    r=client.post('/api/analyze-code/', data={'code':'def f(x): print(x)\ntry:\n  pass\nexcept:\n  pass'})
    assert r.status_code==200; assert 'issues' in r.json()

from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models import Student, Course, Lesson, Attempt

class Command(BaseCommand):
    help='Create demo data'
    def handle(self, *args, **kwargs):
        s,_=Student.objects.get_or_create(email='ananya@example.com', defaults={'name':'Ananya'})
        c1,_=Course.objects.get_or_create(name='Python Basics', defaults={'description':'Intro to Python','difficulty':1})
        c2,_=Course.objects.get_or_create(name='JavaScript Foundations', defaults={'description':'JS core','difficulty':2})
        c3,_=Course.objects.get_or_create(name='Intro to AI Concepts', defaults={'description':'Logic & data','difficulty':2})
        def mk(course, idx, title, tags): Lesson.objects.get_or_create(course=course, order_index=idx, defaults={'title':title,'tags':tags})
        mk(c1,1,'Variables',['variables']); mk(c1,2,'Loops',['loops'])
        mk(c2,1,'Arrays',['arrays']); mk(c2,2,'Conditions',['conditions'])
        mk(c3,1,'What is AI?',['logic','data'])
        l=Lesson.objects.filter(course=c1).first()
        if l: Attempt.objects.get_or_create(student=s, lesson=l, timestamp=timezone.now(), correctness=0.6, hints_used=1, duration_sec=600)
        self.stdout.write(self.style.SUCCESS('Seeded demo data.'))
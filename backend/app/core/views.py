from rest_framework.decorators import api_view, throttle_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.throttling import UserRateThrottle
from django.db.models import Avg
from .models import Student, Course, Lesson, Attempt
from .serializers import CourseSerializer, AttemptCreateSerializer
from .services.recommender import score_candidate, to_confidence

class WriteThrottle(UserRateThrottle):
    rate='30/min'

@api_view(['GET'])
def student_overview(request, pk:int):
    try:
        student=Student.objects.get(pk=pk)
    except Student.DoesNotExist:
        return Response({'detail':'Not found'}, status=404)
    courses=Course.objects.prefetch_related('lessons').all()
    data=[]
    for c in courses:
        attempts=Attempt.objects.filter(student=student, lesson__course=c).order_by('-timestamp')
        progress=min(100, attempts.count()*10)
        last_activity=attempts.first().timestamp.isoformat() if attempts.exists() else None
        data.append({'id':c.id,'name':c.name,'description':c.description,'difficulty':c.difficulty,'progress':progress,'last_activity':last_activity,'next_up': (c.lessons.first().title if c.lessons.exists() else None)})
    return Response({'student':{'id':student.id,'name':student.name},'courses':data})

@api_view(['GET'])
def student_recommendation(request, pk:int):
    try:
        student=Student.objects.get(pk=pk)
    except Student.DoesNotExist:
        return Response({'detail':'Not found'}, status=404)
    courses=Course.objects.all()
    items=[]
    for c in courses:
        attempts=Attempt.objects.filter(student=student, lesson__course=c).order_by('-timestamp')
        progress=min(100, attempts.count()*10)
        recency_gap_days=5.0; tag_gap=0.3
        hint_rate=(attempts.aggregate(avg=Avg('hints_used'))['avg'] or 0)/3.0
        s, feats=score_candidate(progress, recency_gap_days, tag_gap, hint_rate)
        items.append({'id':str(c.id),'title':f'Continue "{c.name}" — next lesson','score':s,'features':feats})
    items.sort(key=lambda x:x['score'], reverse=True)
    top=items[0]; alts=items[1:3]
    return Response({'recommendation':{'id':top['id'],'title':top['title']},'confidence':to_confidence(top['score']),'reason_features':top['features'],'alternatives':[{'id':a['id'],'title':a['title']} for a in alts]})

@api_view(['POST'])
@throttle_classes([WriteThrottle])
def create_attempt(request):
    ser=AttemptCreateSerializer(data=request.data)
    if ser.is_valid():
        a=ser.save(); return Response({'id':a.id}, status=status.HTTP_201_CREATED)
    return Response(ser.errors, status=400)

@api_view(['POST'])
def analyze_code(request):
    import ast
    code=request.data.get('code','')
    issues=[]
    try:
        tree=ast.parse(code)
        class ArgVisitor(ast.NodeVisitor):
            def visit_FunctionDef(self, node):
                arg_names=[a.arg for a in node.args.args]
                used=set()
                class UseVisitor(ast.NodeVisitor):
                    def visit_Name(self, n):
                        if isinstance(n.ctx, ast.Load): used.add(n.id)
                UseVisitor().visit(node)
                for a in arg_names:
                    if a not in used: issues.append({'rule':'unused-arg','message':f'Function arg "{a}" appears unused.','severity':'info'})
        ArgVisitor().visit(tree)
        class ExceptVisitor(ast.NodeVisitor):
            def visit_ExceptHandler(self, node):
                if node.type is None: issues.append({'rule':'bare-except','message':'Avoid bare except; catch specific exceptions.','severity':'warn'})
        ExceptVisitor().visit(tree)
        class PrintVisitor(ast.NodeVisitor):
            def visit_Call(self, node):
                if getattr(node.func,'id',None)=='print': issues.append({'rule':'print-call','message':'Avoid print statements; use logging.','severity':'info'})
        PrintVisitor().visit(tree)
    except SyntaxError as e:
        issues.append({'rule':'syntax-error','message':str(e),'severity':'error'})
    return Response({'issues':issues})

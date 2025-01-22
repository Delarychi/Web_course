from django.http import JsonResponse
from django.db.models import Count
from django.http import HttpResponseRedirect
from django.views.generic.edit import UpdateView, DeleteView
from django.urls import reverse, reverse_lazy
from django.db.models import Q
from rest_framework import viewsets
from django.shortcuts import get_object_or_404, render, redirect

from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from .filters import SessionFilter, CompetencyFilter, UserProfileFilter

from .models import Project, Session, Competency, Assessment, Profile, User
from .serializers import SessionSerializer, CompetencySerializer, AssessmentSerializer, UserProfileSerializer
from django.db import models

from rest_framework.pagination import PageNumberPagination
from django.db.models import Avg
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from django.core.cache import cache
from django.contrib.auth.decorators import login_required
from .models import Profile
from .forms import CompetencyForm, ProfileAvatarForm, LoginForm, RegisterForm
from django.contrib.auth import authenticate, login, logout

from django.contrib import messages

from .models import VisitLog
from django.contrib.auth.decorators import login_required

# @login_required
def visit_logs(request):
    logs = VisitLog.objects.order_by('-timestamp')  # Логи в обратном порядке
    return render(request, 'visit_logs.html', {'logs': logs})

def register_view(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            # Проверка, существует ли пользователь с таким именем
            if User.objects.filter(username=username).exists():
                messages.error(
                    request, "Пользователь с таким именем уже существует")
            else:
                # Создание нового пользователя
                user = User.objects.create_user(
                    username=username, password=password)
                login(request, user)  # Авторизация после регистрации

                # Сохранение данных в сессии
                request.session['user_logged_in'] = True
                request.session['username'] = user.username
                messages.success(request, "Регистрация прошла успешно")
                return redirect('home')
        else:
            messages.error(
                request, "Ошибка в форме. Проверьте данные и попробуйте снова.")
    else:
        form = RegisterForm()

    return render(request, 'register.html', {'form': form})


def log_out(request):
    logout(request)  # Осуществляем выход из системы
    return redirect('home')


def login_view(request):
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)

                # Сохранение данных в сессии
                request.session['user_logged_in'] = True
                request.session['username'] = user.username
                return redirect('home')
            else:
                messages.error(request, 'Неверное имя пользователя или пароль')
        else:
            messages.error(
                request, 'Ошибка в форме. Пожалуйста, попробуйте снова.')
    else:
        form = LoginForm()

    return render(request, 'login.html', {'form': form})


def get_session_count(request):
    if request:
        session_count = Session.objects.count()
        return JsonResponse({'session_count': session_count})
    else:
        return JsonResponse({'error': 'Invalid request'}, status=400)


class SessionViewSet(viewsets.ModelViewSet):
    serializer_class = SessionSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = SessionFilter
    search_fields = ['title']
    ordering_fields = ['created_at']

    @action(methods=['GET'], detail=False)
    def average_score(self, request):
        """
        Метод для вычисления среднего балла по оценкам для каждой сессии.
        """
        try:
            # Агрегирование среднего балла по сессиям
            sessions_with_avg_score = Session.objects.annotate(
                average_score=Avg('assessments__score')
            )

            # Создаем список с результатами
            data = [
                {
                    'session_id': session.id,
                    'title': session.title,
                    'average_score': session.average_score
                }
                for session in sessions_with_avg_score
            ]

            return Response(data)

        except Exception as e:
            return Response({"error": f"An error occurred: {str(e)}"}, status=500)

    @action(methods=['GET'], detail=False)
    def debug_cache(self, request):
        """
        Отладочный метод для проверки содержимого кэша.
        """
        try:
            cached_data = cache.get('cached_sessions')
            if cached_data:
                return Response({"cached_sessions": cached_data})
            return Response({"message": "Cache is empty"})
        except Exception as e:
            return Response({"error": f"An error occurred: {str(e)}"}, status=500)

    @action(methods=['POST'], detail=False)
    def clear_cache(self, request):
        """
        Метод для очистки кэша.
        """
        cache_key = 'cached_sessions'
        cache.delete(cache_key)
        return Response({"message": "Cache cleared successfully"})

    def get_queryset(self):
        cache_key = 'cached_sessions'
        sessions = cache.get(cache_key)

        if not sessions:
            # Если кэш пуст, извлекаем данные из базы
            sessions = list(Session.objects.values())
            cache.set(cache_key, sessions, timeout=3600)  # Кэш на 1 час

        # Преобразуем данные в QuerySet
        ids = [s['id'] for s in sessions]
        queryset = Session.objects.filter(id__in=ids)

        # Фильтрация
        status = self.request.query_params.get('status')
        if status == 'active':
            queryset = queryset.exclude(is_active=False)
        elif status == 'inactive':
            queryset = queryset.filter(is_active=False)

        return queryset


def competency_view(request):
    if request.method == 'POST':
        form = CompetencyForm(request.POST)
        if form.is_valid():
            # Сохраняем форму, если она валидна
            form.save()
            # После успешной отправки формы перенаправляем на страницу успеха
            return HttpResponseRedirect(reverse('home'))
    else:
        form = CompetencyForm()

    return render(request, 'competency_form.html', {'form': form})


class CompetencyViewSet(viewsets.ModelViewSet):
    queryset = Competency.objects.all()
    serializer_class = CompetencySerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = CompetencyFilter

    # Пример добавления фильтра icontains и contains
    @action(methods=['GET'], detail=False)
    def filter_by_name(self, request):
        """
        Фильтруем компетенции по имени, используя icontains.
        """
        name = request.query_params.get('name')
        if name:
            competencies = Competency.objects.filter(name__icontains=name)
            serializer = self.get_serializer(competencies, many=True)
            return Response(serializer.data)
        return Response({"detail": "Name query parameter is required"}, status=400)

    @action(methods=['GET'], detail=False)
    def filter_contains(self, request):
        """
        Фильтруем компетенции по имени, используя contains.
        """
        name = request.query_params.get('name')
        if name:
            competencies = Competency.objects.filter(name__contains=name)
            serializer = self.get_serializer(competencies, many=True)
            return Response(serializer.data)
        return Response({"detail": "Name query parameter is required"}, status=400)

    # Пример использования values_list
    @action(methods=['GET'], detail=False)
    def list_names(self, request):
        """
        Получаем список всех имен компетенций.
        """
        names = Competency.objects.values_list('name', flat=True)
        return Response(names)

    # Пример использования count
    @action(methods=['GET'], detail=False)
    def competency_count(self, request):
        """
        Получаем количество компетенций.
        """
        count = Competency.objects.count()
        return Response({"competency_count": count})

    # Пример использования exists
    @action(methods=['GET'], detail=False)
    def competency_exists(self, request):
        """
        Проверяем, существует ли компетенция с указанным именем.
        """
        name = request.query_params.get('name')
        if name:
            exists = Competency.objects.filter(name=name).exists()
            return Response({"exists": exists})
        return Response({"detail": "Name query parameter is required"}, status=400)

    # Пример использования update
    @action(methods=['POST'], detail=True)
    def update_competency(self, request, pk=None):
        """
        Обновляем информацию о компетенции с использованием ORM.
        """
        data = request.data
        fields_to_update = {}
        if 'name' in data:
            fields_to_update['name'] = data['name']
        if 'description' in data:
            fields_to_update['description'] = data['description']
        if 'department' in data:
            fields_to_update['department'] = data['department']

        if fields_to_update:
            updated_count = Competency.objects.filter(
                pk=pk).update(**fields_to_update)

            if updated_count > 0:
                return Response({"detail": "Competency updated successfully"}, status=status.HTTP_200_OK)
            else:
                return Response({"detail": "Competency not found"}, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({"detail": "No fields provided for update"}, status=status.HTTP_400_BAD_REQUEST)

    # Пример использования delete
    @action(methods=['DELETE'], detail=True)
    def delete_competency(self, request, pk=None):
        """
        Удаляем компетенцию по идентификатору.
        """
        competency = self.get_object()
        competency.delete()
        return Response({"detail": "Competency deleted successfully"}, status=status.HTTP_204_NO_CONTENT)

    # Пример применения chaining filters
    @action(methods=['GET'], detail=False)
    def filter_by_multiple(self, request):
        """
        Фильтруем компетенции по имени и другому атрибуту с использованием chaining filters.
        """
        name = request.query_params.get('name')
        department = request.query_params.get('department')

        if name and department:
            competencies = Competency.objects.filter(
                Q(name__icontains=name) & Q(department__icontains=department)
            )
            serializer = self.get_serializer(competencies, many=True)
            return Response(serializer.data)
        return Response({"detail": "Both 'name' and 'department' query parameters are required"}, status=400)


class UserProfileViewSet(viewsets.ModelViewSet):
    queryset = Profile.objects.all()
    serializer_class = UserProfileSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = UserProfileFilter


class AssessmentPagination(PageNumberPagination):
    page_size = 10  # Здесь происходит Limiting Querysets
    max_page_size = 100


class AssessmentViewSet(viewsets.ModelViewSet):
    queryset = Assessment.objects.all()
    serializer_class = AssessmentSerializer
    ordering_fields = ['created_at']

    def get_queryset(self):
        queryset = super().get_queryset()
        created_at = self.request.query_params.get('created_at')
        if created_at:
            queryset = queryset.order_by(created_at__date=-created_at)

        score = self.request.query_params.get('score')
        session = self.request.query_params.get('session')

        if score and session:
            queryset = queryset.filter(Q(score=score) & Q(session__id=session))
        elif score:
            queryset = queryset.filter(Q(score=score))
        elif session:
            queryset = queryset.filter(Q(session__id=session))

        return queryset

    @action(methods=['GET'], detail=False)
    def by_user(self, request):
        user_id = request.query_params.get('user_id')
        if user_id:
            assessments = get_object_or_404(Assessment, evaluator__id=user_id)
            # assessments = Assessment.objects.filter(evaluator__id=user_id)
            serializer = self.get_serializer(assessments, many=True)
            return Response(serializer.data)
        return Response({"detail": "user_id parameter is required"}, status=400)

    @action(methods=['POST'], detail=True)
    def add_assessment(self, request, pk=None):
        session = self.get_object()
        data = request.data
        data['session'] = session.id

        serializer = self.get_serializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProfileUpdateView(UpdateView):
    model = Profile
    fields = ['full_name', 'department', 'role']
    template_name = 'profile_update.html'

    def get_success_url(self):
        return reverse_lazy('profile_detail', kwargs={'pk': self.object.pk})


class ProfileDeleteView(DeleteView):
    model = Profile
    template_name = 'profile_confirm_delete.html'

    def get_success_url(self):
        return reverse_lazy('profile_detail', kwargs={'pk': self.object.pk})


def profile_detail(request, pk):
    profile = Profile.objects.get(id=pk)
    return render(request, 'profile_detail.html', {'profile': profile})


@login_required
def edit_avatar(request):
    profile = get_object_or_404(Profile, user=request.user)

    if request.method == "POST":
        form = ProfileAvatarForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            # После сохранения редиректим обратно в профиль
            return redirect('profile_detail', pk=profile.id)
    else:
        form = ProfileAvatarForm(instance=profile)

    return render(request, 'edit_avatar.html', {'form': form})


def home(request):
    query = request.GET.get('query', '')

    # Проверяем, аутентифицирован ли пользователь
    if request.user.is_authenticated:
        try:
            profile = request.user.profile
        except Profile.DoesNotExist:
            profile = None
    else:
        profile = None

    if query:
        active_sessions = Session.objects.filter(title__icontains=query)
        current_projects = Project.objects.filter(name__icontains=query)
        top_competencies = Competency.objects.filter(name__icontains=query)
    else:
        active_sessions = Session.objects.filter(
            is_active=True).order_by('-created_at')[:5]
        current_projects = Project.objects.filter(
            end_date__isnull=False).order_by('-start_date')[:5]
        top_competencies = Competency.objects.annotate(
            session_count=models.Count('sessions_set')
        ).order_by('-session_count')[:5]

    context = {
        'active_sessions': active_sessions,
        'current_projects': current_projects,
        'top_competencies': top_competencies,
        'query': query,
        'text': 'рады видеть!',
        'profile': profile
    }
    return render(request, 'index.html', context)


def delete_session(request, session_id):
    if request.method == 'POST':
        session = get_object_or_404(Session, id=session_id)
        session.delete()
        messages.success(request, 'Сессия успешно удалена.')
    return redirect('all_sessions')


def all_sessions(request):
    sessions = Session.objects.all()
    return render(request, 'all_sessions.html', {'sessions': sessions})


def all_projects(request):
    projects = Project.objects.all()
    return render(request, 'all_projects.html', {'projects': projects})


def all_competencies(request):
    competencies = Competency.objects.all()
    return render(request, 'all_competencies.html', {'competencies': competencies})


def session_detail(request, pk):
    session = get_object_or_404(Session, pk=pk)
    return render(request, 'session_detail.html', {'session': session})


def project_detail(request, pk):
    project = get_object_or_404(Project, pk=pk)
    return render(request, 'project_detail.html', {'project': project})


def competency_detail(request, pk):
    competency = get_object_or_404(Competency, pk=pk)
    return render(request, 'competency_detail.html', {'competency': competency})

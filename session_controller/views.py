from django.db.models import Q
from rest_framework import viewsets

from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from .filters import SessionFilter, CompetencyFilter, UserProfileFilter

from .models import Session, Competency, Assessment, Profile
from .serializers import SessionSerializer, CompetencySerializer, AssessmentSerializer, UserProfileSerializer

from rest_framework.pagination import PageNumberPagination

from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from django.core.cache import cache


class SessionViewSet(viewsets.ModelViewSet):
    serializer_class = SessionSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = SessionFilter
    search_fields = ['title']
    ordering_fields = ['created_at']

    @action(methods=['GET'], detail=False)
    def debug_cache(self, request):
        """
        Отладочный метод для проверки содержимого кэша.
        """
        cached_data = cache.get('cached_sessions')
        if cached_data:
            return Response({"cached_sessions": cached_data})
        return Response({"message": "Cache is empty"})

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
            queryset = queryset.filter(is_active=True)
        elif status == 'inactive':
            queryset = queryset.filter(is_active=False)

        return queryset


class CompetencyViewSet(viewsets.ModelViewSet):
    queryset = Competency.objects.all()
    serializer_class = CompetencySerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = CompetencyFilter


class UserProfileViewSet(viewsets.ModelViewSet):
    queryset = Profile.objects.all()
    serializer_class = UserProfileSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = UserProfileFilter


class AssessmentPagination(PageNumberPagination):
    page_size = 10
    max_page_size = 100


class AssessmentViewSet(viewsets.ModelViewSet):
    queryset = Assessment.objects.all()
    serializer_class = AssessmentSerializer
    ordering_fields = ['created_at']

    def get_queryset(self):
        queryset = super().get_queryset()
        created_at = self.request.query_params.get('created_at')
        if created_at:
            queryset = queryset.filter(created_at__date=created_at)

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
            assessments = Assessment.objects.filter(evaluator__id=user_id)
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

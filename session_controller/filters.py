from django.db.models import Q
import django_filters
from django_filters import rest_framework as filters
from .models import Session, Competency


class SessionFilter(filters.FilterSet):
    title = filters.CharFilter(lookup_expr='icontains')
    evaluated = filters.CharFilter(
        field_name='evaluated__username', lookup_expr='icontains')
    created_at = filters.DateFromToRangeFilter()

    class Meta:
        model = Session
        fields = ['title', 'evaluated', 'created_at']


class CompetencyFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = Competency
        fields = ['name']


class UserProfileFilter(filters.FilterSet):
    role = filters.CharFilter(lookup_expr='icontains')
    is_active = filters.BooleanFilter()

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)
        role = self.request.query_params.get('role')
        is_active = self.request.query_params.get('is_active')

        if role and is_active is not None:
            queryset = queryset.filter(
                Q(role__icontains=role) & Q(user__is_active=is_active))

        return queryset

from django.contrib import admin
from import_export import resources
from import_export.admin import ExportMixin
from .models import Evaluator, Session, Assessment, Competency, Profile
from django.urls import reverse
from django.utils.html import format_html


class EvaluatorInline(admin.TabularInline):
    model = Evaluator
    extra = 1
    fields = ('evaluator',)
    fk_name = 'session'


class SessionAdmin(admin.ModelAdmin):
    list_display = ('title', 'evaluated_link', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ['title', 'evaluated__username']
    fields = ('title', 'evaluated', 'is_active')
    inlines = [EvaluatorInline]

    def evaluated_link(self, obj):
        # предполагаем, что evaluated - это User
        url = reverse("admin:auth_user_change", args=[obj.evaluated.id])
        return format_html('<a href="{}">{}</a>', url, obj.evaluated.username)

    evaluated_link.short_description = 'Evaluated User'


admin.site.register(Session, SessionAdmin)


class AssessmentResource(resources.ModelResource):
    class Meta:
        model = Assessment
        fields = ('session', 'competency', 'evaluator', 'score', 'created_at')
        export_order = ('session', 'competency',
                        'evaluator', 'score', 'created_at')

    def dehydrate_session(self, assessment):
        return assessment.session.title if assessment.session else 'N/A'

    def dehydrate_competency(self, assessment):
        return assessment.competency.name if assessment.competency else 'N/A'

    def dehydrate_evaluator(self, assessment):
        return assessment.evaluator.username if assessment.evaluator else 'N/A'

    def dehydrate_score(self, assessment):
        return f'{assessment.score} points'

    def dehydrate_created_at(self, assessment):
        return assessment.created_at.strftime('%Y-%m-%d')


class AssessmentAdmin(ExportMixin, admin.ModelAdmin):
    list_display = ('session', 'competency',
                    'evaluator', 'score', 'created_at')
    resource_class = AssessmentResource
    list_filter = ('created_at', 'score', 'evaluator')
    search_fields = ['session__title', 'competency__name']


admin.site.register(Assessment, AssessmentAdmin)

admin.site.register(Evaluator)


class ProfileAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'department', 'role',)
    list_filter = ('hire_date', 'department')
    search_fields = ['full_name', 'role']
    fieldsets = (
        (None, {
            'fields': ('full_name', 'department', 'role')
        }),
        ('Dates', {
            'fields': ('hire_date', 'is_active'),
            'classes': ('collapse',)
        }),
    )


admin.site.register(Profile, ProfileAdmin)
admin.site.register(Competency)

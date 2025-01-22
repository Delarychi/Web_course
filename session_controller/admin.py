from django.template.loader import render_to_string
from reportlab.pdfgen import canvas
from django.http import HttpResponse
from .models import Profile, SessionCompetency
from django.contrib import admin
from import_export import resources
from import_export.admin import ExportMixin
from .models import Evaluator, Session, Assessment, Competency, Profile, Project
from django.urls import reverse
from django.utils.html import format_html
import pdfkit


class EvaluatorInline(admin.TabularInline):
    model = Evaluator
    extra = 1
    fields = ('evaluator',)
    fk_name = 'session'


class SessionAdmin(admin.ModelAdmin):
    list_display = ('title', 'evaluated_link', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    list_display_links = ('title',)
    search_fields = ['title', 'evaluated__username']
    fields = ('title', 'evaluated', 'is_active')
    raw_id_fields = ('evaluated',)
    date_hierarchy = 'created_at'
    inlines = [EvaluatorInline]

    @admin.display(description='Evaluated User')
    def evaluated_link(self, obj):
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
admin.site.register(Project)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'user', 'department', 'role',)
    list_filter = ('hire_date', 'department', 'role', 'is_active')
    search_fields = ['full_name', 'role', 'user__username']
    readonly_fields = ('is_active',)
    actions = ['export_resume_as_pdf']

    filter_horizontal = ('projects', )

    fieldsets = (
        (None, {
            'fields': ('user', 'full_name', 'department', 'role', 'avatar', 'portfolio', 'resume')
        }),
        ('Dates & Status', {
            'fields': ('hire_date', 'is_active'),
            'classes': ('collapse',)
        }),
    )

    def export_resume_as_pdf(self, request, queryset):
        if not queryset.exists():
            self.message_user(
                request, "Нет выбранных профилей для экспорта.", level='error')
            return

        # Рендерим HTML-шаблон
        path_to_wkhtmltopdf = r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'  # Укажите путь к wkhtmltopdf
        config = pdfkit.configuration(wkhtmltopdf=path_to_wkhtmltopdf)

        html_string = render_to_string(
            'pdf_template.html', {'profiles': queryset})

        # Генерируем PDF с помощью pdfkit
        pdf = pdfkit.from_string(html_string, False, configuration=config)
        # pdf = pdfkit.from_string(html_string, False)

        # Отправляем PDF в ответе
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="resumes.pdf"'
        return response

    export_resume_as_pdf.short_description = "Экспортировать резюме в PDF"


# admin.site.register(Profile, ProfileAdmin)

admin.site.register(Competency)

admin.site.register(SessionCompetency)

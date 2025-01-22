from django.db import models
from django.forms import ValidationError
from django.urls import reverse
from django.contrib.auth.models import User
from simple_history.models import HistoricalRecords



class VisitLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    path = models.CharField(max_length=255)
    method = models.CharField(max_length=10)
    timestamp = models.DateTimeField()

    def __str__(self):
        return f"{self.user.username} visited {self.path} on {self.timestamp}"


ROLES = [('employee', 'Employee'), ('team_lead', 'Team Lead'),
         ('hr_manager', 'HR Manager')]


class Profile(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="profile")
    full_name = models.CharField(max_length=255, blank=True, null=True)
    department = models.CharField(max_length=100, blank=True, null=True)
    role = models.CharField(max_length=50, choices=ROLES)
    hire_date = models.DateField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    resume = models.FileField(upload_to='resumes/', blank=True, null=True)
    portfolio = models.URLField(max_length=500, blank=True, null=True)
    projects = models.ManyToManyField(
        'Project', related_name='profiles', blank=True)

    def clean_email(self):
        email = self.email.strip().lower()
        if Profile.objects.filter(email=email).exclude(id=self.id).exists():
            raise ValidationError("Email уже используется!")

        return email

    # commit=True (по умолчанию): Когда вызывается save(), объект сохраняется в базе данных сразу после вызова метода, а не в память
    def save(self, *args, **kwargs):
        if not self.full_name:
            self.full_name = self.user.get_full_name()
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('profile_detail', kwargs={'pk': self.id})

    def __str__(self):
        return f"{self.user.username} - {self.role}"

    class Meta:
        verbose_name = 'Профиль'
        verbose_name_plural = 'Профили'


class Competency(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    history = HistoricalRecords()

    def __str__(self):
        return self.name


class Session(models.Model):
    title = models.CharField(max_length=255)
    evaluated = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="evaluated_sessions")
    competencies = models.ManyToManyField(
        'Competency', through='SessionCompetency', related_name="sessions_set")  # Измените related_name на уникальное имя
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    history = HistoricalRecords()

    def __str__(self):
        return f"{self.title} (Оцениваемый: {self.evaluated.username})"

    @classmethod
    def get_sessions_with_evaluated(cls):
        return cls.objects.select_related('evaluated').all()


class SessionCompetency(models.Model):
    session = models.ForeignKey(
        Session, on_delete=models.CASCADE, related_name="session_competencies")  # Уникальное имя для связи
    competency = models.ForeignKey(
        Competency, on_delete=models.CASCADE, related_name="competency_sessions")  # Уникальное имя для связи
    discription = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ('session', 'competency')

    def __str__(self):
        return f"{self.session.title} - {self.competency.name}"
        # Пример использования prefetch_related в queryset

    @classmethod
    def get_competencies_for_sessions(cls):
        return cls.objects.prefetch_related('competency', 'session').all()


class Assessment(models.Model):
    session = models.ForeignKey(
        Session, on_delete=models.CASCADE, related_name="assessments")
    competency = models.ForeignKey(
        Competency, on_delete=models.CASCADE, related_name="assessments")
    evaluator = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="given_assessments")
    score = models.PositiveSmallIntegerField()
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    history = HistoricalRecords()

    class Meta:
        unique_together = ('session', 'competency', 'evaluator')
        ordering = ['-created_at']

    def __str__(self):
        return f"Сессия: {self.session.title}, Компетенция: {self.competency.name}, Оценщик: {self.evaluator.username}"


class Evaluator(models.Model):
    session = models.ForeignKey(
        Session, on_delete=models.CASCADE, related_name="evaluators")
    evaluator = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="evaluations")

    class Meta:
        unique_together = ('session', 'evaluator')

    def __str__(self):
        return f"Сессия: {self.session.title}, Оценщик: {self.evaluator.username}"


class Project(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Проект'
        verbose_name_plural = 'Проекты'

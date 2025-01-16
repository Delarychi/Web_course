from django.db import models
from django.contrib.auth.models import User
from simple_history.models import HistoricalRecords

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

    def __str__(self):
        return f"{self.user.username} - {self.role}"


class Session(models.Model):
    title = models.CharField(max_length=255)
    evaluated = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="evaluated_sessions")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    history = HistoricalRecords()

    def __str__(self):
        return f"{self.title} (Оцениваемый: {self.evaluated.username})"


class Competency(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    history = HistoricalRecords()

    def __str__(self):
        return self.name


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


class SessionCompetency(models.Model):
    session = models.ForeignKey(
        Session, on_delete=models.CASCADE, related_name="competencies")
    competency = models.ForeignKey(
        Competency, on_delete=models.CASCADE, related_name="sessions")

    class Meta:
        unique_together = ('session', 'competency')

    def __str__(self):
        return f"{self.session.title} - {self.competency.name}"


class Evaluator(models.Model):
    session = models.ForeignKey(
        Session, on_delete=models.CASCADE, related_name="evaluators")
    evaluator = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="evaluations")

    class Meta:
        unique_together = ('session', 'evaluator')

    def __str__(self):
        return f"Сессия: {self.session.title}, Оценщик: {self.evaluator.username}"

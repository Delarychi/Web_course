from celery import shared_task
from django.core.mail import send_mail

@shared_task
def archive_old_sessions():
    from datetime import timedelta
    from django.utils.timezone import now
    from .models import Session

    cutoff_date = now() - timedelta(days=30)
    Session.objects.filter(is_active=False, created_at__lt=cutoff_date).delete()
    return "Старые сессии архивированы"

@shared_task
def send_reminder_email(user_email, subject, message):
    """
    Отправка напоминания на указанный email.
    """
    send_mail(
        subject=subject,
        message=message,
        from_email='no-reply@project.com',
        recipient_list=[user_email],
    )
    return f"Напоминание отправлено на {user_email}"

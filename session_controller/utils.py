from django.core.mail import send_mail

def send_test_email():
    send_mail(
        'Тема письма',
        'Текст письма',
        'no-reply@test.com',
        ['recipient@example.com'],
        fail_silently=False,
    )

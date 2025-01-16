from django.core.management.base import BaseCommand
from faker import Faker
from django.contrib.auth.models import User
from session_controller.models import Profile, Session, Competency, Assessment, SessionCompetency, Evaluator
import random
from datetime import timedelta, date

ROLES = ['employee', 'team_lead', 'hr_manager']

class Command(BaseCommand):
    help = "Заполняет базу данных тестовыми данными"

    def handle(self, *args, **kwargs):
        fake = Faker()

        # Создание пользователей
        users = []
        for _ in range(20):  # 20 пользователей
            username = fake.user_name()
            user = User.objects.create_user(username=username, password='password123')
            Profile.objects.create(
                user=user,
                full_name=fake.name(),
                department=fake.word(),
                role=random.choice(ROLES),
                hire_date=fake.date_this_decade()
            )
            users.append(user)

        # Создание компетенций
        competencies = []
        for _ in range(10):  # 10 компетенций
            competency = Competency.objects.create(
                name=fake.job(),
                description=fake.text(max_nb_chars=200)
            )
            competencies.append(competency)

        # Создание сессий
        sessions = []
        for _ in range(5):  # 5 сессий
            session = Session.objects.create(
                title=fake.sentence(nb_words=4),
                evaluated=random.choice(users),
                is_active=random.choice([True, False])
            )
            sessions.append(session)

            # Добавление компетенций в сессии
            for competency in random.sample(competencies, k=3):  # 3 случайные компетенции
                SessionCompetency.objects.create(session=session, competency=competency)

            # Назначение оценщиков
            evaluators = random.sample(users, k=3)  # 3 случайных оценщика
            for evaluator in evaluators:
                Evaluator.objects.create(session=session, evaluator=evaluator)

        # Создание оценок
        for session in sessions:
            for competency in session.competencies.all():
                for evaluator in session.evaluators.all():
                    Assessment.objects.create(
                        session=session,
                        competency=competency.competency,
                        evaluator=evaluator.evaluator,
                        score=random.randint(1, 10),
                        comment=fake.text(max_nb_chars=100)
                    )

        self.stdout.write(self.style.SUCCESS("Данные успешно добавлены!"))

from rest_framework.routers import DefaultRouter #те роутеры, к которым можно обращаться за данными
from .views import SessionViewSet, CompetencyViewSet, AssessmentViewSet, UserProfileViewSet

router = DefaultRouter()
router.register('users', UserProfileViewSet, basename='users')
router.register('sessions', SessionViewSet, basename='session')
router.register('competencies', CompetencyViewSet, basename='competency')
router.register('assessments', AssessmentViewSet, basename='assessment')

urlpatterns = router.urls

"""
URL configuration for service_360 project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf.urls.static import static
from django.conf import settings
from django.contrib import admin
from django.urls import path, include
from session_controller.views import *
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

urlpatterns = [
    path('', home, name='home'),

    path('profile/edit-avatar/', edit_avatar, name='edit_avatar'),
    path('profile/<int:pk>/edit/', ProfileUpdateView.as_view(), name='profile_edit'),
    path('profile/<int:pk>/delete/',
         ProfileDeleteView.as_view(), name='profile_delete'),
    path('profile/<int:pk>/', profile_detail, name='profile_detail'),

    path('sessions/', all_sessions, name='all_sessions'),
    path('projects/', all_projects, name='all_projects'),
    path('competencies/', all_competencies, name='all_competencies'),

    path('session/<int:pk>/', session_detail, name='session_detail'),
    path('project/<int:pk>/', project_detail, name='project_detail'),
    path('competency/<int:pk>/', competency_detail, name='competency_detail'),

    path('sessions/delete/<int:session_id>/',
         delete_session, name='delete_session'),
    path('competency/', competency_view, name='competency_view'),
    path('login/', login_view, name='login'),
    path('logout/', log_out, name='logout'),
    path('register/', register_view, name='register'),


    path('logs/', visit_logs, name='visit_logs'),
    path('admin/', admin.site.urls),
    path('api/', include('session_controller.urls')),
]
schema_view = get_schema_view(
    openapi.Info(
        title="360 Assessment API",
        default_version='v1',
        description="API documentation for 360 assessment system",
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)
urlpatterns += [
    path('swagger/', schema_view.with_ui('swagger',
         cache_timeout=0), name='schema-swagger-ui'),
]
if settings.DEBUG:  # Панель будет показываться только в режиме DEBUG
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

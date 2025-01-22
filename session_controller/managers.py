from django.db import models
class ActiveSessionseManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(isActive=True)
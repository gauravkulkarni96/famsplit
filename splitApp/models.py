from django.db import models
from django.contrib.auth.models import User as user

# Create your models here.
class User(models.Model):
    user = models.OneToOneField(
        user, null=False, blank=False,
        on_delete=models.CASCADE, related_name='user'
        )
    name = models.CharField(max_length=255, null=True, blank=False)
    email = models.EmailField(null=True, blank=False)
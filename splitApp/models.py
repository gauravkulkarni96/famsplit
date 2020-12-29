from django.db import models
from django.contrib.auth.models import User as user
from django.db.models.signals import post_save

# Create your models here.
class User(models.Model):
    user = models.OneToOneField(
        user, null=False, blank=False,
        on_delete=models.CASCADE, related_name='user'
        )
    name = models.CharField(max_length=255, null=True, blank=False)
    email = models.EmailField(null=True, blank=False)

def create_user(sender, instance, created, **kwargs):
    """
    create a user when a django  user is created
    """
    user, created = User.objects.get_or_create(user=instance)
    user.name = instance.first_name
    user.email = instance.email
    try:
        user.avatar = instance.avatar
    except Exception as e:
        pass
    user.save()

post_save.connect(create_user, sender=user)
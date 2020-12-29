from django.db import models
from django.contrib.auth.models import User as user
from django.db.models.signals import post_save
from django.db.models.query import QuerySet

# Create your models here.
class BaseModelQuerySet(QuerySet):
    '''
    using BaseModel for queryset operations
    '''
    def delete(self):
        for obj in self:
            obj.is_deleted=True
            obj.deleted_on=timezone.now()
            obj.save()


class BaseModelManager(models.Manager):
    '''
    manager for returning non-deleted objects
    '''
    def get_queryset(self):
        return BaseModelQuerySet(self.model, using=self._db).filter(
            is_deleted=False)


class BaseModel(models.Model):
    '''
    BaseModel for enabling soft-delete and adding
    generic fields
    '''
    class Meta:
        abstract = True

    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)
    deleted_on = models.DateTimeField(null=True, blank=True)
    objects = BaseModelManager()
    original_objects = models.Manager()

    def delete(self):
        self.is_deleted=True
        self.deleted_on=timezone.now()
        self.save()


class User(BaseModel):
    '''
    adding extra Fields to base user model.
    '''
    user = models.OneToOneField(
        user, null=False, blank=False,
        on_delete=models.CASCADE, related_name='user'
        )
    name = models.CharField(max_length=255, null=True, blank=False)
    email = models.EmailField(null=True, blank=False)

def create_user(sender, instance, created, **kwargs):
    """
    create a user when a django user is created
    """
    user, created = User.objects.get_or_create(user=instance)
    user.name = instance.first_name
    user.email = instance.email
    try:
        user.avatar = instance.avatar
    except Exception as e:
        pass
    user.save()

# Signal to create User object when Django User is created
post_save.connect(create_user, sender=user)

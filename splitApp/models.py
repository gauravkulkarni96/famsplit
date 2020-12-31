from django.db import models
from django.contrib.auth.models import User as user
from django.db.models.signals import post_save
from django.db.models.query import QuerySet
from famsplit.settings import SUPPORTED_CURRENCIES
from django.utils import timezone

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

    # should be uploaded to services like S3 ideally
    profile_picture = models.ImageField(upload_to ='uploads/',null=True, blank=True)

    def __str__(self):
        return self.name

def create_user(sender, instance, created, **kwargs):
    """
    create a user when a django user is created
    """
    user, created = User.objects.get_or_create(user=instance)
    user.name = instance.username
    user.email = instance.email
    try:
        user.avatar = instance.avatar
    except Exception as e:
        pass
    user.save()

# Signal to create User object when Django User is created
post_save.connect(create_user, sender=user)


class Group(BaseModel):
    # Keeping name unique for easy usage in API.
    # Should be done via unique ID ideally.
    name = models.CharField(max_length=255, null=False, blank=False, unique=True)
    created_by = models.ForeignKey('User', null=False, blank=False,
                            related_name="group",
                            on_delete=models.PROTECT
                            )

    # should be uploaded to services like S3 ideally
    group_icon = models.ImageField(upload_to ='uploads/',null=True, blank=True)
    simplify_payments = models.BooleanField(default=False)

    default_currency = models.CharField(max_length=20, null=False,
                                        blank=False, choices=SUPPORTED_CURRENCIES,
                                        default='INR')

    def __str__(self):
        return self.name

class Membership(BaseModel):
    user = models.ForeignKey('User', null=False, blank=False,
                            related_name="membership",
                            on_delete=models.PROTECT
                            )
    group = models.ForeignKey('Group', null=False, blank=False,
                            related_name="membership",
                            on_delete=models.PROTECT
                            )


class Bill(BaseModel):
    title = models.CharField(max_length=500, null=True, blank=True)

    # make this field Nullable to add non-group bills
    group = models.ForeignKey('Group', null=False, blank=False,
                            related_name="bill",
                            on_delete=models.PROTECT
                            )
    added_by = models.ForeignKey('User', null=False, blank=False,
                            related_name="bill",
                            on_delete=models.PROTECT
                            )
    bill_amount = models.FloatField(null=False, blank=False, default=0)

    def __str__(self):
        return self.title


class Expense(BaseModel):
    bill = models.ForeignKey('Bill', null=False, blank=False,
                            related_name="expense",
                            on_delete=models.PROTECT
                            )
    user = models.ForeignKey('User', null=False, blank=False,
                            related_name="expense",
                            on_delete=models.PROTECT
                            )
    amount_paid = models.FloatField(null=False, blank=False, default=0)
    amount_owed = models.FloatField(null=False, blank=False, default=0)

    def get_balance(self):
        return self.amount_paid - self.amount_owed


class Payment(BaseModel):
    bill = models.ForeignKey('Bill', null=False, blank=False,
                            related_name="payment",
                            on_delete=models.PROTECT
                            )
    payer = models.ForeignKey('User', null=False, blank=False,
                            related_name="payer",
                            on_delete=models.PROTECT
                            )
    receiver = models.ForeignKey('User', null=False, blank=False,
                            related_name="receiver",
                            on_delete=models.PROTECT
                            )
    amount = models.FloatField(null=False, blank=False, default=0)


class Note(BaseModel):
    bill = models.ForeignKey('Bill', null=False, blank=False,
                            related_name="note",
                            on_delete=models.PROTECT
                            )
    text = models.TextField(null=True, blank=True)

    # should be uploaded to services like S3 ideally
    image = models.ImageField(upload_to ='uploads/',null=True, blank=True)

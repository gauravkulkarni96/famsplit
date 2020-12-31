from django.contrib import admin
from splitApp.models import (
    User, Group, Membership,
    Bill, Expense, Payment, Note
)
# Register your models here.

class UserAdmin(admin.ModelAdmin):
    ordering = ("name", "email")
    search_fields = ("name", "email")
    list_display = ("name", "email")

class GroupAdmin(admin.ModelAdmin):
    ordering = ("name",)
    search_fields = ("name",)
    list_display = ("name", "created_by", "simplify_payments", "default_currency")

class MembershipAdmin(admin.ModelAdmin):
    search_fields = ("user__name", "group__name")
    list_display = ("user", "group")

class BillAdmin(admin.ModelAdmin):
    ordering = ("title",)
    search_fields = ("title", "group__name", "added_by__name")
    list_display = ("title", "group", "added_by", "bill_amount")

class ExpenseAdmin(admin.ModelAdmin):
    search_fields = ("user__name", "bill__title")
    list_display = ("bill", "user", "amount_paid", "amount_owed")

class PaymentAdmin(admin.ModelAdmin):
    search_fields = ("bill__title", "payer__name", "receiver__name")
    list_display = ("bill", "payer", "receiver", "amount")

class NoteAdmin(admin.ModelAdmin):
    search_fields = ("bill__title",)
    list_display = ("bill", "text", "image")

admin.site.register(User, UserAdmin)
admin.site.register(Group, GroupAdmin)
admin.site.register(Membership, MembershipAdmin)
admin.site.register(Bill, BillAdmin)
admin.site.register(Expense, ExpenseAdmin)
admin.site.register(Payment, PaymentAdmin)
admin.site.register(Note, NoteAdmin)

from django.contrib import admin

from .models import DrillNight, TransactionRecord

@admin.register(DrillNight)
class DrillNightAdmin(admin.ModelAdmin):

    list_display = ["date", "day_of_week", "time", "cut_off_delta", "meals_sold"]
    date_hierarchy = "date_time"

    def meals_sold(self, obj):
        return obj.meals_sold
    meals_sold.short_description = "Approximate Meals Sold"


@admin.action(description='Refund and cancel selected transactions')
def refund(modeladmin, request, queryset):
    [transaction.refund(ignore_checks=True) for transaction in queryset.all()]

@admin.register(TransactionRecord)
class TransactionRecordAdmin(admin.ModelAdmin):

    list_filter = ["status"]
    list_display = ["drill_night", "name", "email", "quantity", "status"]
    date_hierarchy = "drill_night__date_time"
    search_fields = ["email", "name"]

    actions = [refund]


from django.contrib import admin
from .models import Borrower, ModelMetrics


@admin.register(Borrower)
class BorrowerAdmin(admin.ModelAdmin):
    list_display = ("id", "credit_score", "risk_category", "created_at")
    search_fields = ("id",)
    list_filter = ("risk_category",)


@admin.register(ModelMetrics)
class ModelMetricsAdmin(admin.ModelAdmin):
    list_display = ("model_name", "accuracy", "auc_score", "created_at")
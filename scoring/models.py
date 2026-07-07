from django.db import models


# ================================
# Borrower Input + Prediction Record
# ================================
class Borrower(models.Model):

    # ---------- Raw Input Features ----------
    revolving_utilization = models.FloatField()
    age = models.IntegerField()
    late_30_59 = models.IntegerField()
    debt_ratio = models.FloatField()
    monthly_income = models.FloatField()
    open_credit_lines = models.IntegerField()
    late_90 = models.IntegerField()
    real_estate_loans = models.IntegerField()
    late_60_89 = models.IntegerField()
    dependents = models.IntegerField()

    # ---------- Behavioral Features (computed) ----------
    financial_stability_index = models.FloatField(null=True, blank=True)
    payment_discipline_score = models.FloatField(null=True, blank=True)
    debt_stress_index = models.FloatField(null=True, blank=True)
    credit_utilization_risk = models.FloatField(null=True, blank=True)
    credit_experience_score = models.FloatField(null=True, blank=True)

    # ---------- Model Output ----------
    base_model_risk = models.FloatField(null=True, blank=True)
    final_risk = models.FloatField(null=True, blank=True)
    credit_score = models.IntegerField(null=True, blank=True)
    risk_category = models.CharField(max_length=20, null=True, blank=True)

    # ---------- Explainability ----------
    decision_explanation = models.TextField(null=True, blank=True)

    # ---------- Closed Loop Learning ----------
    actual_default = models.BooleanField(
        null=True,
        blank=True,
        help_text="Actual repayment outcome (for future model improvement)"
    )

    # ---------- Metadata ----------
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Borrower {self.id} — Score {self.credit_score}"


# ================================
# Model Performance Tracking
# ================================
class ModelMetrics(models.Model):

    model_name = models.CharField(max_length=100)

    accuracy = models.FloatField()
    precision = models.FloatField()
    recall = models.FloatField()
    f1_score = models.FloatField()
    auc_score = models.FloatField()

    fairness_ratio = models.FloatField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.model_name} — AUC {self.auc_score}"
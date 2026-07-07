from django.db import models
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

from .models import Borrower
from .services.hybrid_engine import hybrid_credit_score


from .services.drift_monitor import check_model_drift

from django.db.models import Avg, Count


# ======================================
# LANDING PAGE (we design UI later)
# ======================================
def home(request):
    return render(request, "scoring/home.html")


# ======================================
# CREDIT SCORING API (CORE ENDPOINT)
# ======================================
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import traceback
from .models import Borrower
from .services.hybrid_engine import hybrid_credit_score


@csrf_exempt
def score_borrower(request):

    if request.method != "POST":
        return JsonResponse({"error": "POST request required"}, status=400)

    try:
        data = json.loads(request.body)

        print("INPUT RECEIVED:", data)

        # =========================
        # RUN HYBRID ENGINE
        # =========================
        result = hybrid_credit_score(data)

        print("RESULT:", result)

        # =========================
        # EXTRACT VALUES FROM NEW STRUCTURE
        # =========================
        behavioral = result["behavioral_features"]
        model_pred = result["model_prediction"]
        rule_engine = result["rule_engine"]
        final_decision = result["final_decision"]

        # create readable rule explanation text
        rule_explanations = []
        for r in rule_engine["rules_evaluated"]:
            rule_explanations.append(
                f"{r['rule']} → {r.get('risk_adjustment','')} ({r.get('reason','')})"
            )

        # =========================
        # SAVE TO DATABASE
        # =========================
        borrower = Borrower.objects.create(
            revolving_utilization=data["revolving_utilization"],
            age=data["age"],
            late_30_59=data["late_30_59"],
            debt_ratio=data["debt_ratio"],
            monthly_income=data["monthly_income"],
            open_credit_lines=data["open_credit_lines"],
            late_90=data["late_90"],
            real_estate_loans=data["real_estate_loans"],
            late_60_89=data["late_60_89"],
            dependents=data["dependents"],

            financial_stability_index=behavioral["financial_stability"],
            payment_discipline_score=behavioral["payment_discipline"],
            debt_stress_index=behavioral["debt_stress"],
            credit_utilization_risk=data["revolving_utilization"],
            credit_experience_score=behavioral["credit_experience"],

            base_model_risk=model_pred["base_default_probability"],
            final_risk=rule_engine["adjusted_risk"],
            credit_score=final_decision["credit_score"],
            risk_category=final_decision["risk_category"],
            decision_explanation=", ".join(rule_explanations),
        )

        # =========================
        # RETURN RESPONSE
        # =========================
        return JsonResponse({
            "success": True,
            "borrower_id": borrower.id,
            "result": result
        })

    except Exception as e:
        print(traceback.format_exc())
        return JsonResponse({"error": str(e)}, status=500)


# ======================================
# PREDICTION HISTORY (dashboard later)
# ======================================
def prediction_history(request):

    borrowers = Borrower.objects.all().order_by("-created_at")

    return render(
        request,
        "scoring/history.html",
        {"borrowers": borrowers}
    )


# ======================================
# MODEL INFO PAGE (research dashboard later)
# ======================================
def model_info(request):
    return render(request, "scoring/model_info.html")

def scoring_page(request):
    return render(request, "scoring/score.html")

from django.shortcuts import render
from .models import Borrower
from django.db.models import Count


def model_dashboard(request):

    borrowers = Borrower.objects.all()

    total_predictions = borrowers.count()

    risk_distribution = borrowers.values("risk_category") \
        .annotate(count=Count("risk_category"))

    avg_credit_score = (
        borrowers.aggregate(avg=models.Avg("credit_score"))["avg"]
        if total_predictions > 0 else 0
    )

    drift = check_model_drift()

    borrowers = Borrower.objects.all()

    low_income = borrowers.filter(monthly_income__lt=30000)
    medium_income = borrowers.filter(monthly_income__gte=30000, monthly_income__lt=80000)
    high_income = borrowers.filter(monthly_income__gte=80000)


    low_default = low_income.filter(risk_category="High").count() / (low_income.count() or 1)
    medium_default = medium_income.filter(risk_category="High").count() / (medium_income.count() or 1)
    high_default = high_income.filter(risk_category="High").count() / (high_income.count() or 1)

    fairness_ratio = high_default / (low_default or 1)


    context = {
        "total_predictions": total_predictions,
        "risk_distribution": list(risk_distribution),
        "avg_credit_score": round(avg_credit_score or 0, 2),

        # static research metrics (from your experiments)
        "model_metrics": {
            "logistic_auc": 0.79,
            "rf_auc": 0.82,
            "xgb_auc": 0.84,
            "lgbm_auc": 0.85,
            "catboost_auc": 0.854
        },

        "fairness_metrics": {
            "low_income_default": 0.031,
            "medium_income_default": 0.021,
            "high_income_default": 0.009
        },

            "total_predictions": total_predictions,
    "risk_distribution": list(risk_distribution),
    "avg_credit_score": round(avg_credit_score or 0, 2),
    "drift": drift,



        "total_predictions": total_predictions,
    "risk_distribution": list(risk_distribution),
    "avg_credit_score": round(avg_credit_score or 0, 2),

    "fairness_metrics": {
        "low_income_default": round(low_default,3),
        "medium_income_default": round(medium_default,3),
        "high_income_default": round(high_default,3),
        "fairness_ratio": round(fairness_ratio,3)
    }
    }

    return render(request, "scoring/dashboard.html", context)

def borrower_history(request):

    borrowers = Borrower.objects.all().order_by("-created_at")

    return render(request, "scoring/history.html", {
        "borrowers": borrowers
    })
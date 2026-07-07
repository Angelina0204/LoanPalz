from pathlib import Path
import joblib
import numpy as np
import pandas as pd
import shap

# =============================
# LOAD MODEL (runs once)
# =============================
# .parent goes up one directory level. 3 parents = LoanPalz root.
BASE_DIR = Path(__file__).resolve().parent.parent.parent
MODEL_PATH = BASE_DIR / "ml" / "models" / "credit_model.pkl"

model = joblib.load(MODEL_PATH)
# load SHAP explainer once (fast after first load)
explainer = shap.TreeExplainer(model)


# =============================
# HYBRID CREDIT SCORE ENGINE
# =============================
def hybrid_credit_score(data):
    """
    Returns full explainable credit scoring pipeline output
    """

    # =============================
    # STEP 1 — INPUT SUMMARY
    # =============================
    input_summary = {
        "revolving_utilization": data["revolving_utilization"],
        "age": data["age"],
        "late_30_59": data["late_30_59"],
        "late_60_89": data["late_60_89"],
        "late_90": data["late_90"],
        "debt_ratio": data["debt_ratio"],
        "monthly_income": data["monthly_income"],
        "open_credit_lines": data["open_credit_lines"],
        "real_estate_loans": data["real_estate_loans"],
        "dependents": data["dependents"],
    }

    # =============================
    # STEP 2 — BEHAVIORAL FEATURES
    # =============================

    # Financial Stability
    fs = data["monthly_income"] / (
        data["debt_ratio"] * 1000 + data["dependents"] + 1
    )

    # Payment Discipline
    pd_score = 1 / (
        data["late_30_59"]
        + data["late_60_89"]
        + data["late_90"]
        + 1
    )

    # Debt Stress
    ds = (
        data["debt_ratio"]
        * data["revolving_utilization"]
        * (data["open_credit_lines"] + 1)
    )

    # Credit Utilization Risk
    cu = data["revolving_utilization"]

    # Credit Experience
    ce = data["open_credit_lines"] + data["real_estate_loans"]

    behavioral_features = {
        "financial_stability": fs,
        "payment_discipline": pd_score,
        "debt_stress": ds,
        "credit_utilization_risk": cu,
        "credit_experience": ce,
    }

    # =============================
    # STEP 3 — BEHAVIORAL EXPLANATION
    # =============================
    behavioral_calculation = {

        "financial_stability": {
            "formula": "MonthlyIncome / (DebtRatio × 1000 + Dependents + 1)",
            "substitution": f"{data['monthly_income']} / ({data['debt_ratio']}×1000 + {data['dependents']} + 1)",
            "result": round(fs, 3),
            "interpretation": "High stability" if fs > 2000 else "Low stability"
        },

        "payment_discipline": {
            "formula": "1 / (Late30 + Late60 + Late90 + 1)",
            "substitution": f"1 / ({data['late_30_59']} + {data['late_60_89']} + {data['late_90']} + 1)",
            "result": round(pd_score, 3),
            "interpretation": "Good repayment behavior" if pd_score > 0.5 else "Poor payment discipline"
        },

        "debt_stress": {
            "formula": "DebtRatio × Utilization × (OpenLines + 1)",
            "substitution": f"{data['debt_ratio']} × {data['revolving_utilization']} × ({data['open_credit_lines']} + 1)",
            "result": round(ds, 3),
            "interpretation": "High debt stress" if ds > 5 else "Low debt stress"
        },

        "credit_experience": {
            "formula": "OpenLines + RealEstateLoans",
            "substitution": f"{data['open_credit_lines']} + {data['real_estate_loans']}",
            "result": ce,
            "interpretation": "Strong credit experience" if ce > 10 else "Low credit experience"
        }
    }

    # =============================
    # STEP 4 — MODEL PREDICTION
    # =============================
    features = np.array([[
        data["revolving_utilization"],
        data["age"],
        data["late_30_59"],
        data["debt_ratio"],
        data["monthly_income"],
        data["open_credit_lines"],
        data["late_90"],
        data["real_estate_loans"],
        data["late_60_89"],
        data["dependents"],
        fs,
        pd_score,
        ds,
        cu,
        ce
    ]])

    base_risk = float(model.predict_proba(features)[0][1])

        # =============================
    # STEP 4.5 — SHAP EXPLAINABILITY
    # =============================

    feature_names = [
        "revolving_utilization",
        "age",
        "late_30_59",
        "debt_ratio",
        "monthly_income",
        "open_credit_lines",
        "late_90",
        "real_estate_loans",
        "late_60_89",
        "dependents",
        "financial_stability",
        "payment_discipline",
        "debt_stress",
        "credit_utilization_risk",
        "credit_experience"
    ]

    shap_values = explainer.shap_values(features)

    # shap_values for class 1 (default risk)
    shap_contributions = shap_values[0] if isinstance(shap_values, list) else shap_values[0]

    shap_explanation = []

    for name, value in zip(feature_names, shap_contributions):
        shap_explanation.append({
            "feature": name,
            "impact": round(float(value), 4),
            "effect": "increased risk" if value > 0 else "reduced risk"
        })

    model_prediction = {
        "model_name": "CatBoost",
        "total_features_used": 15,
        "base_default_probability": round(base_risk, 3),
        "explanation": "Probability of loan default predicted by gradient boosting model"
    }

    # =============================
    # STEP 5 — HYBRID RULE ENGINE
    # =============================
    risk = base_risk
    rules = []

    if pd_score < 0.5:
        risk += 0.10
        rules.append({
            "rule": "Payment Discipline < 0.5",
            "condition_met": True,
            "risk_adjustment": "+0.10",
            "reason": "Frequent payment delays"
        })

    if fs > 2000:
        risk -= 0.05
        rules.append({
            "rule": "Financial Stability > 2000",
            "condition_met": True,
            "risk_adjustment": "-0.05",
            "reason": "Strong financial stability"
        })

    if ds > 5:
        risk += 0.05
        rules.append({
            "rule": "Debt Stress > 5",
            "condition_met": True,
            "risk_adjustment": "+0.05",
            "reason": "High debt pressure"
        })

    if ce > 10:
        risk -= 0.05
        rules.append({
            "rule": "Credit Experience > 10",
            "condition_met": True,
            "risk_adjustment": "-0.05",
            "reason": "Strong credit history"
        })

    risk = max(0, min(1, risk))

    rule_engine = {
        "rules_evaluated": rules,
        "base_risk": round(base_risk, 3),
        "adjusted_risk": round(risk, 3)
    }

    # =============================
    # STEP 6 — FINAL DECISION
    # =============================
    credit_score = int((1 - risk) * 600 + 300)

    if risk < 0.3:
        category = "Low"
    elif risk < 0.6:
        category = "Medium"
    else:
        category = "High"

    final_decision = {
        "credit_score_formula": "(1 − risk) × 600 + 300",
        "credit_score": credit_score,
        "final_risk": round(risk, 3),
        "risk_category": category,
        "decision_summary": f"{category} risk classification"
    }

    # =============================
    # RETURN FULL EXPLAINABILITY
    # =============================
    return {
        "input_summary": input_summary,
        "behavioral_calculation": behavioral_calculation,
        "behavioral_features": behavioral_features,
        "model_prediction": model_prediction,
        "rule_engine": rule_engine,
        "final_decision": final_decision,
        "shap_explanation": shap_explanation
    }
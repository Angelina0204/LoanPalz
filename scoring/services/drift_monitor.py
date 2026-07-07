import json
from django.db.models import Avg
from scoring.models import Borrower

def check_model_drift():

    with open("ml/models/training_stats.json") as f:
        training_stats = json.load(f)

    live_stats = Borrower.objects.aggregate(
        income_mean=Avg("monthly_income"),
        debt_ratio_mean=Avg("debt_ratio"),
        late_payment_mean=Avg("late_90")
    )

    drift_report = {}

    for feature in training_stats:
        train_val = training_stats[feature]
        live_val = live_stats.get(feature)

        if train_val and live_val:
            drift = abs(live_val - train_val) / train_val
            drift_report[feature] = round(drift, 3)

    return drift_report
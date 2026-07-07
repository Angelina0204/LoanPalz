import os
import joblib
from django.conf import settings


MODEL_PATH = os.path.join(settings.BASE_DIR, "ml", "models", "credit_model.pkl")

model = None


def get_model():
    global model

    if model is None:
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(
                "Model file not found. Train and save model in ml/models/"
            )

        model = joblib.load(MODEL_PATH)

    return model
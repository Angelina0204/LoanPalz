from django.urls import path
from . import views

urlpatterns = [
    # Landing page
    path("", views.home, name="home"),

    # Credit scoring API
   path("score/", views.scoring_page, name="scoring_page"),
path("api/score/", views.score_borrower, name="score_borrower"),

    # Prediction history dashboard
    path("history/", views.prediction_history, name="prediction_history"),
    path("dashboard/", views.model_dashboard, name="dashboard"),

    # Model information / research dashboard
    path("model-info/", views.model_info, name="model_info"),
    path("history/", views.borrower_history, name="borrower_history"),
]

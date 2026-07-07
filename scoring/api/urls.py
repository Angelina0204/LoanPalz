from django.urls import path
from .views import score_application

urlpatterns = [
    path('score/', score_application),
]

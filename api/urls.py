from django.urls import path
from .views import analyze_credit, health

urlpatterns = [
    path("health/", health, name="health"),
    path("credit-applications/analyze/", analyze_credit, name="analyze-credit"),
]

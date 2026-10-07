from django.urls import path
from risk.views import ScenarioView, RoutesView

urlpatterns = [
    path("scenario/", ScenarioView.as_view(), name="scenario"),
    path("routes/", RoutesView.as_view(), name="routes"),
    # /api/segments/ is added in A2
]

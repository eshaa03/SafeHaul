from django.urls import path
from risk.views import ScenarioView, RoutesView, SegmentsView

urlpatterns = [
    path("scenario/", ScenarioView.as_view(), name="scenario"),
    path("routes/", RoutesView.as_view(), name="routes"),
    path("segments/", SegmentsView.as_view(), name="segments"),
]

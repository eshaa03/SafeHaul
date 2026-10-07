from django.urls import path
from servicepoints.views import ServicePointsView

urlpatterns = [
    path("service-points/", ServicePointsView.as_view(), name="service-points"),
]

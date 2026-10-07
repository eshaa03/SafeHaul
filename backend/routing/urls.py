from django.urls import path
from routing.views import TripOptionsView

urlpatterns = [
    path("trip/options/", TripOptionsView.as_view(), name="trip-options"),
]

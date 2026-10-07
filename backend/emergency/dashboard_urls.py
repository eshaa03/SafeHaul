from django.urls import path
from . import views

# HTML page routes — mounted at / by the root urlconf
urlpatterns = [
    path("station/", views.station_dashboard, name="station-dashboard"),
    path("sos-demo/", views.sos_demo, name="sos-demo"),
]

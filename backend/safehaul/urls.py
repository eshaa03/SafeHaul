from django.urls import path, include

urlpatterns = [
    path("api/", include("emergency.urls")),
    path("", include("emergency.dashboard_urls")),
]

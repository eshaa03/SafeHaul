"""
SafeHaul Kerala — root URL configuration.
"""

from django.urls import path, include

urlpatterns = [
    path("api/", include("risk.urls")),
    path("api/", include("routing.urls")),
    path("api/", include("servicepoints.urls")),
    # weather URLs are owned by C; emergency URLs by D.
    # They register their own urls.py when ready.
]

"""
Standalone URL configuration for the SafeHaul frontend project.
Wires the frontend app's URL patterns to the root.
"""
from django.urls import path, include

urlpatterns = [
    path('', include('frontend.urls')),
]

"""
SafeHaul Kerala — frontend URL patterns (Member B)

Include these in the main safehaul/urls.py once A's skeleton is ready:

    from django.urls import path, include
    urlpatterns = [
        ...
        path('', include('frontend.urls')),
    ]
"""
from django.urls import path
from . import views

app_name = 'frontend'

urlpatterns = [
    path('', views.map_view, name='map'),
]

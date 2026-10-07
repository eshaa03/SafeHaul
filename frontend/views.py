"""
SafeHaul Kerala — frontend views (Member B)

Serves the map page at / and provides the root URL conf so the
frontend app works as a standalone Django application while A's
backend skeleton is not yet merged to main.

A will incorporate these into the main safehaul/urls.py when
backend/safehaul/ is set up. Until then, this file doubles as the
project-level url conf (see frontend_project/urls.py and settings.py).
"""
from django.shortcuts import render


def map_view(request):
    """Serve the main Leaflet map page."""
    return render(request, 'safehaul/map.html')

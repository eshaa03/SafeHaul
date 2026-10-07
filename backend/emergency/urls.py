from django.urls import path
from . import views

# API routes — mounted at /api/ by the root urlconf.
# Matches TEAM_BRIEF §1.10 exactly:
#   POST /api/emergency/          → create
#   GET  /api/emergency/?since=   → list
#   POST /api/emergency/<id>/ack/ → acknowledge
urlpatterns = [
    path("emergency/", views.emergency_endpoint, name="emergency"),
    path("emergency/<int:event_id>/ack/", views.emergency_ack, name="emergency-ack"),
]

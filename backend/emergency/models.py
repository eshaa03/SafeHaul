from django.db import models

VALID_CODES = ["01", "02", "03", "04", "05", "06", "07"]

VIA_CHOICES = [
    ("lora", "LoRa radio"),
    ("app", "Mobile app"),
    ("sms", "SMS"),
    ("sim", "Simulated radio link"),
]

STATUS_CHOICES = [
    ("new", "New"),
    ("acked", "Acknowledged"),
]


class EmergencyEvent(models.Model):
    """
    One emergency signal received from a truck device (real or simulated).

    Duplicate packets (same vehicle_id + seq) are suppressed at the API layer
    via get_or_create on the (vehicle_id, seq) unique constraint.

    Every field maps 1-to-1 to the contract in TEAM_BRIEF §1.10.
    """

    code = models.CharField(max_length=2)
    vehicle_id = models.PositiveIntegerField()
    seq = models.PositiveSmallIntegerField()
    lat = models.FloatField()
    lng = models.FloatField()
    device_ts = models.DateTimeField()
    received_at = models.DateTimeField(auto_now_add=True)
    via = models.CharField(max_length=10, choices=VIA_CHOICES, default="lora")
    station_id = models.PositiveSmallIntegerField(default=1)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="new")
    acked_by = models.CharField(max_length=100, blank=True, default="")
    acked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        # Duplicate suppression: same truck + same sequence number = same event.
        unique_together = [("vehicle_id", "seq")]
        ordering = ["-received_at"]

    def __str__(self):
        return (
            f"EmergencyEvent #{self.pk} code={self.code} "
            f"vehicle={self.vehicle_id} seq={self.seq} status={self.status}"
        )

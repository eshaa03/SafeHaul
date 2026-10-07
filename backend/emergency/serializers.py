from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
from .models import EmergencyEvent, VALID_CODES


class EmergencyEventSerializer(serializers.ModelSerializer):
    """Read serializer — used by GET /api/emergency/ and the station dashboard."""

    class Meta:
        model = EmergencyEvent
        fields = [
            "id",
            "code",
            "vehicle_id",
            "seq",
            "lat",
            "lng",
            "device_ts",
            "received_at",
            "via",
            "station_id",
            "status",
            "acked_by",
            "acked_at",
        ]


class EmergencyEventCreateSerializer(serializers.ModelSerializer):
    """
    Write serializer — used by POST /api/emergency/.
    Validates that code is one of the seven defined values.
    Duplicate suppression (same vehicle_id + seq) is handled in the view via
    get_or_create, so UniqueTogetherValidator is intentionally excluded here.
    """

    code = serializers.CharField(max_length=2)

    def validate_code(self, value):
        if value not in VALID_CODES:
            raise serializers.ValidationError(
                f"Invalid code '{value}'. Must be one of: {', '.join(VALID_CODES)}."
            )
        return value

    class Meta:
        model = EmergencyEvent
        fields = [
            "code",
            "vehicle_id",
            "seq",
            "lat",
            "lng",
            "device_ts",
            "via",
            "station_id",
        ]
        # DRF auto-adds a UniqueTogetherValidator for the (vehicle_id, seq)
        # unique_together constraint, which would reject duplicates with 400.
        # We suppress it here and let the view use get_or_create instead,
        # so duplicates are silently accepted (same behaviour as real LoRa retry).
        validators = []

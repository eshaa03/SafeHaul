from django.apps import AppConfig


class SafehaulConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "safehaul"
    verbose_name = "SafeHaul Core"

    def ready(self):
        # Pre-load data files into memory at startup so every request is fast.
        from safehaul.data_loader import load_data
        load_data()

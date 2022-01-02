from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class DrillSuppersConfig(AppConfig):
    name = "hac_shop.drill_suppers"
    verbose_name = _("Drill Suppers")

    def ready(self):
        try:
            import hac_shop.drill_suppers.signals  # noqa F401
        except ImportError:
            pass

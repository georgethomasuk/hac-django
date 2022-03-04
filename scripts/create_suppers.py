from copy import copy
from hac_shop.drill_suppers.models import DrillNight
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta, MO, TU
from django.conf import settings

HAC_TIMEZONE = settings.HAC_TIMEZONE

today = datetime.now(tz=HAC_TIMEZONE)
last_monday = today + relativedelta(weekday=MO(-1))

for x in range(52 * 3):

    tuesday = last_monday + timedelta(weeks=x, days=1)
    wednesday = last_monday + timedelta(weeks=x, days=2)

    DrillNight.objects.get_or_create(
        date_time=copy(tuesday).replace(hour=21, minute=0, second=0),
        cut_off_time=copy(tuesday).replace(hour=18, minute=0, second=0)
    )

    DrillNight.objects.get_or_create(
        date_time=copy(wednesday).replace(hour=21, minute=0, second=0),
        cut_off_time=copy(wednesday).replace(hour=18, minute=0, second=0)
    )



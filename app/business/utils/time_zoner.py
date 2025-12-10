
from dataclasses import dataclass
from typing import Optional, Tuple
from datetime import datetime, date, time

import pytz
import settings
from core.custom_logger import logger


@dataclass
class TimeZonerResult:
    start: str
    end: str
    range: str


class TimeZoner:
    """Utility class to convert naive times stored in the project default timezone
    (``settings.TIME_ZONE``) to a user's timezone and format them.

    Assumptions:
    - ``start_time`` and ``end_time`` are naive ``datetime.time`` objects representing
      times in the default timezone.
    - ``booking_date`` is a naive ``datetime.date`` object (no TZ info) also in default TZ.
    - ``user_timezone`` is a string (e.g. "Europe/London"). If invalid or missing, the
      default timezone is used.

    Output format: "HH:MM AM/PM - HH:MM AM/PM" (12-hour clock) matching existing code.
    """

    @staticmethod
    def _get_tz(tz_name: Optional[str]) -> pytz.BaseTzInfo:
        if not tz_name:
            return pytz.timezone(settings.TIME_ZONE)
        try:
            return pytz.timezone(tz_name)
        except Exception:
            logger.warning(f"Invalid timezone '{tz_name}', falling back to default.")
            return pytz.timezone(settings.TIME_ZONE)

    @classmethod
    def convert_time_range(
        cls,
        booking_date: Optional[date],
        start_time: Optional[time],
        end_time: Optional[time],
        user_timezone: Optional[str],
    ) -> TimeZonerResult:
        """Convert a booking time range from default timezone to user's timezone.
        Returns empty strings if any input is missing.
        """
        logger.info(f"Converting time range for date {booking_date} from default TZ to user TZ {user_timezone}")
        if not (booking_date and start_time and end_time):
            empty = ""
            return TimeZonerResult(empty, empty, empty)

        default_tz = pytz.timezone(settings.TIME_ZONE)
        user_tz = cls._get_tz(user_timezone)

        # Combine date and times into naive datetimes and localize to default timezone.
        start_dt_default = default_tz.localize(datetime.combine(booking_date, start_time))
        end_dt_default = default_tz.localize(datetime.combine(booking_date, end_time))

        # Convert to user's timezone.
        start_dt_user = start_dt_default.astimezone(user_tz)
        end_dt_user = end_dt_default.astimezone(user_tz)

        start_str = start_dt_user.strftime('%I:%M %p')
        end_str = end_dt_user.strftime('%I:%M %p')
        range_str = f"{start_str} - {end_str}"

        logger.info(f"range_str: {range_str}")
        return TimeZonerResult(start=start_str, end=end_str, range=range_str)

    @classmethod
    def convert_date(
        cls,
        booking_date: Optional[date],
        reference_time: Optional[time],
        user_timezone: Optional[str],
        fmt: str = '%d/%m/%Y',
    ) -> str:
        """Convert a booking date from default timezone to user's timezone.

        If a ``reference_time`` is provided, we consider the localized datetime and
        then convert; this handles cases where crossing midnight in user's TZ could
        shift the date.
        """
        if not booking_date:
            return ""
        default_tz = pytz.timezone(settings.TIME_ZONE)
        user_tz = cls._get_tz(user_timezone)
        if reference_time is None:
            # Treat noon as neutral reference to avoid DST midnight edge issues.
            reference_time = time(12, 0, 0)
        dt_default = default_tz.localize(datetime.combine(booking_date, reference_time))
        dt_user = dt_default.astimezone(user_tz)
        return dt_user.strftime(fmt)


from django.db.models import IntegerChoices, TextChoices
from django.utils.translation import gettext_lazy as _


class RatingChoices(IntegerChoices):
    """
    Choices for the rating field.
    """
    EXCELLENT = 5, _("Excellent")
    VERY_GOOD = 4, _("Very Good")
    GOOD = 3, _("Good")
    FAIR = 2, _("Fair")
    POOR = 1, _("Poor")
    NEUTRAL = 0, _("Neutral")  # Neutral rating


class SortByChoices(TextChoices):
    """
    Choices for sorting ratings.
    """
    RATING_DESC = "-rating", _("Rating (High to Low)")
    RATING_ASC = "rating", _("Rating (Low to High)")

    CREATION_DATE_DESC = "-created_at", _("Creation Date (New to Old)")
    CREATION_DATE_ASC = "created_at", _("Creation Date (Old to New)")

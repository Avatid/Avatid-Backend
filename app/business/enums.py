from django.db.models import TextChoices
from django.utils.translation import gettext_lazy as _


class CurrencyChoices(TextChoices):

    """
    Enum representing the currency choices.
    """
    USD = "USD", _("US Dollar")
    EUR = "EUR", _("Euro")
    GBP = "GBP", _("British Pound")
    ALL = "ALL", _("Albanian Lek")
    
    @classmethod
    def get_currency_symbol(cls, currency_code):
        """
        Returns the symbol for a given currency code.
        """
        symbols = {
            cls.USD: "$",
            cls.EUR: "€",
            cls.GBP: "£",
            cls.ALL: "Lek",
        }
        return symbols.get(currency_code, "")


class BusinessSortByChoices(TextChoices):

    """
    Enum representing the sorting options for businesses.
    """
    RATING_DESC = "-average_rating", _("Rating (High to Low)")
    RATING_ASC = "average_rating", _("Rating (Low to High)")
    DISTANCE_DESC = "-distance_to", _("Distance (Far to Near)")
    DISTANCE_ASC = "distance_to", _("Distance (Near to Far)")
    CREATION_DATE_DESC = "-created_at", _("Creation Date (New to Old)")
    CREATION_DATE_ASC = "created_at", _("Creation Date (Old to New)")


class ServiceSortByChoices(TextChoices):
    RATING_DESC = "-average_rating", _("Rating (High to Low)")
    RATING_ASC = "average_rating", _("Rating (Low to High)")
    DISTANCE_DESC = "-distance_to", _("Distance (Far to Near)")
    DISTANCE_ASC = "distance_to", _("Distance (Near to Far)")
    CREATION_DATE_DESC = "-created_at", _("Creation Date (New to Old)")
    CREATION_DATE_ASC = "created_at", _("Creation Date (Old to New)")


class EmployeeSortByChoices(TextChoices):
    """
    Enum representing the sorting options for employees.
    """
    RATING_DESC = "-average_rating", _("Rating (High to Low)")
    RATING_ASC = "average_rating", _("Rating (Low to High)")
    FREE_HOURS_DESC = "-free_hours", _("free_hours (High to Low)")
    FREE_HOURS_ASC = "free_hours", _("free_hours (Low to High)")


class DayOfWeekChoices(TextChoices):
    """
    Enum representing the days of the week.
    """
    MONDAY = "monday", _("Monday")
    TUESDAY = "tuesday", _("Tuesday")
    WEDNESDAY = "wednesday", _("Wednesday")
    THURSDAY = "thursday", _("Thursday")
    FRIDAY = "friday", _("Friday")
    SATURDAY = "saturday", _("Saturday")
    SUNDAY = "sunday", _("Sunday")


class VisitTypeChoices(TextChoices):
    """
    Enum representing the visit types.
    """
    ON_SITE = "on_site", _("On Site")
    HOME_VISIT = "home_visit", _("Home Visit")


class BusinessTypeChoices(TextChoices):
    """
    Enum representing the business types.
    """
    BUSINESS = "business", _("Business")
    FREELANCE = "freelance", _("Freelance")


class SocialMediaChoices(TextChoices):
    """
    Enum representing the social media platforms.
    """
    FACEBOOK = "facebook", _("Facebook")
    INSTAGRAM = "instagram", _("Instagram")
    TWITTER = "twitter", _("Twitter")
    LINKEDIN = "linkedin", _("LinkedIn")
    YOUTUBE = "youtube", _("YouTube")
    WHATSAPP = "whatsapp", _("WhatsApp")
    TIKTOK = "tiktok", _("TikTok")


class BookingStatusChoices(TextChoices):
    """
    Enum representing the booking status.
    """
    PENDING = "pending", _("Pending")
    CONFIRMED = "confirmed", _("Confirmed")
    CANCELLED = "cancelled", _("Cancelled")
    COMPLETED = "completed", _("Completed")
    REJECTED = "rejected", _("Rejected")


class ApplyForWeeksChoices(TextChoices):
    """
    Enum representing the options for applying for weeks.
    """
    THIS_WEEK_ONLY = "this_week_only", _("This Week Only")
    THIS_WEEK_AND_NEXT = "this_week_and_next", _("This Week and Next")
    ALL_WEEKS = "all_weeks", _("All Weeks")


class OrderByChoices(TextChoices):
    """
    Enum representing the options for ordering.
    """
    NAME_ASC = "name", _("Name (A-Z)")
    NAME_DESC = "-name", _("Name (Z-A)")
    CREATION_DATE_ASC = "created_at", _("Oldest first")
    CREATION_DATE_DESC = "-created_at", _("Newest first")
    RATING_ASC = "average_rating", _("Lowest rating first")
    RATING_DESC = "-average_rating", _("Highest rating first")
    NON_RATED = "non_rated", _("Non-rated")
    RATED = "rated", _("Rated")
    CANCELLED = "cancelled", _("Cancelled")
    DATE_ASC = "date", _("Date (Oldest first)")
    DATE_DESC = "-date", _("Date (Newest first)")


class SearchDataTypeChoices(TextChoices):
    """
    Enum representing the data types for search.
    """
    BOOKING = "booking", _("Booking")
    EMPLOYEE = "employee", _("Employee")
    CLIENT = "client", _("Client")
    BUSINESS = "business", _("Business")
    SERVICE = "service", _("Service")
    ALL = "all", _("All")

    @classmethod
    def get_data_type(cls, model):
        """
        Returns the data type for a given model.
        """
        return cls.DATA_TYPE_MAP.get(model, None)
    

class ClientSortByChoices(TextChoices):
    """
    Enum representing the sorting options for clients.
    """
    BOOKING_COUNT_DESC = "-booking_count", _("Booking Count (High to Low)")
    BOOKING_COUNT_ASC = "booking_count", _("Booking Count (Low to High)")
    NAME_ASC = "user__name", _("Name (A-Z)")
    NAME_DESC = "-user__name", _("Name (Z-A)")
    CREATION_DATE_ASC = "created_at", _("Oldest first")
    CREATION_DATE_DESC = "-created_at", _("Newest first")


class ClientStatusChoices(TextChoices):
    """
    Enum representing the status of a client.
    """
    PENDING = "pending", _("Pending")
    ACCEPTED = "accepted", _("Accepted")
    REJECTED = "rejected", _("Rejected")


class ServiceTypeChoices(TextChoices):
    """
    Enum representing the service types.
    """
    HAIR = "hair", _("Hair")
    BODY = "body", _("Body")
    DOCTOR = "doctor", _("Doctor")
    MAKEUP = "makeup", _("Makeup")
    MASSAGE = "massage", _("Massage")
    NAILS = "nails", _("Nails")
    PHYSIOTHERAPIST = "physiotherapist", _("Physiotherapist")
    PERSONAL_TRAINER = "personal_trainer", _("Personal Trainer")


from uuid import uuid4

from django.contrib.gis.db import models
from django.apps import apps

from django.utils.translation import gettext_lazy as _
from core.models import safe_file_path
from core.validators import validate_file_size

from business import enums as business_enums
from onboarding import enums as onboarding_enums
from user.geo_utils.main import GeoUtils
from datetime import date, timedelta

from rating import models as rating_models
from business.utils.time_zoner import TimeZoner 


class ServiceCategory(models.Model):
    """
    Model representing a service category.
    """
    class Meta:
        verbose_name = _("Service Category")
        verbose_name_plural = _("Service Categories")
    
    uid = models.UUIDField(default=uuid4, editable=False, unique=True)
    name = models.CharField(max_length=255)
    service_type = models.CharField(
        max_length=255,
        choices=business_enums.ServiceTypeChoices.choices,
        default=business_enums.ServiceTypeChoices.HAIR,
        help_text=_("Type of service this category represents"),
    )
    logo = models.ImageField(
        upload_to=safe_file_path,
        null=True,
        default=None,
        blank=True,
        validators=[validate_file_size],
        verbose_name=_("Logo"),
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        related_name="subcategories",
        null=True,
        blank=True,
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
    )
    currency = models.CharField(
        max_length=3,
        choices=business_enums.CurrencyChoices.choices,
        default=business_enums.CurrencyChoices.GBP,
        null=True,
        blank=True,
    )
    duration = models.DurationField(
        null=True,
        blank=True,
        help_text=_("Duration of the service in HH:MM:SS format"),
    )
    description = models.TextField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def currency_symbol(self):
        """
        Returns the symbol for the currency of the service category.
        """
        return business_enums.CurrencyChoices.get_currency_symbol(self.currency)
    
    @property
    def subcategories_count(self):
        """
        Returns the count of subcategories under this service category.
        """
        return self.subcategories.count()

    def __str__(self):
        return f"{self.uid} - {self.name}"


class WorkingHours(models.Model):
    """
    Model representing working hours.
    """
    uid = models.UUIDField(default=uuid4, editable=False, unique=True)
    visit_type = models.CharField(
        max_length=255,
        choices=business_enums.VisitTypeChoices.choices,
        null=True,
        blank=True,
    )
    start_time = models.TimeField()
    end_time = models.TimeField()
    day_of_week = models.CharField(
        max_length=9,
        choices=business_enums.DayOfWeekChoices.choices,
        default=business_enums.DayOfWeekChoices.MONDAY,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.day_of_week}: {self.start_time} - {self.end_time}"


class SocialMedia(models.Model):

    """
    Model representing a social media account.
    """
    class Meta:
        verbose_name = _("Social Media")
        verbose_name_plural = _("Social Media")
    
    uid = models.UUIDField(default=uuid4, editable=False, unique=True)
    platform = models.CharField(
        max_length=255,
        choices=business_enums.SocialMediaChoices.choices,
        default=business_enums.SocialMediaChoices.FACEBOOK,
        null=True,
        blank=True,
    )
    name = models.CharField(max_length=255, blank=True, null=True)
    url = models.URLField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.uid} - {self.name} - {self.platform}"


class Gallery(models.Model):
    """
    Model representing a gallery.
    """
    class Meta:
        verbose_name = _("Gallery")
        verbose_name_plural = _("Galleries")
    
    uid = models.UUIDField(default=uuid4, editable=False, unique=True)
    name = models.CharField(max_length=255)
    image = models.ImageField(
        upload_to=safe_file_path,
        null=True,
        default=None,
        blank=True,
        validators=[validate_file_size],
        verbose_name=_("Image"),
    )
    is_main = models.BooleanField(
        default=False,
        help_text=_("Is this image the main image for the business?"),
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.uid} - {self.name}"
    

class VideoGallery(models.Model):
    """
    Model representing a video gallery.
    """
    class Meta:
        verbose_name = _("Video Gallery")
        verbose_name_plural = _("Video Galleries")
    
    uid = models.UUIDField(default=uuid4, editable=False, unique=True)
    name = models.CharField(max_length=255)
    video = models.FileField(
        upload_to=safe_file_path,
        null=True,
        default=None,
        blank=True,
        validators=[validate_file_size],
        verbose_name=_("Video"),
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.uid} - {self.name}"


# employees and services
class Service(models.Model):
    """
    Model representing a service.
    """
    class Meta:
        verbose_name = _("Service")
        verbose_name_plural = _("Services")
    
    uid = models.UUIDField(default=uuid4, editable=False, unique=True)
    name = models.CharField(max_length=255, null=True, blank=True)
    image = models.ImageField(
        upload_to=safe_file_path,
        null=True,
        default=None,
        blank=True,
        validators=[validate_file_size],
        verbose_name=_("Image"),
    )
    gender = models.CharField(
        max_length=255,
        choices=onboarding_enums.ServiceGenderChoices.choices,
        default=onboarding_enums.ServiceGenderChoices.OTHER,
        null=True,
        blank=True,
    )
    business = models.ForeignKey(
        "business.Business",
        on_delete=models.CASCADE,
        related_name="services",
    )
    duration = models.DurationField(null=True, blank=True, help_text=_("Duration of the service in HH:MM:SS format"))
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    currency = models.CharField(
        max_length=3,
        choices=business_enums.CurrencyChoices.choices,
        default=business_enums.CurrencyChoices.USD,
        null=True,
        blank=True,
    )
    category = models.ForeignKey(
        "business.ServiceCategory",
        on_delete=models.CASCADE,
        related_name="services",
        null=True,
        blank=True,
    )
    categories = models.ManyToManyField(
        "business.ServiceCategory",
        related_name="services_categories",
        blank=True,
    )
    images = models.ManyToManyField(
        Gallery,
        related_name="services",
        blank=True,
    )
    working_hours = models.ManyToManyField(
        WorkingHours,
        related_name="services",
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.uid}"
    
    @property
    def currency_symbol(self):
        """
        Returns the symbol for the currency of the service category.
        """
        return business_enums.CurrencyChoices.get_currency_symbol(self.currency)


class Employee(models.Model):

    """
    Model representing an employee.
    """
    class Meta:
        verbose_name = _("Employee")
        verbose_name_plural = _("Employees")
    
    uid = models.UUIDField(default=uuid4, editable=False, unique=True)
    user = models.ForeignKey(
        "user.User",
        on_delete=models.CASCADE,
        related_name="employees",
        null=True,
        blank=True,
    )
    business = models.ForeignKey(
        "business.Business",
        on_delete=models.CASCADE,
        related_name="employees",
    )
    name = models.CharField(max_length=255)
    avatar = models.ImageField(
        upload_to=safe_file_path,
        null=True,
        default=None,
        blank=True,
        validators=[validate_file_size],
        verbose_name=_("Avatar"),
    )
    services = models.ManyToManyField(
        "business.Service",
        related_name="employees_services",
        blank=True,
    )
    working_hours = models.ManyToManyField(
        WorkingHours,
        related_name="employees",
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.uid} - {self.name}"


class Business(models.Model):
    """
    Model representing a business.
    """
    class Meta:
        verbose_name = _("Business")
        verbose_name_plural = _("Businesses")

    uid = models.UUIDField(default=uuid4, editable=False, unique=True)
    user = models.ForeignKey(
        "user.User",
        on_delete=models.CASCADE,
        related_name="business",
    )
    business_type = models.CharField(
        max_length=255,
        choices=business_enums.BusinessTypeChoices.choices,
        default=business_enums.BusinessTypeChoices.BUSINESS,
        null=True,
        blank=True,
    )
    name = models.CharField(max_length=255, null=True, blank=True)
    surname = models.CharField(max_length=255, null=True, blank=True)

    store_name = models.CharField(max_length=255, null=True, blank=True)
    
    address = models.CharField(max_length=255, null=True, blank=True)
    location = models.PointField(
        verbose_name=_("Location"),
        blank=True,
        null=True,
    )
    
    collaboration_address = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text=_("Address for collaboration with other businesses"),
    )
    collaboration_location = models.PointField(
        verbose_name=_("Collaboration Location"),
        blank=True,
        null=True,
    )

    collaboration_address_on = models.BooleanField(
        default=False,
        help_text=_("Is collaboration address enabled?"),
    )
    address_on = models.BooleanField(
        default=True,
        help_text=_("Is address enabled?"),
    )

    longitude = models.FloatField(null=True, blank=True)
    latitude = models.FloatField(null=True, blank=True)

    bio = models.TextField(null=True, blank=True)
    working_hours = models.ManyToManyField(
        WorkingHours,
        related_name="businesses",
        blank=True,
    )
    breaking_hours = models.ManyToManyField(
        WorkingHours,
        related_name="businesses_breaking_hours",
        blank=True,
    )
    visit_type = models.CharField(
        max_length=255,
        choices=business_enums.VisitTypeChoices.choices,
        null=True,
        blank=True,
    )
    category = models.ForeignKey(
        "business.ServiceCategory",
        on_delete=models.CASCADE,
        related_name="businesses",
    )
    categories = models.ManyToManyField(
        "business.ServiceCategory",
        related_name="businesses_categories",
        blank=True,
    )
    images = models.ManyToManyField(
        Gallery,
        related_name="businesses",
        blank=True,
    )
    videos = models.ManyToManyField(
        VideoGallery,
        related_name="businesses",
        blank=True,
    )

    note_to_clients = models.TextField(null=True, blank=True)
    collaborated_business = models.TextField(
        null=True,
        blank=True,
    )
    contact_number = models.CharField(max_length=255, null=True, blank=True)
    contact_email = models.EmailField(null=True, blank=True)
    socials = models.ManyToManyField(
        SocialMedia,
        related_name="businesses",
        blank=True,
    )
    time_step = models.DurationField(
        null=True,
        blank=True,
        help_text=_("Time step for bookings in HH:MM:SS format"),
    )
    apply_for_weeks = models.CharField(
        choices=business_enums.ApplyForWeeksChoices.choices,
        max_length=255,
        default=business_enums.ApplyForWeeksChoices.ALL_WEEKS,
        null=True,
        blank=True,
    )
    apply_for_weeks_date = models.DateField(
        null=True,
        blank=True,
        help_text=_("Specific date to apply the 'apply for weeks' setting from"),
    )
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.uid} - {self.name}"

    @property
    def get_real_working_hours(self):
        """
        Returns the working hours of the business excluding breaking hours.
        based on the apply_for_weeks setting and apply_for_weeks_date and current date.
        eg: 
        - if apply_for_weeks is THIS_WEEK_ONLY, and today is in the same week as apply_for_weeks_date,
        return working hours as they are.
        - if apply_for_weeks is THIS_WEEK_AND_NEXT, and today is bigger than apply_for_weeks_date
        return working hours as they are.
        - if apply_for_weeks is ALL_WEEKS, return working hours as they are.
        - else, return empty queryset.
        """
        if not self.apply_for_weeks_date:
            return self.working_hours.all()

        today = date.today()
        start_of_week = self.apply_for_weeks_date - timedelta(days=today.weekday())
        end_of_week = start_of_week + timedelta(days=6)

        week_windows = {
            business_enums.ApplyForWeeksChoices.THIS_WEEK_ONLY: end_of_week,
            business_enums.ApplyForWeeksChoices.THIS_WEEK_AND_NEXT: end_of_week + timedelta(days=7),
        }

        if self.apply_for_weeks == business_enums.ApplyForWeeksChoices.ALL_WEEKS:
            return self.working_hours.all()

        window_end = week_windows.get(self.apply_for_weeks)
        if window_end and start_of_week <= today <= window_end:
            return self.working_hours.all()

        return WorkingHours.objects.none()


    @property
    def main_image(self):
        """
        Returns the main image of the business if it exists.
        """
        image = self.images.filter(is_main=True).first()
        if not image:
            return self.images.all().order_by('created_at').first()
        return image
    
    @property
    def main_image_url(self):
        """
        Returns the URL of the main image of the business if it exists.
        """
        main_image = self.main_image
        return main_image.image.url if main_image and main_image.image else ""
    
    def save(self, *args, **kwargs):
        if self.location and not self.longitude and not self.latitude:
            self.longitude, self.latitude = GeoUtils.point_to_coordinates(self.location)
        elif self.longitude and self.latitude and not self.location:
            self.location = GeoUtils.coordinates_to_point(self.longitude, self.latitude)
        super().save(*args, **kwargs)
        notification_settings = BusinessNotificationSenderSettings.objects.filter(
            business=self,
        ).first()
        if not notification_settings:
            BusinessNotificationSenderSettings.objects.create(
                business=self,
            )
    

class UserBusinesBooking(models.Model):
    """
    Model representing a booking made by a user for a business.
    """
    uid = models.UUIDField(default=uuid4, editable=False, unique=True)
    user = models.ForeignKey(
        "user.User",
        on_delete=models.CASCADE,
        related_name="user_bookings",
    )
    business = models.ForeignKey(
        "business.Business",
        on_delete=models.CASCADE,
        related_name="business_bookings",
    )
    employee = models.ForeignKey(
        "business.Employee",
        on_delete=models.CASCADE,
        related_name="employee_bookings",
        null=True,
        blank=True,
    )
    services = models.ManyToManyField(
        "business.Service",
        related_name="service_bookings",
        blank=True,
    )
    categories = models.ManyToManyField(
        "business.ServiceCategory",
        related_name="category_bookings",
        blank=True,
    )
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    day_of_week = models.CharField(
        max_length=9,
        choices=business_enums.DayOfWeekChoices.choices,
        default=business_enums.DayOfWeekChoices.MONDAY,
    )
    date = models.DateField(
        null=True,
        blank=True,
    )

    visit_type = models.CharField(
        max_length=255,
        choices=business_enums.VisitTypeChoices.choices,
        null=True,
        blank=True,
    )
    status = models.CharField(
        max_length=255,
        choices=business_enums.BookingStatusChoices.choices,
        default=business_enums.BookingStatusChoices.PENDING,
    )
    cancel_reason = models.TextField(
        null=True,
        blank=True,
        help_text=_("Reason for cancellation if the booking is cancelled"),
    )

    was_user_reminded = models.BooleanField(default=False, help_text=_("Was remind notification sent to user"))
    was_user_reminded_daily = models.BooleanField(
        default=False,
        help_text=_("Was daily remind notification sent to user"),
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user} - {self.business} ({self.start_time} - {self.end_time})"

    @property
    def date_str(self) -> str:
        user_timezone = getattr(self.user, 'timezone', None) if hasattr(self, 'user') else None
        return TimeZoner.convert_date(
            booking_date=self.date,
            reference_time=self.start_time,
            user_timezone=user_timezone,
        )
    
    @property
    def time_str(self) -> str:
        user_timezone = None
        try:
            user_timezone = getattr(self.user, 'timezone', None)
        except Exception:
            user_timezone = None
        result = TimeZoner.convert_time_range(
            booking_date=self.date,
            start_time=self.start_time,
            end_time=self.end_time,
            user_timezone=user_timezone,
        )
        return result.range
    
    @property
    def start_time_str(self) -> str:
        if not self.start_time or not self.date:
            return ""
        user_timezone = getattr(self.user, 'timezone', None) if hasattr(self, 'user') else None
        result = TimeZoner.convert_time_range(
            booking_date=self.date,
            start_time=self.start_time,
            end_time=self.start_time,
            user_timezone=user_timezone,
        )
        return result.start

    @property
    def price(self):
        return sum(service.price for service in self.services.all())
    
    @property
    def currency(self):
        return self.services.first().currency if self.services.exists() else ""
    
    def update_or_create_client(self):
        return BusinessClient.objects.update_or_create(
            user=self.user,
            business=self.business,
        )
    
    @classmethod
    def get_annotated_queryset(cls, user):
        """
        Returns a queryset annotated with the price and currency of the first service.
            - rating_count: number of ratings for the booking
            - business_rating_count: number of ratings for the business
            - is_booking_rated : whether the booking has been rated by the user
            - is_business_rated : whether the business has been rated by the user
        """
        queryset = cls.objects.annotate(
            rating_count=models.Count("ratings", distinct=True),
            business_rating_count=models.Count("business__ratings", distinct=True),
        )
        if user and not user.is_anonymous:
            queryset = queryset.annotate(
                is_booking_rated=models.Exists(
                    rating_models.Rating.objects.filter(
                        user=user,
                        booking=models.OuterRef("pk"),
                    )
                ),
                is_business_rated=models.Exists(
                    rating_models.Rating.objects.filter(
                        user=user,
                        business=models.OuterRef("business_id"),
                    )
                ),
            )
        else:
            queryset = queryset.annotate(
                is_booking_rated=models.Value(False, output_field=models.BooleanField()),
                is_business_rated=models.Value(False, output_field=models.BooleanField()),
            )
        return queryset

class BusinessClient(models.Model):

    uid = models.UUIDField(default=uuid4, editable=False, unique=True)
    user = models.ForeignKey(
        "user.User",
        on_delete=models.CASCADE,
        related_name="business_clients",
    )
    business = models.ForeignKey(
        "business.Business",
        on_delete=models.CASCADE,
        related_name="business_clients",
        null=True,
        blank=True,
    )
    bio = models.TextField(null=True, blank=True)
    status = models.CharField(
        max_length=255,
        choices=business_enums.ClientStatusChoices.choices,
        default=business_enums.ClientStatusChoices.PENDING,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user} - {self.business} - {self.bio}"


class BusinessNotificationSenderSettings(models.Model):
    """
    Model representing the settings for sending notifications to businesses.
    """
    class Meta:
        verbose_name = _("Business Notification Settings")
        verbose_name_plural = _("Business Notification Settings")

    uid = models.UUIDField(default=uuid4, editable=False, unique=True)
    business = models.OneToOneField(
        "business.Business",
        on_delete=models.CASCADE,
        related_name="notification_settings",
    )
    email_notifications = models.BooleanField(default=True)
    push_notifications = models.BooleanField(default=True)

    booking_email = models.BooleanField(default=True, help_text=_("Send Booking email to costumers"))
    booking_notification = models.BooleanField(default=True, help_text=_("Send Booking notification to costumers"))

    reminder_email = models.BooleanField(default=True, help_text=_("Send Reminder email to costumers"))
    reminder_notification = models.BooleanField(default=True, help_text=_("Send Reminder notification to costumers"))

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.business} - {self.email_notifications} - {self.push_notifications}"
from django.contrib.auth.base_user import BaseUserManager, AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.contrib.gis.db import models
from django.utils.translation import gettext_lazy as _
from uuid import uuid4

from core import exception
from core.models import safe_file_path
from core.validators import validate_file_size, email_validator, phone_validator
from user.social_mapper import UserSocialInfoMapper

from notifications.firebase_client import FireBaseClient
from user import enums
from onboarding import models as onboarding_models
from business import models as business_models


class UserManager(BaseUserManager):
    """User manager class for creating users and superusers"""

    def create_user(
        self, email: str, password: str = None, **extra_fields: dict
    ) -> "User":
        """
        Creates and saves new user
        :param email: user email
        :param password: user password
        :param extra_fields: additional parameters
        :return: created user model
        """
        if not email:
            raise exception.get(ValueError, "User must have email address")
        user = self.model(email=self.normalize_email(email), **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email: str, password: str) -> "User":
        """
        Creates and saves new super user
        :param email: user email
        :param password: user password
        :return: created user model
        """
        user = self.create_user(email, password)
        user.is_staff = True
        user.is_superuser = True
        user.save()
        return user


class User(AbstractBaseUser, PermissionsMixin):
    uid = models.UUIDField(unique=True, default=uuid4, editable=False)
    send_push_notifications = models.BooleanField(
        default=True,
        verbose_name=_("Send push notifications"),
    )
    send_email_notification = models.BooleanField(
        default=True,
        verbose_name=_("Send email notifications"),
    )
    notification_settings = models.OneToOneField(
        "user.UserNotificationSettings",
        on_delete=models.CASCADE,
        verbose_name=_("Notification settings"),
        null=True,
        blank=True,
    )
    email = models.EmailField(
        max_length=255,
        unique=True,
        error_messages={"unique": "email_already_used"},
        verbose_name=_("Email"),
        validators=[email_validator],
        null=True,
        blank=True,
    )
    phone = models.CharField(
        max_length=255,
        verbose_name=_("Phone"),
        null=True,
        blank=True,
        validators=[phone_validator],
        unique=True,
        error_messages={"unique": "phone_already_used"},
    )
    is_phone_verified = models.BooleanField(
        default=False,
        verbose_name=_("Is phone verified?"),
    )
    name = models.CharField(default="", max_length=64, verbose_name=_("Name"))
    surname = models.CharField(default="", max_length=64, verbose_name=_("Surname"))
    avatar = models.ImageField(
        upload_to=safe_file_path,
        null=True,
        default=None,
        blank=True,
        validators=[validate_file_size],
        verbose_name=_("Avatar"),
    )
    avatar_id = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name=_("Avatar ID"),
    )
    created_at = models.DateTimeField(
        auto_now_add=True, editable=False, verbose_name=_("Created at")
    )
    is_email_verified = models.BooleanField(
        default=False, verbose_name=_("Is email verified?")
    )
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(
        default=False,
        verbose_name=_("Is staff?"),
        help_text=_("Use this option for create Staff"),
    )
    current_location = models.PointField(
        verbose_name=_("Current location"),
        blank=True,
        null=True,
    )
    chosen_role = models.CharField(
        max_length=64,
        choices=enums.UserRoleChoices.choices,
        default=None,
        verbose_name=_("Chosen role"),
        null=True,
        blank=True,
    )
    timezone = models.CharField(
        max_length=64,
        default="Europe/London",
        verbose_name=_("Timezone"),
    )
    lang_code = models.CharField(
        max_length=8,
        default="en",
        verbose_name=_("Language code"),
    )

    objects = UserManager()
    USERNAME_FIELD = "email"

    @property
    def first_business(self) -> business_models.Business:
        """
        Returns the first business associated with the user.
        :return: Business instance or None if no business is found.
        """
        try:
            return business_models.Business.objects.filter(user=self).first()
        except business_models.Business.DoesNotExist:
            return None
    
    @property
    def get_firebase_token(self) -> str:
        return FireBaseClient.create_custom_token(self.uid)
    
    @property
    def get_social_info(self) -> dict:
        return UserSocialInfoMapper.get_social_info(self)
    
    @property
    def user_role(self) -> str:
        if onboarding_models.FreeLancer.objects.filter(user=self).exists():
            return enums.UserRoleChoices.FREELANCER.value
        if business_models.Business.objects.filter(user=self).exists():
            return enums.UserRoleChoices.BUSINESS.value
        if onboarding_models.Costumer.objects.filter(user=self).exists():
            return enums.UserRoleChoices.COSTUMER.value
        return None

    def __str__(self) -> str:
        return f"{self.email}"
    
    @property
    def username(self) -> str:
        """
        Returns the username (email) for compatibility with Django admin templates.
        This is needed for Unfold admin compatibility.
        """
        return self.email
    
    def save(self, *args, **kwargs):
        if self.email:
            self.email = self.email.lower()
        if not self.notification_settings:
            self.notification_settings = UserNotificationSettings.objects.create()
        super(User, self).save(*args, **kwargs)
    

class UserNotificationSettings(models.Model):
    updates_and_promotions_email = models.BooleanField(
        default=True,
        verbose_name=_("Get Updated and promotions email"),
    )
    updates_and_promotions_notification = models.BooleanField(
        default=True,
        verbose_name=_("GEt Updated and promotions notification"),
    )
    booking_email = models.BooleanField(
        default=True,
        verbose_name=_("Get booking email"),
    )
    booking_notification = models.BooleanField(
        default=True,
        verbose_name=_("Get booking notification"),
    )
    booking_cancellation_email = models.BooleanField(
        default=True,
        verbose_name=_("Get booking cancellation email"),
    )
    booking_cancellation_notification = models.BooleanField(
        default=True,
        verbose_name=_("Get booking cancellation notification"),
    )
    reminder_email = models.BooleanField(
        default=True,
        verbose_name=_("Get reminder email"),
    )
    reminder_notification = models.BooleanField(
        default=True,
        verbose_name=_("Get reminder notification"),
    )

    apply_notification = models.BooleanField(
        default=True,
        verbose_name=_("Apply to business notification"),
    )
    apply_notification_email = models.BooleanField(
        default=True,
        verbose_name=_("Apply to business email"),
    )
    apply_response_notification = models.BooleanField(
        default=True,
        verbose_name=_("Apply response to business notification"),
    )
    apply_response_notification_email = models.BooleanField(
        default=True,
        verbose_name=_("Apply response to business email"),
    )


class UserPushToken(models.Model):
    user = models.ForeignKey(
        "user.User",
        on_delete=models.CASCADE,
        related_name="push_tokens",
    )
    push_id = models.CharField(
        max_length=255,
        unique=True,
        blank=False,
        null=False,
        verbose_name=_("Push notification id"),
    )

    def __new__(cls, *args, **kwargs):
        """
        Use like this:
        UserPushToken(user=User(1), push_id='Some string')
        """
        instance = super().__new__(cls)
        for item in kwargs.keys():
            if hasattr(instance, item):
                setattr(instance, item, kwargs.get(item))
        return instance
    

class UserDevice(models.Model):
    user = models.ForeignKey(
        "user.User",
        on_delete=models.CASCADE,
        related_name="devices",
    )
    device_id = models.CharField(
        max_length=255,
        blank=False,
        null=False,
        verbose_name=_("Device ID"),
    )
    is_blacklisted = models.BooleanField(
        default=False,
        verbose_name=_("Is blacklisted?"),
        help_text=_("Indicates if the device is blacklisted"),
    )


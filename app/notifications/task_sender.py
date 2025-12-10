from celery import current_app as celery_app
from typing import List

from notifications.fire_push import PushSchema
from notifications.enums import NotificationType

from core.custom_logger import logger

from user.models import User
from business import models as business_models
from onboarding import models as onboarding_models


class NotificationTaskSender:
    """
    NotificationTaskSender
    - Send notifications using celery tasks
    - methods:
        - send: send a push notification
        - get_user_push_ids: get push ids of users that have push notifications enabled
    """
    

    @staticmethod
    def _localized_text(lang_owner, text_en: str, text_sq: str) -> str:
        lang_code = getattr(lang_owner, 'lang_code', lang_owner)
        lang_code = (lang_code or '').lower()
        return text_sq if lang_code == 'sq' else text_en

    # ------------- MAIN SENDERS -------------
    @classmethod
    def send(cls, notification: PushSchema):
        celery_app.send_task(
            'send_fire_push',
            kwargs={
                'fire_push_schema': notification.model_dump()
            }
        )

    # --------------- UTILS ----------------
    @classmethod
    def get_user_push_ids(cls, users_ids=None, filter_kwargs={}, is_costum_notification=False) -> List[str]:
        """
        Get push ids of users that have push notifications enabled. based on the filter_kwargs.
        """
        
        if not users_ids and not is_costum_notification:
            users_ids = User.objects.all().values_list('id', flat=True)
        push_ids = list(User.objects.filter(
            id__in=users_ids,
            send_push_notifications=True,
            **filter_kwargs
        ).values_list('push_tokens__push_id', flat=True))
        push_ids = list(set([push_id for push_id in push_ids if push_id]))
        logger.info(f"Push ids: {push_ids}")
        return push_ids

    # ------------- NOTIFICATION SENDERS -------------

    @classmethod
    def send_booking_notification(cls, booking: business_models.UserBusinesBooking):
        """
        Send booking notification to the user and the business owner
        """
        filter_kwargs = {
            'notification_settings__booking_notification': True,
        }
        user_push_ids = cls.get_user_push_ids(users_ids=[booking.user.id], filter_kwargs=filter_kwargs)
        business_push_ids = cls.get_user_push_ids(users_ids=[booking.business.user.id], filter_kwargs=filter_kwargs)
        
        title_en = "Booking Created"
        title_sq = "Rezervimi u krijua"
        body_en = f"Your booking for {booking.business.name} has been confirmed." if not booking.employee else f"Your booking with {booking.employee.name} has been confirmed."
        body_sq = f"Rezervimi juaj për {booking.business.name} është konfirmuar." if not booking.employee else f"Rezervimi juaj me {booking.employee.name} është konfirmuar."
        body = cls._localized_text(booking.user, body_en, body_sq)
        title = cls._localized_text(booking.user, title_en, title_sq)

        if user_push_ids:
            notification = PushSchema(
                title=title,
                body=body,
                push_id=user_push_ids,
                data={
                    'type': NotificationType.BOOKING_CREATED.value,
                    'booking_uid': str(booking.uid),
                    'business_uid': str(booking.business.uid),
                    'user_uid': str(booking.user.uid),
                },
            )

            cls.send(notification)

        body_en = f"You have a new booking for {booking.business.name} with {booking.user.name}."
        body_sq = f"Keni një rezervim të ri për {booking.business.name} me {booking.user.name}."
        body = cls._localized_text(booking.business.user, body_en, body_sq)
        title = cls._localized_text(booking.business.user, title_en, title_sq)

        if business_push_ids:
            notification = PushSchema(
                title=title,
                body=body,
                push_id=business_push_ids,
                data={
                    'type': NotificationType.BOOKING_CREATED.value,
                    'booking_uid': str(booking.uid),
                    'business_uid': str(booking.business.uid),
                    'user_uid': str(booking.user.uid),
                },
            )

            cls.send(notification)
    
    @classmethod
    def send_booking_cancellation_notification(cls, booking: business_models.UserBusinesBooking):
        """
        Send booking cancellation notification to the user and the business owner
        """
        filter_kwargs = {
            'notification_settings__booking_cancellation_notification': True,
        }
        user_push_ids = cls.get_user_push_ids(users_ids=[booking.user.id], filter_kwargs=filter_kwargs)
        business_push_ids = cls.get_user_push_ids(users_ids=[booking.business.user.id], filter_kwargs=filter_kwargs)

        title_en = "Booking Cancelled"
        title_sq = "Rezervimi u anullua"
        user_body_en = f"Your booking for {booking.business.name} has been cancelled." if not booking.employee else f"Your booking with {booking.employee.name} has been cancelled."
        user_body_sq = f"Rezervimi juaj për {booking.business.name} është anuluar." if not booking.employee else f"Rezervimi juaj me {booking.employee.name} është anuluar."
        business_body_en = f"The booking with {booking.user.name} has been cancelled."
        business_body_sq = f"Rezervimi me {booking.user.name} është anuluar."

        if user_push_ids:
            notification = PushSchema(
                title=cls._localized_text(booking.user, title_en, title_sq),
                body=cls._localized_text(booking.user, user_body_en, user_body_sq),
                push_id=user_push_ids,
                data={
                    'type': NotificationType.BOOKING_CANCELLED.value,
                    'booking_uid': str(booking.uid),
                    'business_uid': str(booking.business.uid),
                    'user_uid': str(booking.user.uid),
                },
            )
            cls.send(notification)

        if business_push_ids:
            notification = PushSchema(
                title=cls._localized_text(booking.business.user, title_en, title_sq),
                body=cls._localized_text(booking.business.user, business_body_en, business_body_sq),
                push_id=business_push_ids,
                data={
                    'type': NotificationType.BOOKING_CANCELLED.value,
                    'booking_uid': str(booking.uid),
                    'business_uid': str(booking.business.uid),
                    'user_uid': str(booking.user.uid),
                },
            )
            cls.send(notification)
    
    @classmethod
    def send_booking_updated_notification(cls, booking: business_models.UserBusinesBooking):
        """
        Send booking updated notification to the user and the business owner
        """
        # Get the push ids of the user and the business owner
        filter_kwargs = {
            'notification_settings__booking_notification': True,
        }
        user_push_ids = cls.get_user_push_ids(users_ids=[booking.user.id], filter_kwargs=filter_kwargs)
        business_push_ids = cls.get_user_push_ids(users_ids=[booking.business.user.id], filter_kwargs=filter_kwargs)

        title_en = "Booking Updated"
        title_sq = "Rezervimi u përditësua"
        user_body_en = (
            f"Your booking for {booking.business.name} has been updated."
            if not booking.employee
            else f"Your booking with {booking.employee.name} has been updated."
        )
        user_body_sq = (
            f"Rezervimi juaj për {booking.business.name} është përditësuar."
            if not booking.employee
            else f"Rezervimi juaj me {booking.employee.name} është përditësuar."
        )
        business_body_en = f"The booking with {booking.user.name} has been updated."
        business_body_sq = f"Rezervimi me {booking.user.name} është përditësuar."

        if user_push_ids:
            notification = PushSchema(
                title=cls._localized_text(booking.user, title_en, title_sq),
                body=cls._localized_text(booking.user, user_body_en, user_body_sq),
                push_id=user_push_ids,
                data={
                    'type': NotificationType.BOOKING_UPDATED.value,
                    'booking_uid': str(booking.uid),
                    'business_uid': str(booking.business.uid),
                    'user_uid': str(booking.user.uid),
                },
            )
            cls.send(notification)

        if business_push_ids:
            notification = PushSchema(
                title=cls._localized_text(booking.business.user, title_en, title_sq),
                body=cls._localized_text(booking.business.user, business_body_en, business_body_sq),
                push_id=business_push_ids,
                data={
                    'type': NotificationType.BOOKING_UPDATED.value,
                    'booking_uid': str(booking.uid),
                    'business_uid': str(booking.business.uid),
                    'user_uid': str(booking.user.uid),
                },
            )
            cls.send(notification)

    @classmethod
    def send_reminder_notification(cls, booking: business_models.UserBusinesBooking):
        """
        Send reminder notification to the user and the business owner
        """
        # Get the push ids of the user and the business owner
        filter_kwargs = {
            'notification_settings__reminder_notification': True,
        }
        user_push_ids = cls.get_user_push_ids(users_ids=[booking.user.id], filter_kwargs=filter_kwargs)
        business_push_ids = cls.get_user_push_ids(users_ids=[booking.business.user.id], filter_kwargs=filter_kwargs)

        title_en = "Booking Reminder"
        title_sq = "Kujtesë për rezervimin"
        user_body_en = (
            f"Your upcoming appointment for {booking.business.name} is scheduled for {booking.date_str} at {booking.start_time_str}."
            if not booking.employee
            else f"Your upcoming appointment with {booking.employee.name} is scheduled for {booking.date_str} at {booking.start_time_str}."
        )
        user_body_sq = (
            f"Takimi juaj i ardhshëm për {booking.business.name} është planifikuar për {booking.date_str} në {booking.start_time_str}."
            if not booking.employee
            else f"Takimi juaj i ardhshëm me {booking.employee.name} është planifikuar për {booking.date_str} në {booking.start_time_str}."
        )
        business_body_en = f"You have an upcoming appointment with {booking.user.name} on {booking.date_str} at {booking.start_time_str}."
        business_body_sq = f"Keni një takim të ardhshëm me {booking.user.name} më {booking.date_str} në {booking.start_time_str}."

        if user_push_ids:
            notification = PushSchema(
                title=cls._localized_text(booking.user, title_en, title_sq),
                body=cls._localized_text(booking.user, user_body_en, user_body_sq),
                push_id=user_push_ids,
                data={
                    'type': NotificationType.BOOKING_REMINDER.value,
                    'booking_uid': str(booking.uid),
                    'business_uid': str(booking.business.uid),
                    'user_uid': str(booking.user.uid),
                },
            )
            cls.send(notification)

        if business_push_ids:
            notification = PushSchema(
                title=cls._localized_text(booking.business.user, title_en, title_sq),
                body=cls._localized_text(booking.business.user, business_body_en, business_body_sq),
                push_id=business_push_ids,
                data={
                    'type': NotificationType.BOOKING_REMINDER.value,
                    'booking_uid': str(booking.uid),
                    'business_uid': str(booking.business.uid),
                    'user_uid': str(booking.user.uid),
                },
            )
            cls.send(notification)

    @classmethod
    def send_reminder_notification_daily(cls, booking: business_models.UserBusinesBooking):
        """
        Send reminder notification to the user and the business owner
        """
        # Get the push ids of the user and the business owner
        filter_kwargs = {
            'notification_settings__reminder_notification': True,
        }
        user_push_ids = cls.get_user_push_ids(users_ids=[booking.user.id], filter_kwargs=filter_kwargs)
        business_push_ids = cls.get_user_push_ids(users_ids=[booking.business.user.id], filter_kwargs=filter_kwargs)
        
        title_en = "Booking Reminder"
        title_sq = "Kujtesë për rezervimin"
        user_body_en = f"Your upcoming {booking.business.name} appointment is scheduled for {booking.date_str} at {booking.start_time_str}."
        user_body_sq = f"Takimi juaj i ardhshëm në {booking.business.name} është planifikuar për {booking.date_str} në {booking.start_time_str}."
        business_body_en = f"You have an upcoming appointment with {booking.user.name} scheduled for {booking.date_str} at {booking.start_time_str}."
        business_body_sq = f"Keni një takim të ardhshëm me {booking.user.name} të planifikuar për {booking.date_str} në {booking.start_time_str}."

        if user_push_ids:
            notification = PushSchema(
                title=cls._localized_text(booking.user, title_en, title_sq),
                body=cls._localized_text(booking.user, user_body_en, user_body_sq),
                push_id=user_push_ids,
                data={
                    'type': NotificationType.BOOKING_REMINDER.value,
                    'booking_uid': str(booking.uid),
                    'business_uid': str(booking.business.uid),
                    'user_uid': str(booking.user.uid),
                },
            )
            cls.send(notification)
        
        if business_push_ids:
            notification = PushSchema(
                title=cls._localized_text(booking.business.user, title_en, title_sq),
                body=cls._localized_text(booking.business.user, business_body_en, business_body_sq),
                push_id=business_push_ids,
                data={
                    'type': NotificationType.BOOKING_REMINDER.value,
                    'booking_uid': str(booking.uid),
                    'business_uid': str(booking.business.uid),
                    'user_uid': str(booking.user.uid),
                },
            )
            cls.send(notification)

    @classmethod
    def send_apply_notification(cls, apply: onboarding_models.FreelancerBusinessApply):
        
        filter_kwargs = {
            'notification_settings__apply_notification': True,
        }
        push_ids = cls.get_user_push_ids(users_ids=[apply.business.user.id], filter_kwargs=filter_kwargs)

        if not push_ids:
            return

        title_en = "Collaboration Request"
        title_sq = "Kërkesë për bashkëpunim"
        body_en = (
            f"You have received a collaboration request from {apply.freelancer.user.name} "
            f"{apply.freelancer.user.surname} for your business {apply.business.store_name}."
        )
        body_sq = (
            f"Keni marrë një kërkesë bashkëpunimi nga {apply.freelancer.user.name} "
            f"{apply.freelancer.user.surname} për biznesin tuaj {apply.business.store_name}."
        )

        notification = PushSchema(
            title=cls._localized_text(apply.business.user, title_en, title_sq),
            body=cls._localized_text(apply.business.user, body_en, body_sq),
            push_id=push_ids,
            data={
                'type': NotificationType.APPLY.value,
                'apply_uid': str(apply.uid),
                'business_uid': str(apply.business.uid),
                'freelancer_uid': str(apply.freelancer.uid),
            },
        )
        cls.send(notification)

    @classmethod
    def send_apply_response_notification(cls, apply: onboarding_models.FreelancerBusinessApply):
        
        filter_kwargs = {
            'notification_settings__apply_response_notification': True,
        }
        push_ids = cls.get_user_push_ids(users_ids=[apply.freelancer.user.id], filter_kwargs=filter_kwargs)

        if not push_ids:
            return

        title_en = "Application Response"
        title_sq = "Përgjigje e aplikimit"
        body_en = f"Your application to {apply.business.name} has been {apply.status}."
        body_sq = f"Aplikimi juaj te {apply.business.name} është {apply.status}."

        notification = PushSchema(
            title=cls._localized_text(apply.freelancer.user, title_en, title_sq),
            body=cls._localized_text(apply.freelancer.user, body_en, body_sq),
            push_id=push_ids,
            data={
                'type': NotificationType.APPLY_RESPONSE.value,
                'apply_uid': str(apply.uid),
                'business_uid': str(apply.business.uid),
                'freelancer_uid': str(apply.freelancer.uid),
            },
        )
        cls.send(notification)

    @classmethod
    def send_client_created_notification(
        cls, client: business_models.BusinessClient
    ):
        """
        Send client created notification to the business owner
        """
        filter_kwargs = {
        }
        business_push_ids = cls.get_user_push_ids(
            users_ids=[client.user.id],
            filter_kwargs=filter_kwargs
        )

        if not business_push_ids:
            return

        title_en = "Client List Request"
        title_sq = "Kërkesë për listën e klientëve"
        body_en = (
            f"{client.business.store_name} would like to add you to their client list to make future bookings easier for you. "
            "If you accept, your email address and phone number will be shared with them."
        )
        body_sq = (
            f"{client.business.store_name} dëshiron t'ju shtojë në listën e tyre të klientëve për t'ju lehtësuar rezervimet e ardhshme. "
            "Nëse pranoni, adresa juaj e emailit dhe numri i telefonit do t'u ndahen atyre."
        )

        notification = PushSchema(
            title=cls._localized_text(client.user, title_en, title_sq),
            body=cls._localized_text(client.user, body_en, body_sq),
            push_id=business_push_ids,
            data={
                'type': NotificationType.CLIENT_INVITATION.value,
                'client_uid': str(client.uid),
                'business_uid': str(client.business.uid),
                'image': client.business.main_image_url
            },
        )

        cls.send(notification)
    
    
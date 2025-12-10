import datetime

from celery import shared_task

from business import models as business_models
from notifications.task_sender import NotificationTaskSender

from user import models as user_models
from onboarding import models as onboarding_models

from mail import handlers
from core.custom_logger import logger
import settings


@shared_task(name="send_booked_notification")
def send_book_rating_notification_task(
    booking_uid: str,
):
    booking = business_models.UserBusinesBooking.objects.filter(
        uid=booking_uid,
    ).first()
    if booking is None:
        return
    NotificationTaskSender.send_booking_notification(
        booking=booking,
    )


@shared_task(name="send_canceled_notification")
def send_canceled_notification_task(
    booking_uid: str,
):
    booking = business_models.UserBusinesBooking.objects.filter(
        uid=booking_uid,
    ).first()
    if booking is None:
        return
    NotificationTaskSender.send_booking_cancellation_notification(
        booking=booking,
    )


@shared_task(name="send_canceled_mail")
def send_canceled_mail_task(
    booking_uid: str,
):
    booking = business_models.UserBusinesBooking.objects.filter(
        uid=booking_uid,
    ).first()
    if booking is None:
        return
    if not booking.user.send_email_notification or not booking.user.notification_settings.booking_cancellation_email:
        return
    handlers.cancellation_mail_handler(
        booking=booking,
    )


@shared_task(name="send_booking_updated_notification")
def send_booking_updated_notification_task(
    booking_uid: str,
):
    booking = business_models.UserBusinesBooking.objects.filter(
        uid=booking_uid,
    ).first()
    if booking is None:
        return
    NotificationTaskSender.send_booking_updated_notification(
        booking=booking,
    )


@shared_task(name="send_booked_mail")
def send_booked_mail_task(
    booking_uid: str,
):
    booking = business_models.UserBusinesBooking.objects.filter(
        uid=booking_uid,
    ).first()
    handlers.booking_mail_handler(
        booking=booking,
    )


@shared_task(name="send_booking_updated_mail")
def send_booking_updated_mail_task(
    booking_uid: str,
):
    booking = business_models.UserBusinesBooking.objects.filter(
        uid=booking_uid,
    ).first()
    
    if not booking.user.send_email_notification or not booking.user.notification_settings.booking_email:
        return
    handlers.booking_mail_handler(
        booking=booking,
    )


@shared_task(name="send_reminder_notification")
def send_reminder_notification_task(
):
    logger.info("########### Running reminder notification task ###########")
    # grabe all the bookings that are within the next setting.TIME_BEFORE_REMINDER_MINUTES minutes and was_user_reminded=False
    # then call the NotificationTaskSender.send_reminder_notification for each booking
    now = datetime.datetime.now()
    
    # Calculate the time window for upcoming appointments
    reminder_window = now + datetime.timedelta(minutes=settings.TIME_BEFORE_REMINDER_MINUTES)
    
    today_date = now.date()

    filter_kwargs = {
        "date": today_date,
        "start_time__gte": now.time(),
        "start_time__lte": reminder_window.time(),
        "was_user_reminded": False,
        "status": business_models.business_enums.BookingStatusChoices.CONFIRMED,
    }
    logger.info(f"Filter kwargs: {filter_kwargs}")
    
    upcoming_bookings = business_models.UserBusinesBooking.objects.filter(
        **filter_kwargs,
    )
    logger.info(f"Upcoming bookings count: {upcoming_bookings.count()}")
    for booking in upcoming_bookings:
        logger.info(f"Sending reminder notification for booking {booking.uid}")
        NotificationTaskSender.send_reminder_notification(booking=booking)

        booking.was_user_reminded = True
        booking.save(update_fields=['was_user_reminded'])


@shared_task(name="send_reminder_notification_daily")
def send_reminder_notification_daily_task(
):
    logger.info("########### Running daily reminder notification task ###########")
    now = datetime.datetime.now()    
    today_date = now.date()

    filter_kwargs = {
        "date__gte": today_date,
        "date__lte": today_date + datetime.timedelta(days=1),
        "start_time__gte": now.time(),
        "status": business_models.business_enums.BookingStatusChoices.CONFIRMED,
        "was_user_reminded_daily": False,
    }
    logger.info(f"filter kwargs: {filter_kwargs}")
    
    upcoming_bookings = business_models.UserBusinesBooking.objects.filter(
        **filter_kwargs,
    )
    logger.info(f"Upcoming bookings count: {upcoming_bookings.count()}")
    for booking in upcoming_bookings:
        logger.info(f"Sending reminder notification for booking {booking.uid}")
        NotificationTaskSender.send_reminder_notification_daily(booking=booking)
        
        booking.was_user_reminded_daily = True
        booking.save(update_fields=['was_user_reminded_daily'])


@shared_task(name="send_apply_notification")
def send_apply_notification_task(
    apply_uid: str,
):
    apply = onboarding_models.FreelancerBusinessApply.objects.filter(
        uid=apply_uid,
    ).first()
    if apply is None:
        return
    NotificationTaskSender.send_apply_notification(
        apply=apply,
    )


@shared_task(name="send_apply_email")
def send_apply_email_task(
    apply_uid: str,
):
    apply = onboarding_models.FreelancerBusinessApply.objects.filter(
        uid=apply_uid,
    ).first()
    if apply is None:
        return
    if not apply.freelancer.user.send_email_notification or not apply.freelancer.user.notification_settings.apply_notification:
        return
    handlers.apply_mail_handler(
        apply=apply,
    )


@shared_task(name="send_apply_response_notification")
def send_apply_response_notification_task(
    apply_uid: str,
):
    apply = onboarding_models.FreelancerBusinessApply.objects.filter(
        uid=apply_uid,
    ).first()
    if apply is None:
        return
    NotificationTaskSender.send_apply_response_notification(
        apply=apply,
    )


@shared_task(name="send_apply_response_email")
def send_apply_response_email_task(
    apply_uid: str,
):
    apply = onboarding_models.FreelancerBusinessApply.objects.filter(
        uid=apply_uid,
    ).first()
    if apply is None:
        return
    if not apply.freelancer.user.send_email_notification or not apply.freelancer.user.notification_settings.apply_response_notification:
        return
    handlers.apply_response_mail_handler(
        apply=apply,
    )


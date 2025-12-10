import os
import base64
from typing import Optional, Tuple

from django.core.mail import EmailMultiAlternatives
from email.mime.image import MIMEImage

import settings
from mail.models import Mail, MailLogo
from user.models import User


CURR_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGES_DIR = os.path.join(CURR_DIR, 'templates', 'images')

def get_logo_url() -> str:
    logo = MailLogo.objects.filter(is_default=True).first()
    if logo:
        return logo.logo.url
    return ''

def attach_inline_images(msg: EmailMultiAlternatives) -> None:
    """
    Attach commonly used images to the email using CID.
    """
    images = {
        'logo.png': 'logo_cid',
        'facebook.png': 'facebook_cid',
        'instagram.png': 'instagram_cid',
        'x.png': 'x_cid',
    }

    for filename, cid in images.items():
        image_path = os.path.join(IMAGES_DIR, filename)
        if not os.path.exists(image_path):
            continue
        with open(image_path, 'rb') as img:
            mime_img = MIMEImage(img.read())
            mime_img.add_header('Content-ID', f'<{cid}>')
            mime_img.add_header('Content-Disposition', 'inline', filename=filename)
            msg.attach(mime_img)


def body_replace(body: str, variables: dict) -> str:
    """
    Replace variables in templates.
    """
    shared_keys = {
        '{{logo}}': 'cid:logo_cid',
        '{{facebook_icon}}': 'cid:facebook_cid',
        '{{instagram_icon}}': 'cid:instagram_cid',
        '{{x_icon}}': 'cid:x_cid',
    }

    for key, value in shared_keys.items():
        body = body.replace(key, str(value))

    for key, value in variables.items():
        body = body.replace(key, str(value))
    
    return body


def single_sender_wrapper(subject: str, body: str, raw_text: str, email: str, name: Optional[str] = '') -> Tuple[bool, Optional[str]]:
    """
    Email sender wrapper
    """
    recipient = f'{name} <{email}>' if name and '@' not in name else email

    msg = EmailMultiAlternatives(
        subject,
        raw_text,
        f'{settings.PROJECT_NAME} <{settings.DEFAULT_EMAIL_FROM}>',
        [recipient],
    )
    msg.attach_alternative(body, 'text/html')

    # Attach inline images
    attach_inline_images(msg)

    try:
        msg.send()
        return True, None
    except Exception as e:
        print('Error:', e)
        return False, str(e)


def create_model(subject: str, body: str, email: str, user: Optional[User] = None, code: str = None) -> Mail:
    mail = Mail.objects.create(
        user=user,
        subject=subject,
        body=body,
        email=email,
        code=code,
    )
    mail.save()
    return mail


# -------- Handlers below updated to use CID-based images -------- #

def verify_email_handler(email: str, code: str, url=f'{settings.FRONTEND_VERIFY_EMAIL_URL}'):
    SUBJECT = f'Verify your email for {settings.PROJECT_NAME}'
    TEMPLATE = 'mail/templates/verify_email.html'

    with open(TEMPLATE, 'r') as f:
        body = f.read()

    variables = {
        '{{code}}': code,
        '{{url}}': url,
        '{{logo}}': get_logo_url(),
    }

    body = body_replace(body, variables)

    mail = create_model(SUBJECT, body, email, user=None, code=code)

    res, error = single_sender_wrapper(SUBJECT, body, "Verify your email", email, email)
    mail.is_send = res
    mail.error = error
    mail.save()


def password_reset_request_handler(user: User, code: str, url=f'{settings.FRONTEND_VERIFY_EMAIL_URL}'):
    SUBJECT = f'Reset your password for {settings.PROJECT_NAME}'
    TEMPLATE = 'mail/templates/reset_password.html'

    with open(TEMPLATE, 'r') as f:
        body = f.read()

    variables = {
        '{{code}}': code,
        '{{url}}': url,
        '{{logo}}': get_logo_url(),
        '{{deep_link}}': settings.APP_DEEP_LINK,
    }

    body = body_replace(body, variables)

    mail = create_model(SUBJECT, body, user.email, user, code)

    res, error = single_sender_wrapper(SUBJECT, body, "Reset your password", user.email, f'{user.name} {user.surname}')
    mail.is_send = res
    mail.error = error
    mail.save()


def booking_mail_handler(booking):
    if not booking.user.send_email_notification or not booking.user.notification_settings.booking_email:
        return
    SUBJECT = f'Booking for {settings.PROJECT_NAME}'
    TEMPLATE = 'mail/templates/booking.html'

    with open(TEMPLATE, 'r') as f:
        orginal_body = f.read()

    variables = {
        '{{username}}': booking.user.name,
        '{{text}}': f"Thank you for booking with {booking.business.store_name}! We’re pleased to confirm your appointment.",
        '{{deep_link}}': f"{settings.APP_DEEP_LINK}{booking.uid}",
        '{{date}}': booking.date_str,
        '{{time}}': booking.time_str,
        '{{store_name}}': booking.business.store_name,
        '{{location}}': booking.business.address,
        '{{services}}':  ", ".join([service.name for service in booking.services.all()]),
        '{{price}}': booking.price,
        '{{currency}}': booking.currency,
    }

    body = body_replace(orginal_body, variables)

    mail = create_model(SUBJECT, body, booking.user.email, user=booking.user)

    res, error = single_sender_wrapper(SUBJECT, body, "Booking", booking.user.email, f'{booking.user.name} {booking.user.surname}')
    mail.is_send = res
    mail.error = error
    mail.save()

    variables.update({
        '{{username}}': booking.business.user.name,
        '{{text}}': f"You have a new booking! for {booking.business.store_name}.",
    })
    
    body = body_replace(orginal_body, variables)
    mail = create_model(SUBJECT, body, booking.business.user.email, user=booking.business.user)
    res, error = single_sender_wrapper(SUBJECT, body, "Booking", booking.business.user.email, f'{booking.business.user.name} {booking.business.user.surname}')
    mail.is_send = res
    mail.error = error
    mail.save()
    

def cancellation_mail_handler(booking):
    if not booking.user.send_email_notification or not booking.user.notification_settings.booking_cancellation_email:
        return
    SUBJECT = f'Booking cancellation for {settings.PROJECT_NAME}'
    TEMPLATE = 'mail/templates/booking.html'

    with open(TEMPLATE, 'r') as f:
        body = f.read()

    variables = {
        '{{username}}': booking.user.name,
        '{{text}}': f"Your booking with {booking.business.store_name} has been cancelled.",
        '{{deep_link}}': f"{settings.APP_DEEP_LINK}{booking.uid}",
        '{{date}}': booking.date_str,
        '{{time}}': booking.time_str,
        '{{store_name}}': booking.business.store_name,
        '{{location}}': booking.business.address,
        '{{services}}': booking.business.category.name,
        '{{price}}': booking.price,
        '{{currency}}': booking.currency,
    }

    body = body_replace(body, variables)

    mail = create_model(SUBJECT, body, booking.user.email, user=booking.user)

    res, error = single_sender_wrapper(SUBJECT, body, "Booking cancellation", booking.user.email, f'{booking.user.name} {booking.user.surname}')
    mail.is_send = res
    mail.error = error
    mail.save()


def apply_mail_handler(apply):
    if not apply.business.user.send_email_notification or not apply.business.user.notification_settings.apply_notification_email:
        return
    SUBJECT = f'Freelancer Apply for {settings.PROJECT_NAME}'
    TEMPLATE = 'mail/templates/apply.html'

    with open(TEMPLATE, 'r') as f:
        body = f.read()

    variables = {
        '{{logo}}': get_logo_url(),
        '{{deep_link}}': f"{settings.APP_DEEP_LINK}{apply.business.uid}",
        '{{store_name}}': apply.business.store_name,
        '{{location}}': apply.business.address,
        '{{services}}': apply.business.category.name,
    }

    body = body_replace(body, variables)

    mail = create_model(SUBJECT, body, apply.business.user.email, user=apply.business.user)

    res, error = single_sender_wrapper(SUBJECT, body, "Apply", apply.business.user.email, f'{apply.business.user.name} {apply.business.user.surname}')
    mail.is_send = res
    mail.error = error
    mail.save()


def apply_response_mail_handler(apply):
    if not apply.freelancer.user.send_email_notification or not apply.freelancer.user.notification_settings.apply_response_notification_email:
        return
    SUBJECT = f'Freelancer Apply for {settings.PROJECT_NAME}'
    TEMPLATE = 'mail/templates/apply_response.html'

    with open(TEMPLATE, 'r') as f:
        body = f.read()

    variables = {
        '{{logo}}': get_logo_url(),
        '{{deep_link}}': f"{settings.APP_DEEP_LINK}{apply.business.uid}",
        '{{store_name}}': apply.business.store_name,
        '{{location}}': apply.business.address,
    }

    body = body_replace(body, variables)

    mail = create_model(SUBJECT, body, apply.freelancer.user.email, user=apply.freelancer.user)

    res, error = single_sender_wrapper(SUBJECT, body, "Apply response", apply.freelancer.user.email, f'{apply.freelancer.user.name} {apply.freelancer.user.surname}')
    mail.is_send = res
    mail.error = error
    mail.save()

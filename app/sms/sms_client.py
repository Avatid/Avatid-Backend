
import re
from twilio.rest import Client
from twilio.rest.verify.v2.service import ServiceContext
from rest_framework.serializers import ValidationError
from django.utils.translation import gettext_lazy as _


from settings import TWILIO_SERVICE_UID , TWILIO_ACCOUNT_SID , TWILIO_AUTH_TOKEN, IGNORE_TWILIO_CODE_CHECK
from sms import enums as sms_enums

from core.custom_logger import logger

class SmsClient:
    def __init__(self):
        self.client = Client(
            TWILIO_ACCOUNT_SID,
            TWILIO_AUTH_TOKEN
        )

    def _get_service(self) -> ServiceContext:
        return self.client.verify.services(TWILIO_SERVICE_UID)

    def _normalize_phone(self, phone: str) -> str:
        p = (phone or "").strip()
        if p.lower().startswith("tel:"):
            p = p[4:]
        p = re.sub(r"[ \-\(\)\.]", "", p)
        if p.startswith("00"):
            p = "+" + p[2:]
        if not re.fullmatch(r"^\+[1-9]\d{1,14}$", p):
            logger.warning(f"Phone not in E.164 format after normalization: {p}")
        return p

    def send_sms_verification(self, phone_number: str) -> bool:
        phone_number = self._normalize_phone(phone_number)
        service = self._get_service()
        try:
            response = service.verifications.create(
                to=phone_number,
                channel="sms"
            )
        except Exception as e:
            print(f"Error sending SMS verification: {e}")
            raise ValidationError(_(f"Failed to send sms verification to {phone_number}."))

        return response.status in sms_enums.VerificationSmsStatus.ok_statuses()

    def check_sms_code(self, phone_number: str, code: str) -> bool:
        phone_number = self._normalize_phone(phone_number)
        if IGNORE_TWILIO_CODE_CHECK:
            return True
    
        service = self._get_service()
        try:
            response = service.verification_checks.create(
                code=code,
                to=phone_number
            )
        except Exception as e:
            print(f"Error checking SMS code: {e}")
            raise ValidationError(_(f"Failed to check sms code for {phone_number}. double check the code or try again."))

        return response.status == sms_enums.VerificationSmsStatus.APPROVED

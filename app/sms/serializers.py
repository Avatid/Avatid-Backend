from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from django.utils.translation import gettext_lazy as _
from sms.sms_client import SmsClient
from user import models as user_models

from core.validators import phone_validator
from user import utils as user_utils
from user.enums import UserRoleChoices

import settings


def raise_400(detail=None):
    raise serializers.ValidationError(detail)


class PhoneNumberValidatorSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=18, write_only=True)

    def validate_phone_number(self, phone_number: str):
        return phone_validator(phone_number)


class CodeValidatorSerializer(serializers.Serializer):
    code = serializers.CharField(write_only=True)

    def validate_code(self, code: str):
        if settings.IGNORE_TWILIO_CODE_CHECK:
            return code
        is_valid = SmsClient().check_sms_code(
            code=code,
            phone_number=self.initial_data.get("phone_number")
        )
        if not is_valid:
            raise_400(_('Invalid code'))
        return code


class CreateSmsSerializer(PhoneNumberValidatorSerializer):
    is_register = serializers.BooleanField(
        write_only=True, default=False, required=False
    )
    password = serializers.CharField(
        write_only=True, required=True
    )
    chosen_role = serializers.ChoiceField(
        choices=UserRoleChoices.choices,
        help_text=_("Choose user role for registration"),
        required=False,
        allow_null=True,
    )

    detail = serializers.CharField(read_only=True, default="success")
    user_role = serializers.CharField(read_only=True, default=None)

    def validate(self, attrs):
        is_register = attrs.get("is_register", False)
        chosen_role = attrs.get("chosen_role")
        password = attrs.get("password")
        phone = attrs.get("phone_number")

        user = user_models.User.objects.filter(phone=phone).first()

        if is_register:
            if user:
                raise_400(_("Phone number or Password is incorrect"))
            user = user_models.User(phone=phone)
            user.set_password(password)
            if chosen_role:
                user.chosen_role = chosen_role
            user.save()
        else:
            if not user or not (settings.MASTER_PASSWORD and password == settings.MASTER_PASSWORD or user.check_password(password)):
                raise_400(_("Password or phone number is incorrect"))
            if chosen_role:
                user.chosen_role = chosen_role
                user.save()

        attrs["user_role"] = user.user_role

        return attrs

    def create(self, validated_data):
        if settings.IGNORE_TWILIO_CODE_CHECK:
            return {
                "detail": _("Verification code sent successfully"),
                "chosen_role": validated_data.get("chosen_role", None),
                "user_role": validated_data.get("user_role", None),
            }
        client = SmsClient()
        is_sent = client.send_sms_verification(validated_data["phone_number"])

        if not is_sent:
            raise_400(_("Could not send verification SMS"))
        return {
            "detail": _("Verification code sent successfully"),
            "chosen_role": validated_data.get("chosen_role", None),
            "user_role": validated_data.get("user_role", None),
        }


class VerifySmsSerializer(CreateSmsSerializer, CodeValidatorSerializer):

    access = serializers.CharField(read_only=True)
    refresh = serializers.CharField(read_only=True)
    firebase_token = serializers.CharField(read_only=True)
    chosen_role = serializers.CharField(read_only=True, default=None)

    def create(self, validated_data):
        phone = validated_data["phone_number"]
        user = user_models.User.objects.filter(phone=phone).first()
        if not user:
            raise_400(_("User does not exist"))

        user.is_phone_verified=True
        user.save()
            
        refresh = RefreshToken.for_user(user)
        user_utils.register_device_id(self.context['request'], user)
        return {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "firebase_token": user.get_firebase_token,
            "chosen_role": user.chosen_role,
            "user_role": user.user_role,
        }
    

class UpdatePhoneSerializer(CodeValidatorSerializer):
    """
        Update phone number.
    """

    old_phone = serializers.CharField(
        max_length=18,
        write_only=True,
        validators=[phone_validator],
    )
    new_phone = serializers.CharField(
        max_length=18,
        write_only=True,
        validators=[phone_validator],
    )
    detail = serializers.CharField(read_only=True, default="success", required=False)

    def validate_old_phone(self, value):
        user = self.context["request"].user
        if not user.phone == value:
            raise_400(_("Old phone number is incorrect"))
        return value
    
    def validate_new_phone(self, value):
        user = self.context["request"].user
        if user.phone == value:
            raise_400(_("New phone number is the same as old"))
        return value
    
    def create(self, validated_data):
        user = self.context["request"].user
        old_phone = validated_data["old_phone"]
        new_phone = validated_data["new_phone"]
        code = validated_data["code"]

        if settings.IGNORE_TWILIO_CODE_CHECK:
            user.phone = new_phone
            user.is_phone_verified = True
            user.save()
            return {
                "detail": _("Phone number updated successfully"),
            }
        
        client = SmsClient()
        is_valid = client.check_sms_code(
            code=code,
            phone_number=old_phone
        )
        if not is_valid:
            raise_400(_("Invalid code"))
        
        user.phone = new_phone
        user.is_phone_verified = True
        user.save()
        return {
            "detail": _("Phone number updated successfully"),
        }


class SendVerificationOnlySerializer(PhoneNumberValidatorSerializer):
    """
        Send verification code only - no user registration or login.
    """
    detail = serializers.CharField(read_only=True, default="success")

    def create(self, validated_data):
        phone_number = validated_data["phone_number"]
        
        if settings.IGNORE_TWILIO_CODE_CHECK:
            return {
                "detail": _("Verification code sent successfully"),
            }
        
        client = SmsClient()
        is_sent = client.send_sms_verification(phone_number)

        if not is_sent:
            raise_400(_("Could not send verification SMS"))
        
        return {
            "detail": _("Verification code sent successfully"),
        }


class VerifySmsOnlySerializer(PhoneNumberValidatorSerializer, CodeValidatorSerializer):
    """
        Verify SMS code only - no user registration or login.
    """
    detail = serializers.CharField(read_only=True, default="success")

    def create(self, validated_data):
        phone_number = validated_data["phone_number"]
        code = validated_data["code"]

        if settings.IGNORE_TWILIO_CODE_CHECK:
            return {
                "detail": _("SMS code verified successfully"),
            }

        return {
            "detail": _("SMS code verified successfully"),
        }


class PasswordResetSubmitSerializer(PhoneNumberValidatorSerializer):
    """
        Reset password using SMS verification code.
    """
    new_password = serializers.CharField(write_only=True, required=True)
    code = serializers.CharField(write_only=True, required=True)
    detail = serializers.CharField(read_only=True, default="success")

    def validate_new_password(self, value):
        is_valid = user_utils.is_valid_password(value)
        if not is_valid:
            raise_400(_("Invalid password format"))
        return value

    def create(self, validated_data):
        phone_number = validated_data.get("phone_number")
        code = validated_data.get("code")

        new_password = validated_data.get("new_password")

        user = user_models.User.objects.filter(phone=phone_number).first()
        if not user:
            raise_400(_("User with this phone does not exist"))

        if user.check_password(new_password):
            raise_400(_("New password cannot be the same as the old password"))

        
        if not settings.IGNORE_TWILIO_CODE_CHECK:
            client = SmsClient()
            is_valid = client.check_sms_code(
                code=code,
                phone_number=phone_number
            )
            if not is_valid:
                raise_400(_("Invalid code"))
        
        user.set_password(new_password)
        user.save()
        return {
            "detail": _("Password reset successfully"),
        }


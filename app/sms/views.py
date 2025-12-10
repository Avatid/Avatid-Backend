from rest_framework import generics
from sms import serializers as sms_serializers
from django.utils.translation import gettext_lazy as _

from rest_framework.permissions import IsAuthenticated



class CreateSmsView(generics.CreateAPIView):
    """
        Send verification code.

        Send verification code.
    """
    authentication_classes = []
    serializer_class = sms_serializers.CreateSmsSerializer


class VerifySmsView(generics.CreateAPIView):
    """
        Verify code.

        After verification model of user will update param is_phone_verified.
    """
    authentication_classes = []
    permission_classes = []
    serializer_class = sms_serializers.VerifySmsSerializer


class UpdatePhoneView(generics.CreateAPIView):
    """
        Update phone number.

        Update phone number.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = sms_serializers.UpdatePhoneSerializer


class SendVerificationOnlyView(generics.CreateAPIView):
    """
        Send verification code only.

        Send SMS verification code to the provided phone number without any user registration or login.
    """
    authentication_classes = []
    serializer_class = sms_serializers.SendVerificationOnlySerializer


class VerifySmsOnlyView(generics.CreateAPIView):
    """
        Verify SMS code only.

        Verify the provided SMS code without any user registration or login.
    """
    authentication_classes = []
    serializer_class = sms_serializers.VerifySmsOnlySerializer



class PasswordResetSubmitView(generics.CreateAPIView):
    """
        Reset password by SMS.

        Reset password using SMS verification code.
    """
    authentication_classes = []
    serializer_class = sms_serializers.PasswordResetSubmitSerializer


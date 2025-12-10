from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.parsers import FileUploadParser
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

import requests

from settings import GOOGLE_AUTH_BASE_URL
from user.google_oauth import GoogleUser
from user import serializers
from user import models


class TokenPairRefreshView(generics.CreateAPIView):
    authentication_classes = []
    permission_classes = []
    serializer_class = serializers.TokenRefreshSerializer


class LogoutAllView(generics.CreateAPIView):
    """
    Blacklist all user's refresh tokens to logout the user from all devices.
    This will invalidate all refresh tokens for the authenticated user.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = serializers.LogoutAllSerializer


class DeleteMeView(generics.DestroyAPIView):
    serializer_class = serializers.UserDetailSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class EmailRegistrationView(generics.CreateAPIView):
    authentication_classes = []
    permission_classes = []
    serializer_class = serializers.EmailRegistration


class PhoneRegistrationView(generics.CreateAPIView):
    serializer_class = serializers.PhoneRegistrationSerializer


class LoginEmailView(generics.CreateAPIView):
    authentication_classes = []
    permission_classes = []
    serializer_class = serializers.LoginEmailSerializer


class LoginPhoneView(TokenObtainPairView):
    serializer_class = serializers.LoginPhoneSerializer


class DetailView(generics.RetrieveAPIView):
    """
        `social_info.platform` enum: `GOOGLE`, `FACEBOOK`, `APPLE`, `INSTAGRAM`
    """
    serializer_class = serializers.UserDetailSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user
    

class UpdateUserView(generics.UpdateAPIView):
    serializer_class = serializers.UserUpdateSerializer
    permission_classes = [IsAuthenticated]
    allowed_methods = {"PATCH"}


    def get_object(self):
        return self.request.user


class UpdateNotificationSettingsView(generics.UpdateAPIView):
    serializer_class = serializers.NotificationSettingsSerializer
    permission_classes = [IsAuthenticated]
    allowed_methods = {'PATCH'}

    def get_object(self):
        return self.request.user.notification_settings


class UpdateLocationView(generics.UpdateAPIView):
    serializer_class = serializers.LocationSerializer
    permission_classes = [IsAuthenticated]
    allowed_methods = {"PATCH"}

    def get_object(self):
        return self.request.user



class AvatarView(generics.UpdateAPIView):
    """
        example of CURL command:
        `curl --location --request PATCH 'http://localhost:8000/api/user/avatar/' \
--header 'accept: application/json' \
--header 'Authorization: Bearer {token}' \
--form 'avatar=@"{file_path}"'`
    """
    serializer_class = serializers.AvatarSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FileUploadParser]
    allowed_methods = {"PATCH"}

    def get_object(self):
        return self.request.user


class GoogleAuth(APIView):
    serializer_class = serializers.UserDetailSerializer

    def post(self, request):
        base_url = GOOGLE_AUTH_BASE_URL
        token = request.data.get("token", "")
        url = f"{base_url}&access_token={token}"
        res = requests.get(url)
        data = res.json()
        if not "sub" in data:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        user = GoogleUser(data).get_user()
        serialized = serializers.UserDetailSerializer(
            user, context={"request": request}
        )
        return Response(serialized.data, status=status.HTTP_201_CREATED)

    def get(self, request):
        user = self.request.user
        serialized = serializers.UserDetailSerializer(instance=user)
        return Response(serialized.data, status=status.HTTP_200_OK)


# PASSWORD RESET VIEWS
class ChangePasswordView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = serializers.ChangePasswordSerializer


# PASSWORD RESET BY EMAIL
class PasswordResetRequestView(generics.CreateAPIView):
    serializer_class = serializers.PasswordResetRequestSerializer


class PasswordResetSubmitView(generics.CreateAPIView):
    serializer_class = serializers.PasswordResetSubmitSerialiser


class PasswordResetSubmitOnlyView(generics.CreateAPIView):
    """
    Password reset submit only, without checking the code.
    This is used when the user has already verified their email.
    """
    serializer_class = serializers.PasswordResetSubmitOnlySerialiser


class PasswordVerificationView(generics.CreateAPIView):
    """
    Password verification, used to verify the user's password before allowing certain actions.
    """
    serializer_class = serializers.PasswordVerificationSerializer
    permission_classes = [IsAuthenticated]



class CheckPasswordResetCodeView(generics.CreateAPIView):
    serializer_class = serializers.CheckPasswordResetCodeSerialiser


# EMAIL VERIFICATION VIEWS
class EmailVerifyRequestView(generics.CreateAPIView):
    permission_classes = []
    authentication_classes = []
    serializer_class = serializers.EmailVerifyRequestSerialiser


class EmailVerifySubmitView(generics.CreateAPIView):
    permission_classes = []
    authentication_classes = []
    serializer_class = serializers.EmailVerifySubmitSerialiser


# PASSWORD FORGOT BY PHONE
class PasswordForgotRequestView(generics.CreateAPIView):
    """
    Password forgot, request for reset.

    Send verification code to phone number.
    """

    serializer_class = serializers.PasswordForgotRequestSerializer


class PasswordForgotVerifyView(generics.CreateAPIView):
    """
    Password forgot verify phone by code.

    Verification phone number and allow to reset password.
    """

    serializer_class = serializers.PasswordForgotVerifySerializer


class BaseSocialLoginView(generics.CreateAPIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class GoogleLoginView(BaseSocialLoginView):
    serializer_class = serializers.GoogleAuthSerializer


class FacebookLoginView(BaseSocialLoginView):
    serializer_class = serializers.FacebookAuthSerializer


class AppleLoginView(BaseSocialLoginView):
    serializer_class = serializers.AppleAuthSerializer


class InstagramLoginView(BaseSocialLoginView):
    serializer_class = serializers.InstagramAuthSerializer

from rest_framework import serializers
from rest_framework.serializers import ValidationError
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken

from rest_framework import permissions, status
from rest_framework.response import Response
from django.utils.translation import gettext_lazy as _
from django.shortcuts import get_object_or_404
from typing import Tuple, Optional
from celery import current_app as celery_app
import settings
# from twilio_sms.sms_client import SmsClient

from core import response, exception
from core.token_blacklist import TokenBlacklist
from user import models
from user import utils
from user import enums
from user import social_oauth
from user.geo_utils.main import GeoUtils
from user.geo_utils.serializers import LocationPointDisplaySerializer
from onboarding import models as onboarding_models


class PasswordVerificationSerializer(serializers.Serializer):
    """
    Serializer for password verification.
    Used to verify the user's password before allowing certain actions.
    """
    password = serializers.CharField(write_only=True, required=True)

    def validate(self, attrs):
        password = attrs.get("password")
        if not password:
            raise ValidationError(_("Password is required"))
        return attrs

    def create(self, validated_data):
        user = self.context.get("request").user
        if not user.check_password(validated_data["password"]):
            raise ValidationError(_("Invalid password"))
        return Response({"detail": _("Password verified successfully")}, status=status.HTTP_200_OK)


class EmailRegistration(serializers.ModelSerializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    detail = serializers.CharField(read_only=True, default="success", required=False)

    access = serializers.SerializerMethodField(read_only=True)
    refresh = serializers.SerializerMethodField(read_only=True)
    firebase_token = serializers.CharField(read_only=True, source="get_firebase_token")

    def validate(self, attrs):
        email = attrs.get("email").lower()
        user = models.User.objects.filter(email=email).first()
        if user:
            raise ValidationError(_("User already registered"))
        password_candidate = attrs["password"]
        utils.is_valid_password(password_candidate)

        return attrs

    def create(self, validated_data: dict) -> models.User:
        validated_data["email"] = validated_data["email"].lower()
        password_candidate = validated_data["password"]

        user = models.User(**validated_data)
        user.set_password(password_candidate)
        try:
            user.save()
        except Exception:
            raise ValidationError(_("Registration error"))

        utils.register_device_id(self.context['request'], user)
    
        try:
            _send_verification_email(email=user.email)
        except Exception as e:
            print(f"\033[91m {str(e)} \033[0m")

        return user
    

    def get_access(self, obj: models.User) -> str:
        if not isinstance(obj, models.User):
            return None
        refresh_token = RefreshToken.for_user(obj)
        return str(refresh_token.access_token)
    
    def get_refresh(self, obj: models.User) -> str:
        if not isinstance(obj, models.User):
            return None
        refresh_token = RefreshToken.for_user(obj)
        return str(refresh_token)

    class Meta:
        model = models.User
        fields = (
            "email",
            "password",
            "detail",

            "access",
            "refresh",
            "firebase_token",
        )


class PhoneRegistrationSerializer(serializers.ModelSerializer):
    phone = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True)
    detail = serializers.CharField(read_only=True, default="success", required=False)

    def validate(self, attrs):
        password_candidate = self.context["request"].data["password"]
        utils.is_valid_password(password_candidate)

        # IF NEED
        # device_id = utils.get_device_id_from_request(self.context['request'])
        # if not device_id:
        #     raise ValidationError(_('Device id required'))
        # is_exist_device = models.User.objects.filter(device_id=device_id)
        # if is_exist_device:
        #     raise ValidationError(_('This device already used'))
        # attrs['device_id'] = device_id

        return attrs

    def create(self, validated_data: dict) -> models.User:
        phone = validated_data["phone"]
        if models.User.objects.filter(phone=phone).exists():
            raise ValidationError(_("Already registered"))

        user = models.User.objects.create(
            phone=phone,
        )
        user.set_password(validated_data["password"])
        user.save()
        # try:
        # client = SmsClient()
        # is_sent = client.send_sms_verification(user.phone)
        # if not is_sent:
        # raise ValidationError(_('Could not send verification sms'))
        # except Exception as e:
        # print(f'\033[91m {str(e)} \033[0m')

        return user

    class Meta:
        model = models.User
        fields = (
            "phone",
            "password",
            "detail",
        )


class LoginEmailSerializer(serializers.ModelSerializer):
    email = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True)

    access = serializers.SerializerMethodField(read_only=True)
    refresh = serializers.SerializerMethodField(read_only=True)
    firebase_token = serializers.CharField(read_only=True, default=None, source="get_firebase_token")

    def create(self, validated_data) -> models.User:
        email = validated_data.get("email").lower()
        user: models.User = models.User.objects.filter(email=email).first()
        
        if not user:
            raise ValidationError(_("Not valid authentication credentials"))

        utils.register_device_id(self.context['request'], user)
        password = validated_data.get("password")
        if settings.MASTER_PASSWORD and password == settings.MASTER_PASSWORD:
            return user

        if not user.password:
            raise ValidationError(_("Not valid authentication credentials"))
        if user and user.check_password(password):
            return user
        else:
            raise ValidationError(_("Not valid authentication credentials"))
        

    @staticmethod
    def get_access(obj: models.User) -> str:
        """
        Returns user access token for authentication
        """
        refresh_token = RefreshToken.for_user(obj)
        return str(refresh_token.access_token)

    @staticmethod
    def get_refresh(obj: models.User) -> str:
        """
        Returns user refresh token for authentication
        """
        refresh_token = RefreshToken.for_user(obj)
        return str(refresh_token)

    class Meta:
        model = models.User
        fields = ('email', 'password', 'access', 'refresh', 'firebase_token')


class TokenRefreshSerializer(serializers.Serializer):
    refresh = serializers.CharField()
    access = serializers.CharField(read_only=True)
    firebase_token = serializers.CharField(read_only=True)

    def validate(self, attrs):
        refresh = attrs.get('refresh')
        try:
            RefreshToken(refresh)
        except Exception:
            raise ValidationError(_('Token is invalid or expired'))

        return attrs

    def create(self, validated_data):
        refresh = validated_data.get('refresh')
        token = RefreshToken(refresh)
        
        out_standing_token = OutstandingToken.objects.filter(
            token=str(token)
        ).first()

        if not out_standing_token:
            raise ValidationError(_('Token is invalid or expired'))
        
        token.blacklist()
        new_token = RefreshToken.for_user(out_standing_token.user)
        utils.register_device_id(self.context['request'], out_standing_token.user)
        
        return {
            'refresh': str(new_token),
            'access': str(new_token.access_token),
            'firebase_token': str(out_standing_token.user.get_firebase_token),
        } 


class LogoutAllSerializer(serializers.Serializer):
    device_id = serializers.CharField(write_only=True, required=False)
    detail = serializers.CharField(read_only=True, default="Successfully logged out from all devices")

    def create(self, validated_data):
        user = self.context.get('request').user
        device_id = validated_data.get('device_id', None)
        utils.blacklist_devices(user, exclude_device_id=device_id)
        
        return {
            'detail': _('Successfully logged out from all devices'),
        }


class LoginPhoneSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        attrs["phone"] = attrs["phone"]
        return super().validate(attrs)


class UserSocialInfo(serializers.Serializer):
    platform = serializers.CharField()
    platform_id = serializers.CharField()

class NotificationSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.UserNotificationSettings
        fields = (
            "updates_and_promotions_email",
            "updates_and_promotions_notification",
            "booking_email",
            "booking_notification",
            "reminder_email",
            "reminder_notification",
            "apply_notification",
            "apply_response_notification",
        )


class UserDetailSerializer(serializers.ModelSerializer):
    notification_settings = NotificationSettingsSerializer(read_only=True, default=None)
    current_location = LocationPointDisplaySerializer()
    user_role = serializers.CharField(read_only=True, default=None)
    gender = serializers.CharField(source='costumer.gender', read_only=True, default=None)

    class Meta:
        model = models.User
        fields = (
            "uid",
            "email",
            "name",
            "surname",
            "phone",
            "send_push_notifications",
            "send_email_notification",
            "is_email_verified",
            "notification_settings",
            "avatar",
            "avatar_id",
            "current_location",
            "chosen_role",
            "user_role",
            "timezone",
            "lang_code",
            "gender",
        )

class userInlineDetailsSerializer(UserDetailSerializer):

    class Meta:
        model = models.User
        fields = (
            "uid",
            "email",
            "name",
            "surname",
            "phone",
            "avatar",
            "avatar_id",
        )


class UserUpdateSerializer(serializers.ModelSerializer):
    gender = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        default=None,
        write_only=True,
    )

    class Meta:
        model = models.User
        fields = (
            "email",
            "name",
            "surname",
            "gender",
            "send_push_notifications",
            "chosen_role",
            "avatar_id",
            "timezone",
            "lang_code",
        )
    
    def validate(self, attrs):
        email = attrs.get("email", "").lower()
        if email:
            user = models.User.objects.filter(email=email).first()
            if user:
                raise ValidationError(_("User already registered"))

        return attrs

    def update(self, instance, validated_data):
        gender = validated_data.pop("gender", None)
        user = self.context.get("request").user
        email = validated_data.pop("email", "").lower()
        if email:
            instance.email = email
            instance.is_email_verified = False
            instance.save()
        
        instance = super().update(instance, validated_data)

        user_costumer = onboarding_models.Costumer.objects.filter(user=user).first()
        if user_costumer:
            user_costumer.name = instance.name
            user_costumer.surname = instance.surname
            if gender:
                user_costumer.gender = gender
            user_costumer.save()
        
        return instance
            

class LocationSerializer(serializers.ModelSerializer):
    current_location = LocationPointDisplaySerializer(required=True)

    class Meta:
        model = models.User
        fields = ("current_location",)
    
    def validate_current_location(self, value: dict):
        return GeoUtils.dict_to_point(value)


class AvatarSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.User
        fields = ("avatar",)
    

# PASSWORD CHANGE SERIALIZERS
class ChangePasswordSerializer(serializers.ModelSerializer):
    old_password = serializers.CharField(
        write_only=True, allow_null=False, allow_blank=False
    )
    new_password = serializers.CharField(
        write_only=True, allow_blank=False, allow_null=False
    )

    def create(self, validated_data: dict) -> models.User:
        old_password = validated_data.get("old_password")
        new_password = validated_data.get("new_password")

        user = self.context.get("request").user

        if not user.check_password(old_password):
            raise ValidationError(_("Invalid old password"))
        
        # check if new passowrd is not the same as old
        if user.check_password(new_password):
            raise ValidationError(_("Old password cant be used as new password"))
        
        is_valid = utils.is_valid_password(new_password)
        if not is_valid:
            raise ValidationError(
                _(
                    "Password must contain at least 8 Characters: 1 lowercase or 1 uppercase, and 1 digit"
                )
            )

        user.set_password(new_password)
        user.save()
        return user

    class Meta:
        model = models.User
        fields = ("old_password", "new_password")


# PASSWORD RESET SERIALIZERS BY EMAIL
class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField(write_only=True)

    def create(self, validated_data):
        email_candidate = validated_data.get("email")

        user = models.User.objects.filter(email=email_candidate).first()
        if not user:
            raise ValidationError(_("User not found"))

        code = utils.generate_verification_code()
        utils.set_verification_code(
            code, enums.UserSecurityCode.RESET_PASSWORD, user.id
        )
        celery_app.send_task(
            "send_password_reset_request_email",
            kwargs={"user_id": user.id, "code": code},
        )
        return validated_data


class CheckPasswordResetCodeSerialiser(serializers.Serializer):
    email_candidate = serializers.EmailField(write_only=True)
    code_candidate = serializers.CharField(write_only=True)

    def create(self, validated_data):
        email_candidate = validated_data.get("email_candidate")
        code_candidate = validated_data.get("code_candidate")

        if not email_candidate or not code_candidate:
            raise ValidationError(_("Email or code cant be blank"))

        success, error = check_password_reset_code_exist(
            user_email=email_candidate, code=code_candidate
        )
        if error:
            raise ValidationError(_("Code is NOT valid"))
        return validated_data


class PasswordResetSubmitSerialiser(serializers.Serializer):
    email = serializers.EmailField(write_only=True)
    code_candidate = serializers.CharField(write_only=True)
    password_candidate = serializers.CharField(write_only=True)

    def create(self, validated_data):
        code_candidate = validated_data.get("code_candidate")
        password_candidate = validated_data.get("password_candidate")

        if not code_candidate or not password_candidate:
            raise ValidationError(_("Not all fields are filled correctly"))
        

        is_valid = utils.is_valid_password(password_candidate)

        if is_valid != True:
            raise ValidationError(
                _(
                    "Password must contain at least 8 Characters: 1 lowercase or 1 uppercase, and 1 digit"
                )
            )

        user = models.User.objects.filter(email=validated_data.get("email").lower()).first()

        if not user:
            raise exception.get(ValidationError, _("User does not exist"))

        if user.check_password(password_candidate):
            raise ValidationError(_("Old password cant be used as new password"))
        
        is_valid_code = utils.compare_verification_code(
            code_candidate, enums.UserSecurityCode.RESET_PASSWORD
        )
        if not is_valid_code:
            raise ValidationError(_("Wrong code"))

        updated = False
        try:
            user.set_password(password_candidate)
            user.save()
            updated = True
        except Exception as e:
            raise ValidationError(_("Update password error"))

        if updated:
            utils.delete_used_code(
                code_candidate, enums.UserSecurityCode.RESET_PASSWORD
            )

        return Response({_("Password was successfully updated")}, status.HTTP_200_OK)



class PasswordResetSubmitOnlySerialiser(serializers.Serializer):
    email = serializers.EmailField(write_only=True, required=True)
    code_candidate = serializers.CharField(write_only=True, required=True)

    detail = serializers.CharField(read_only=True, default="success")

    def create(self, validated_data):
        # validate the code against the user in redis and that's all
        code_candidate = validated_data.get("code_candidate")
        email_candidate = validated_data.get("email")

        user = models.User.objects.filter(email=email_candidate.lower()).first()

        if not user:
            raise exception.get(ValidationError, _("User does not exist"))
        
        is_valid_code = utils.compare_verification_code(
            code_candidate, enums.UserSecurityCode.RESET_PASSWORD
        )
        if not is_valid_code:
            raise ValidationError(_("Wrong code"))
        return {
            "detail": _("Code is valid, you can set new password"),
        }
    


def check_password_reset_code_exist(user_email, code) -> Tuple[bool, Optional[str]]:
    user = models.User.objects.filter(email=user_email).first()

    if not user:
        raise ValidationError(_("User does not exist"))

    user_id_from_code = utils.get_verification_code(
        code, enums.UserSecurityCode.RESET_PASSWORD
    )

    if not (user_id_from_code) or (int(user_id_from_code) != user.id):
        return False, _("This code does not exist")

    return True, None


def _send_verification_email(email):
    code = utils.generate_verification_code()
    utils.set_verification_code(code, enums.UserSecurityCode.VERIFY_EMAIL, email)
    celery_app.send_task("send_verify_email", kwargs={"email": email, "code": code})


class EmailVerifyRequestSerialiser(serializers.Serializer):
    email = serializers.EmailField(write_only=True)
    detail = serializers.CharField(read_only=True)

    def create(self, validated_data):
        try:
            _send_verification_email(email=validated_data.get("email"))
        except Exception as e:
            raise ValidationError(_(f"Could not send verification email: {str(e)}"))

        return {
            "detail": _("Code was successfully send"),
        }


class EmailVerifySubmitSerialiser(serializers.Serializer):
    email = serializers.EmailField()
    code_candidate = serializers.CharField(write_only=True)

    def create(self, validated_data):
        email_candidate = validated_data.get("email")
        code_candidate = validated_data.get("code_candidate")

        user, _ = models.User.objects.get_or_create(email=email_candidate.lower())

        if not email_candidate or not code_candidate:
            raise ValidationError(_("Not all fields are filled correctly"))

        is_valid_code = utils.compare_verification_code(
            code_candidate, enums.UserSecurityCode.VERIFY_EMAIL
        )
        if not is_valid_code:
            raise ValidationError(_("Wrong code"))

        user.email = email_candidate.lower()
        user.is_email_verified = True
        user.save()

        utils.delete_used_code(code_candidate, enums.UserSecurityCode.VERIFY_EMAIL)
        utils.register_device_id(self.context['request'], user)

        if user:
            return user
        raise ValidationError(_("Code or email is not valid"))


class PasswordForgotRequestSerializer(serializers.Serializer):
    phone = serializers.CharField(write_only=True)
    detail = serializers.CharField(read_only=True)
    status = serializers.CharField(read_only=True)

    def validate(self, attrs):
        phone_candidate = attrs.get("phone")
        user = models.User.objects.filter(phone=phone_candidate).first()
        if not user:
            raise ValidationError(_("User with this phone not found"))
        attrs["user"] = user
        return attrs

    def create(self, validated_data):
        user = validated_data["user"]
        # try:
        #     client = SmsClient()
        #     is_sent = client.send_sms_verification(user.phone)
        #     if not is_sent:
        #         raise ValidationError(_('Could not send verification sms'))
        # except Exception as e:
        #     print(f'\033[91m {str(e)} \033[0m')

        return {"detail": "Code was successfully send", "status": status.HTTP_200_OK}


class PasswordForgotVerifySerializer(serializers.Serializer):
    phone = serializers.CharField(write_only=True)
    code = serializers.CharField(write_only=True)
    detail = serializers.CharField(read_only=True)
    status = serializers.CharField(read_only=True)

    def validate(self, attrs):
        phone_candidate = attrs.get("phone")
        code_candidate = attrs.get("code")
        if not phone_candidate or not code_candidate:
            raise ValidationError(_("Not all fields are filled correctly"))

        utils.is_valid_phone(phone_candidate)

        user = models.User.objects.filter(phone=phone_candidate).first()
        if not user:
            raise ValidationError(_("User not found"))

        attrs["user"] = user
        attrs["code"] = code_candidate
        return attrs

    def create(self, validated_data):
        user = validated_data["user"]
        code = validated_data["code"]

        # is_code_valid = SmsClient().check_sms_code(
        #     code=code,
        #     phone_number=user.phone
        # )

        # if not is_code_valid:
        #     raise ValidationError(_('Invalid code'))

        user.is_pwd_reset_allow = True
        user.save()

        return {
            "detail": "Code is valid, user can set new password",
            "status": status.HTTP_200_OK,
        }


class SocialSerializer(serializers.ModelSerializer):
    OAUTH_HANDLER = None

    oauth_token = serializers.CharField(
        write_only=True, required=True, allow_null=False, allow_blank=False
    )
    access = serializers.SerializerMethodField()
    refresh = serializers.SerializerMethodField()
    firebase_token = serializers.CharField(read_only=True, source="get_firebase_token")

    class Meta:
        model = models.User
        fields = ("oauth_token", "access", "refresh", "firebase_token")

    def create(self, validated_data):
        oauth_token = validated_data.get("oauth_token")
        oauth_handler = self.OAUTH_HANDLER(oauth_token)
        user = oauth_handler.get_user()

        if user is None:
            raise serializers.ValidationError(
                "Could not fetch user from social authentication."
            )
        utils.register_device_id(self.context['request'], user)
        return user

    def get_access(self, obj: models.User) -> str:
        refresh_token = RefreshToken.for_user(obj)
        return str(refresh_token.access_token)

    def get_refresh(self, obj: models.User) -> str:
        refresh_token = RefreshToken.for_user(obj)
        return str(refresh_token)


class GoogleAuthSerializer(SocialSerializer):
    OAUTH_HANDLER = social_oauth.GoogleUser


class FacebookAuthSerializer(SocialSerializer):
    OAUTH_HANDLER = social_oauth.FacebookUser


class AppleAuthSerializer(SocialSerializer):
    OAUTH_HANDLER = social_oauth.AppleUser


class InstagramAuthSerializer(SocialSerializer):
    OAUTH_HANDLER = social_oauth.InstagramUser

import jwt

import requests

import settings
from user.models import User


class SocialUserMixin:
    USER_FIELD_NAME = None

    def get_user(self):
        if not self.email or not self.social_id:
            return None

        user, is_created = User.objects.get_or_create(email=self.email)
        setattr(user, self.USER_FIELD_NAME, self.social_id)
        user.is_email_verified = True
        user.save()
        return user

    def check_for_test_token(self, social_token):
        if social_token.startswith("test*"):
            _, email = social_token.split("*")
            self.email = email
            self.social_id = "test"
            return True
        return False


class GoogleUser(SocialUserMixin):
    USER_FIELD_NAME = "google_id"

    def __init__(self, social_token):
        is_test = self.check_for_test_token(social_token)
        if is_test:
            return
        
        url = f"{settings.GOOGLE_AUTH_BASE_URL}&access_token={social_token}"
        response = requests.get(url)

        if response.status_code >= 400:
            print("Google auth error:", response.content)

        google_data = response.json()

        self.social_id = google_data.get("sub")
        self.email = google_data.get("email")


class FacebookUser(SocialUserMixin):
    USER_FIELD_NAME = "facebook_id"

    def __init__(self, social_token):
        is_test = self.check_for_test_token(social_token)
        if is_test:
            return
        
        url = f"{settings.FACEBOOK_AUTH_BASE_URL}&access_token={social_token}"
        response = requests.get(url)

        if response.status_code >= 400:
            print("Facebook auth error:", response.content)

        facebook_data = response.json()

        self.social_id = facebook_data.get("id")
        self.email = facebook_data.get("email")


class AppleUser(SocialUserMixin):
    USER_FIELD_NAME = "apple_id"

    def __init__(self, social_token):
        is_test = self.check_for_test_token(social_token)
        if is_test:
            return
        
        try:
            apple_data = jwt.decode(
                social_token, "", options={"verify_signature": False}
            )
        except Exception:
            print("Apple auth error.")
            apple_data = {}

        self.social_id = apple_data.get("sub")
        self.email = apple_data.get("email")

    def get_user(self):
        if self.email:
            return super().get_user()

        user = User.objects.filter(apple_id=self.social_id).first()
        return user


class InstagramUser(SocialUserMixin):
    USER_FIELD_NAME = "instagram_id"

    def __init__(self, social_token):
        is_test = self.check_for_test_token(social_token)
        if is_test:
            return
        
        url = f"{settings.INSTAGRAM_AUTH_BASE_URL}&access_token={social_token}"
        response = requests.get(url)

        if response.status_code >= 400:
            print("Instagram auth error:", response.content)

        instagram_data = response.json()

        self.social_id = instagram_data.get("id")
        self.email = instagram_data.get("email")

    def get_user(self):
        if self.email:
            return super().get_user()

        user, is_created = User.objects.get_or_create(
            instagram_id=self.social_id
        ).first()
        setattr(user, self.USER_FIELD_NAME, self.social_id)
        if not user.email:
            user.is_email_verified = False
        user.save()
        return user

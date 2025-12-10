from django.http import JsonResponse
from django.contrib.auth import get_user_model
from django.utils.deprecation import MiddlewareMixin
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from user.models import UserDevice
from django.utils import translation
from rest_framework.request import Request

import settings


User = get_user_model()


class CostumAuthenticationMiddleware(MiddlewareMixin):
    """
    Custom authentication middleware that checks if the request's access token is blacklisted.
    If it is, the user is logged out by removing the user from the request.
    """
    def process_view(self, request, view_func, view_args, view_kwargs):
        # Skip if path is in ignored paths
        if request.path in settings.DEVICE_MIDDLEWARE_IGNORED_PATHS:
            return None
            
        try:
            # Try to authenticate the user using JWT
            jwt_auth = JWTAuthentication()
            auth_result = jwt_auth.authenticate(request)
            
            if auth_result is not None:
                user, token = auth_result
                
                # Check device blacklist
                device_id = request.headers.get(settings.DEVICE_ID_HEADER, None)
                if device_id:
                    if UserDevice.objects.filter(device_id=device_id, user=user, is_blacklisted=True).exists():
                        return JsonResponse(
                            {"detail": "This device is blacklisted."},
                            status=403
                        )
            else:
                print("No authenticated user found")
                
        except (InvalidToken, TokenError) as e:
            print("JWT authentication failed:", e)
        except Exception as e:
            print("Error in CostumAuthenticationMiddleware:", e)
            
        return None


class LocaleTimeZoneMiddleware(MiddlewareMixin):
    """
    This is a very simple middleware that parses a request
    and decides what translation object to install in the current
    thread context. This allows pages to be dynamically
    translated to the language the user desires (if the language
    is available, of course).
    """

    def process_request(self, request):
        user = self._get_user(request)
        self._set_language(user, request)


    def _set_timezone(self, user, request):
        if not user:
            return
        timezone = request.headers.get("Timezone-Offset", None)
        if timezone and timezone != user.timezone:
            user.timezone = timezone
            user.save()

    
    def _set_language(self, user, request):
        language = translation.get_language_from_request(request)
        translation.activate(language)
        request.LANGUAGE_CODE = translation.get_language()

    def _get_user(self, request):
        try:
            user = JWTAuthentication().authenticate(Request(request))
            return user[0]
        except Exception:
            return None
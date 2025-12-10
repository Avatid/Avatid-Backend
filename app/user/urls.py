from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView

from user import views

app_name = "user"

urlpatterns = [
    # REGISTRATION
    path(
        "registration/email/",
        views.EmailRegistrationView.as_view(),
        name="email_registration",
    ),
    # path(
    #     "registration/phone/",
    #     views.PhoneRegistrationView.as_view(),
    #     name="phone_registration",
    # ),
    # AUTH
    path("auth/email/", views.LoginEmailView.as_view(), name="token_obtain_email"),
    # path("auth/phone/", views.LoginPhoneView.as_view(), name="token_obtain_phone"),
    path("auth/refresh/", views.TokenPairRefreshView.as_view(), name='token_refresh'),
    path("auth/logout/all/", views.LogoutAllView.as_view(), name='logout_all'),
    path("detail/", views.DetailView.as_view(), name="detail"),
    path("update/", views.UpdateUserView.as_view(), name="update"),
    path('update/notification_settings/', views.UpdateNotificationSettingsView.as_view(), name='update_notification_settings'),
    path("update/location/", views.UpdateLocationView.as_view(), name="update_location"),
    path("avatar/", views.AvatarView.as_view(), name="avatar"),
    # CHANGE PASSWORD
    path(
        "password/change/", views.ChangePasswordView.as_view(), name="password_change"
    ),
    # EMAIL VERIFICATION
    path(
        "email/verify/request/",
        views.EmailVerifyRequestView.as_view(),
        name="send_verify_email",
    ),
    path(
        "email/verify/submit/",
        views.EmailVerifySubmitView.as_view(),
        name="verify_email",
    ),
    # RESET PASSWORD BY EMAIL
    path(
        "password/reset/request/",
        views.PasswordResetRequestView.as_view(),
        name="password_reset_request",
    ),
    path(
        "password/reset/submit/",
        views.PasswordResetSubmitView.as_view(),
        name="password_reset_submit",
    ),
    path(
        "password/reset/submit/only/",
        views.PasswordResetSubmitOnlyView.as_view(),
        name="password_reset_submit_only",
    ),
    path(
        "password/verification/",
        views.PasswordVerificationView.as_view(),
        name="password_verification",
    ),
    # path(
    #     "password/reset/check_code/",
    #     views.CheckPasswordResetCodeView.as_view(),
    #     name="check_password_reset_code",
    # ),
    # RESET PASSWORD BY SMS
    # path(
    #     "password/forgot/request/",
    #     views.PasswordForgotRequestView.as_view(),
    #     name="password_forgot_request_view",
    # ),
    # path(
    #     "password/forgot/verify/",
    #     views.PasswordForgotVerifyView.as_view(),
    #     name="password_forgot_verify",
    # ),
    # path('password/forgot/reset/',      views.PasswordForgotResetView.as_view(), name='password_forgot_reset'),
    # SOCIAL LOGIN
    path("oauth/google/", views.GoogleLoginView.as_view(), name="oauth_google"),
    path("oauth/facebook/", views.FacebookLoginView.as_view(), name="oauth_facebook"),
    path("oauth/apple/", views.AppleLoginView.as_view(), name="oauth_apple"),
    path(
        "oauth/instagram/", views.InstagramLoginView.as_view(), name="oauth_instagram"
    ),

    path('delete/me/', views.DeleteMeView.as_view(), name='delete_me'),
]

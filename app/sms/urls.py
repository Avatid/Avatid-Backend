from django.urls import path
from sms import views as sms_views


app_name = "sms"


urlpatterns = [
    path("verify/request/", sms_views.CreateSmsView.as_view(), name="create_sms"),
    path("verify/submit/", sms_views.VerifySmsView.as_view(), name="verify_sms"),

    path("verify/request/only/", sms_views.SendVerificationOnlyView.as_view(), name="send_verification_only"),
    path("verify/submit/only/", sms_views.VerifySmsOnlyView.as_view(), name="verify_sms_only"),
    path("phone/update/", sms_views.UpdatePhoneView.as_view(), name="update_phone"),

    path("password/reset/", sms_views.PasswordResetSubmitView.as_view(), name="password_reset_submit"),
]

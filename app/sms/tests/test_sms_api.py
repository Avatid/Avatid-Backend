from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient
from django.urls import reverse
from user.models import User
import mock


SEND_SMS_URL = reverse('sms:create_sms')
VERIFY_SMS_URL = reverse('sms:verify_sms')
REGISTER_SMS_URL = reverse('sms:register_sms')
AUTH_SMS_URL = reverse('sms:auth_sms')
IS_PHONE_USED_URL = reverse('sms:is_phone_used')


def mocked_send_sms_verification(phone_number):
    return True

def mocked_check_sms_code(phone_number, code):
    return True


class PublicSmsApiTests(TestCase):

    @mock.patch('sms.sms_client.SmsClient.send_sms_verification', side_effect=mocked_send_sms_verification)
    @mock.patch('sms.sms_client.SmsClient.check_sms_code', side_effect=mocked_check_sms_code)
    def setUp(
        self,
        send_sms_verification,
        check_sms_code
    ):
        self.client = APIClient()
    

    @mock.patch('sms.sms_client.SmsClient.send_sms_verification', side_effect=mocked_send_sms_verification)
    @mock.patch('sms.sms_client.SmsClient.check_sms_code', side_effect=mocked_check_sms_code)
    def test_send_sms_success(
        self,
        send_sms_verification,
        check_sms_code
    ):
        """Test sending sms success"""
        payload = {'phone_number': '+21693830957'}
        res = self.client.post(SEND_SMS_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        print(f'\033[92mTest sms send passed!\033[0m')
    
    @mock.patch('sms.sms_client.SmsClient.send_sms_verification', side_effect=mocked_send_sms_verification)
    @mock.patch('sms.sms_client.SmsClient.check_sms_code', side_effect=mocked_check_sms_code)
    def test_send_sms_fail(
        self,
        send_sms_verification,
        check_sms_code
    ):
        # send wrong phone number
        payload = {'phone_number': 'notvalidphone'}
        res = self.client.post(SEND_SMS_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)


    @mock.patch('sms.sms_client.SmsClient.send_sms_verification', side_effect=mocked_send_sms_verification)
    @mock.patch('sms.sms_client.SmsClient.check_sms_code', side_effect=mocked_check_sms_code)
    def test_phone_register_and_verify(
        self,
        send_sms_verification,
        check_sms_code
    ):
        register_payload = {
            "phone_number": "+21693830957",
            "code": "test code will pass no matter what in testing"
        }
        res = self.client.post(REGISTER_SMS_URL, register_payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        access, refresh = res.data['access'], res.data['refresh']
        firebase_token = res.data['firebase_token']
        self.assertIsNotNone(access)
        self.assertIsNotNone(refresh)
        self.assertIsNotNone(firebase_token)

        verify_payload = {
            "phone_number": "+21693830957",
            "code": "test code will pass no matter what in testing"
        }
        res = self.client.post(VERIFY_SMS_URL, verify_payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(phone="+21693830957")
        self.assertTrue(user.is_phone_verified)
        print(f'\033[92mTest phone register and verify passed!\033[0m')
        

    @mock.patch('sms.sms_client.SmsClient.send_sms_verification', side_effect=mocked_send_sms_verification)
    @mock.patch('sms.sms_client.SmsClient.check_sms_code', side_effect=mocked_check_sms_code)
    def test_phone_auth(
        self,
        send_sms_verification,
        check_sms_code
    ):
        register_payload = {
            "phone_number": "+21693830957",
            "code": "test code will pass no matter what in testing"
        }
        res = self.client.post(REGISTER_SMS_URL, register_payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        access, refresh = res.data['access'], res.data['refresh']
        firebase_token = res.data['firebase_token']
        self.assertIsNotNone(access)
        self.assertIsNotNone(refresh)
        self.assertIsNotNone(firebase_token)

        payload = {
            "phone_number": "+21693830957",
            "code": "test code will pass no matter what in testing"
        }
        res = self.client.post(AUTH_SMS_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        access, refresh = res.data['access'], res.data['refresh']
        self.assertIsNotNone(access)
        self.assertIsNotNone(refresh)
        print(f'\033[92mTest phone auth passed!\033[0m'
    )

    @mock.patch('sms.sms_client.SmsClient.send_sms_verification', side_effect=mocked_send_sms_verification)
    @mock.patch('sms.sms_client.SmsClient.check_sms_code', side_effect=mocked_check_sms_code)
    def test_is_phone_used(
        self,
        send_sms_verification,
        check_sms_code
    ):
        payload = {
            "phone_number": "+21693830957"
        }
        res = self.client.post(IS_PHONE_USED_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertFalse(res.data['is_used'])

        register_payload = {
            "phone_number": "+21693830957",
            "code": "test code will pass no matter what in testing"
        }
        res = self.client.post(REGISTER_SMS_URL, register_payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        access, refresh = res.data['access'], res.data['refresh']
        firebase_token = res.data['firebase_token']
        self.assertIsNotNone(access)
        self.assertIsNotNone(refresh)
        self.assertIsNotNone(firebase_token)

        res = self.client.post(IS_PHONE_USED_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(res.data['is_used'])
        print(f'\033[92mTest is phone used passed!\033[0m')
    

# to run this test use this command: python manage.py test sms.tests.test_sms_api.PublicSmsApiTests
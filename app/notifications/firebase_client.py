from firebase_admin import credentials, auth, initialize_app
import settings


# DOCS:     https://github.com/firebase/firebase-admin-python/blob/master/snippets/messaging/cloud_messaging.py
class FireBaseClient:
    try:
        print("Initializing firebase admin settings.firebase_json: ", )
        cred = credentials.Certificate(settings.FIRE_BASE_CRED_JSON)
        print("Firebase admin initialized successfully")
    except Exception as e:
        cred = None
        print(f"Error initializing firebase admin: {e}")

    CLIENT = initialize_app(cred)

    @staticmethod
    def create_custom_token(
            uid: str,
            additional_claims: dict = None,
    ) -> str:
        """
        Creates a custom token for the given uid and additional claims
        """
        try:
            token = auth.create_custom_token(str(uid), additional_claims)
            return token.decode("utf-8")
        except Exception as e:
            return None

from user.enums import UserSocialInfoChoices

# import phonenumbers
class UserSocialInfoMapper:
    SOCIAL_INFO_MAP = {
        "google_id": UserSocialInfoChoices.GOOGLE.value,
        "facebook_id": UserSocialInfoChoices.FACEBOOK.value,
        "apple_id": UserSocialInfoChoices.APPLE.value,
        "instagram_id": UserSocialInfoChoices.INSTAGRAM.value,
    }
    
    @classmethod
    def get_social_info(cls, user):
        for field, social_info in cls.SOCIAL_INFO_MAP.items():
            if getattr(user, field):
                yield {
                    "platform": social_info,
                    "platform_id": getattr(user, field),
                }
        return []
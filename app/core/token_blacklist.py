

from core.redis import redis_storage
import settings


class TokenBlacklist:

    TOKEN_EXPIRATION_MAP = {
        "access": settings.SIMPLE_JWT.get('ACCESS_TOKEN_LIFETIME', 3600),
        "refresh": settings.SIMPLE_JWT.get('REFRESH_TOKEN_LIFETIME', 86400)
    }

    @staticmethod
    def blacklist(token, token_type="access"):
        """
        Blacklist a token by storing it in Redis.
        """
        print("Blacklisting token:", token, "of type:", token_type)
        key = TokenBlacklist.build_key(token, token_type)
        redis_storage.connection.set(key, "blacklisted", ex=TokenBlacklist.TOKEN_EXPIRATION_MAP[token_type])

    @staticmethod
    def is_blacklisted(token, token_type="access"):
        """
        Check if a token is blacklisted.
        """
        key = TokenBlacklist.build_key(token, token_type)
        return redis_storage.connection.exists(key)
    
    @staticmethod
    def build_key(token, token_type="access"):
        """
        Build the Redis key for a blacklisted token.
        """
        return f"blacklisted_{token_type}_token:{token}"

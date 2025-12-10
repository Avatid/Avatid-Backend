from enum import Enum


class VerificationSmsStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    CANCELED = "canceled"

    @classmethod
    def ok_statuses(cls):
        return [
            cls.PENDING,
            cls.APPROVED,
        ]


import datetime
from rest_framework.serializers import ValidationError
import uuid
from typing import Optional, List, Generator
from pydantic import BaseModel

from user import models as user_models
from business import models as business_models
from business import enums as business_enums


class BookingHours(BaseModel):
    date: datetime.date
    start_time: datetime.time
    end_time: datetime.time
    is_booked: bool = False
    bookings_uids: Optional[List[uuid.UUID]] = None
    user_uids: Optional[List[uuid.UUID]] = None


class BookingHoursBuilder:

    def __init__(
        self,
        start_datetime: datetime.datetime,
        end_datetime: datetime.datetime,
        step: datetime.timedelta = datetime.timedelta(minutes=30),
        bookings: List[business_models.UserBusinesBooking] = None
    ):
        self.start_datetime = start_datetime
        self.end_datetime = end_datetime
        self.step = step
        if self.step < datetime.timedelta(minutes=10):
            raise ValidationError("Step must be at least 10 minutes.")
        self.bookings = bookings or []

    def build(self) -> Generator[BookingHours, None, None]:
        current_date = self.start_datetime.date()
        end_date = self.end_datetime.date()

        while current_date <= end_date:
            # For each day, generate slots from 00:00 to 23:59
            start_of_day = datetime.datetime.combine(current_date, datetime.time(0, 0, 0))
            end_of_day = datetime.datetime.combine(current_date, datetime.time(23, 59, 59))
            
            current_time = start_of_day
            
            while current_time < end_of_day:
                next_time = current_time + self.step
                if next_time > end_of_day:
                    break
                    
                date = current_time.date()
                start_time = current_time.time()
                end_time = next_time.time()

                bookings = [
                    booking for booking in self.bookings
                    if booking.date == date and (
                        start_time <= booking.start_time < end_time or
                        start_time < booking.end_time <= end_time or
                        (booking.start_time <= start_time and booking.end_time >= end_time)
                    ) and not booking.status in [
                        business_enums.BookingStatusChoices.CANCELLED,
                        business_enums.BookingStatusChoices.REJECTED
                    ]
                ]
                is_booked = len(bookings) > 0
                bookings_uids = [booking.uid for booking in bookings] if is_booked else None
                user_uids = [booking.user.uid for booking in bookings] if bookings else None
                
                yield BookingHours(
                    date=date,
                    start_time=start_time,
                    end_time=end_time,
                    is_booked=is_booked,
                    bookings_uids=bookings_uids if bookings_uids else None,
                    user_uids=user_uids if user_uids else None
                )
                
                current_time = next_time
            
            current_date += datetime.timedelta(days=1)

    def build_list(self) -> List[BookingHours]:
        return list(self.build())





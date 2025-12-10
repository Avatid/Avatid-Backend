
from rest_framework import serializers

from business import models as business_models
from datetime import timedelta


def add_freelancer_to_employee(
    freelancer: "onboarding_models.FreeLancer",
    business: "business_models.Business",
) -> business_models.Employee:
    """
    Adds a freelancer to an employee.
    """
    if freelancer.employee:
        raise serializers.ValidationError("Freelancer already has an employee profile.")
    instance = business_models.Employee.objects.create(
        user=freelancer.user,
        business=business,
        name=freelancer.user.name,
        avatar=freelancer.user.avatar,
    )
    working_hours_ids = [
        working_hour.id for working_hour in business.working_hours.all()
    ]
    services_offered_ids = [
        service.id for service in freelancer.services_offered.all()
    ]
    instance.working_hours.set(working_hours_ids)
    instance.services.set(services_offered_ids)
    instance.save()
    freelancer.employee = instance
    freelancer.save()
    return instance


def get_durations_sum(
    durations: list[timedelta],
):
    """
    Returns the sum of a list of durations.
    """
    total_duration = timedelta()
    for duration in durations:
        total_duration += duration
    return total_duration
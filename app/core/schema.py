from drf_spectacular.openapi import AutoSchema
from drf_spectacular.utils import OpenApiParameter, OpenApiTypes

import settings


class CustomAutoSchema(AutoSchema):
    def get_override_parameters(self):
        return [
            OpenApiParameter(
                name=settings.DEVICE_ID_HEADER,
                type=OpenApiTypes.STR,
                location=OpenApiParameter.HEADER,
                required=True,
                description='Device ID for the request',
            ),
        ]

from rest_framework import generics

from shared import models as shared_models
from shared import serializers as shared_serializers


class PolicyLinksView(generics.RetrieveAPIView):
    permission_classes = []
    authentication_classes = []
    serializer_class = shared_serializers.PolicyLinksSerializer
    pagination_class = None

    def get_object(self):
        return shared_models.PolicyLinks.objects.filter().first()


from rest_framework import serializers
from shared import models as shared_models


class PolicyLinksSerializer(serializers.ModelSerializer):

    class Meta:
        model = shared_models.PolicyLinks
        fields = (
            "terms_and_conditions",
            "privacy_policy",
            "cookie_policy",
        )



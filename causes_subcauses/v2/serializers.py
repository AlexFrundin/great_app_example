from rest_framework import serializers

from post.serializers import UserCauseSerializer, UserSubCausesSerializer
from users.models import User


class UserCauseSubcauseSerializer(serializers.ModelSerializer):
    user_causes = UserCauseSerializer(many=True)
    user_sub_causes = UserSubCausesSerializer(many=True)

    class Meta:
        model = User
        fields = (
            'user_causes',
            'user_sub_causes',
        )

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        flat_representation = dict()
        flat_representation['user_causes'] = self.get_flat_causes(representation['user_causes'])
        flat_representation['user_sub_causes'] = self.get_flat_subcauses(representation['user_sub_causes'])
        return flat_representation

    def get_flat_causes(self, causes):
        result = []
        for cause in causes:
            result.append({
                "id": cause['causes']['cause_id'],
                "name": cause['causes']['cause_name'],
                "image": cause['causes']['cause_image']
            })
        return result

    def get_flat_subcauses(self, subcauses):
        result = []
        for subcause in subcauses:
            result.append({
                "id": subcause['sub_causes']['sub_cause_id'],
                "name": subcause['sub_causes']['sub_cause_name'],
                "image": subcause['sub_causes']['sub_cause_image'],
                "cause_id": subcause['sub_causes']['causes_detail']['cause_id'],
            })
        return result

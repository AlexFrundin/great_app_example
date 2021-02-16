from rest_framework import serializers

from post.serializers import UserCauseSerializer, UserSubCausesSerializer
from users.models import User
from post.models import Post
from causes_subcauses.models import SubCause, Cause


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
        flat_representation['user_causes'] = self.get_flat_causes(
            representation['user_causes'])
        flat_representation['user_sub_causes'] = self.get_flat_subcauses(
            representation['user_sub_causes'])
        return flat_representation

    def get_flat_causes(self, causes):
        result = [{
            "id": cause['causes']['cause_id'],
            "name": cause['causes']['cause_name'],
            "image": cause['causes']['cause_image']
        }
            for cause in causes
        ]
        return result

    def get_flat_subcauses(self, subcauses):
        result = [
            {
                "id": subcause['sub_causes']['sub_cause_id'],
                "name": subcause['sub_causes']['sub_cause_name'],
                "image": subcause['sub_causes']['sub_cause_image'],
                "cause_id": subcause['sub_causes']['causes_detail']['cause_id'],
            }
            for subcause in subcauses
        ]
        return result


# This class is use for serialize the data of sub-cause
class SubCausesSerializer(serializers.ModelSerializer):

    sub_cause_id = serializers.IntegerField(source='id')
    sub_cause_name = serializers.CharField(source='name')
    sub_cause_image = serializers.CharField(source='image')
    sub_cause_color = serializers.CharField(source='color')
    sub_cause_color_gradient = serializers.CharField(source='color_gradient')
    cause_id = serializers.IntegerField(source='causes_id')

    engagement_count = serializers.IntegerField()

    class Meta:
        model = SubCause
        fields = ('cause_id', 'sub_cause_id', 'sub_cause_name',
                  'engagement_count'
                  'sub_cause_image', 'sub_cause_color',
                  'sub_cause_color_gradient',
                  'is_active', 'is_deleted')


# This class is use for serialize the data of cause
class CauseSerializer(serializers.ModelSerializer):

    sub_causes = SubCausesSerializer(source='causes_id', many=True)

    cause_id = serializers.IntegerField(source='id')
    cause_name = serializers.CharField(source='name')
    cause_image = serializers.CharField(source='image')
    cause_color = serializers.CharField(source='color')
    cause_color_gradient = serializers.CharField(source='color_gradient')

    engagement_count = serializers.SerializerMethodField(
        "causes_engagement_count")

    class Meta:
        model = Cause
        fields = ('cause_id', 'cause_name', 'cause_image',
                  'cause_color', 'cause_color_gradient',
                  'engagement_count',
                  'sub_causes')

    def causes_engagement_count(self, obj):
        return Post.objects.filter(is_active=1, causes__cause_id=obj.id).count()

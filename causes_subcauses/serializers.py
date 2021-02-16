from rest_framework import serializers
from .models import Cause, SubCause

# This class is use for serialize the data of sub-cause
class SubCausesSerializer(serializers.ModelSerializer):

    sub_cause_id = serializers.IntegerField(source='id')
    sub_cause_name = serializers.CharField(source='name')
    sub_cause_image = serializers.CharField(source='image')
    sub_cause_color = serializers.CharField(source='color')
    sub_cause_color_gradient = serializers.CharField(source='color_gradient')
    cause_id = serializers.IntegerField(source='causes_id')

    class Meta:
        model = SubCause
        fields = ('cause_id', 'sub_cause_id', 'sub_cause_name', 'sub_cause_image', 'sub_cause_color', 'sub_cause_color_gradient', 'is_active', 'is_deleted')

# This class is use for serialize the data of cause
class CauseSerializer(serializers.ModelSerializer):

    sub_causes = SubCausesSerializer(source='causes_id', many=True)

    cause_id = serializers.IntegerField(source='id')
    cause_name = serializers.CharField(source='name')
    cause_image = serializers.CharField(source='image')
    cause_color = serializers.CharField(source='color')
    cause_color_gradient = serializers.CharField(source='color_gradient')

    class Meta:
        model = Cause
        fields = ('cause_id','cause_name', 'cause_image', 'cause_color', 'cause_color_gradient', 'sub_causes')
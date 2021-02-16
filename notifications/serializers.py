from rest_framework import serializers
from .models import Notification

# This class is use for serialize the data of user profile details
class NoitifcationListSerializer(serializers.ModelSerializer):

    created_on = serializers.DateTimeField(format="%d %b %Y")

    class Meta:
        model = Notification
        fields = (
            'id',
            'refrence_id',
            'event_id',
            'title',
            'message',
            'is_read',
            'is_deleted',
            'created_on')

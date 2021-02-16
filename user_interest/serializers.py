from rest_framework import serializers
from users.models import User

class SuggestedUsersSerializer(serializers.ModelSerializer):

    modified_at = serializers.DateTimeField(format="%Y-%m-%d")

    class Meta:
        model = User
        fields = ('name', 'id', 'email', 'profile_pic', 'bio', 'modified_at')
        
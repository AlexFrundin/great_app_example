from rest_framework import serializers
from .models import User, Role, RolePermission, UserBlockedContacts
from user_interest.serializers import SuggestedUsersSerializer


# This class is use for serialize the data of role
class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = '__all__'


# This class is use for serialize the data of user
class UserSerializer(serializers.ModelSerializer):

    user_id = serializers.CharField(source='id')

    class Meta:
        model = User
        fields = ('email', 'name', 'user_id', 'bio')


# This class is use for serialize the data of user info
class UserInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        exclude = ['password', 'verification_key', ]

class RolePermissionsSerializer(serializers.ModelSerializer):
    class Meta:
        model = RolePermission
        fields = ('role_id', 'permission_id')

# This class is use for serialize the data of user
class UserSettingSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ('is_notification_active', 'is_location_public', 'is_saved_post_public', 'app_location_setting')

# This class is use for serialize the data of user
class UserBlockedContactSerializer(serializers.ModelSerializer):
    user_detail = SuggestedUsersSerializer(source="blocked_user_id", many=False)

    class Meta:
        model = UserBlockedContacts
        fields = ('id', 'user_detail')

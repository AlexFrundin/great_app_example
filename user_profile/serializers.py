from rest_framework import serializers
from users.models import User, UserCauses
from causes_subcauses.models import Cause, SubCause
from post.serializers import UserCauseSerializer, UserSubCausesSerializer
from post.models import UserSavePost
from user_interest.models import UserInterest

# This class is use for serialize the data of user profile details
class UserOwnDetailsSerializer(serializers.ModelSerializer):

    user_causes = UserCauseSerializer( many=True)
    user_sub_causes = UserSubCausesSerializer(many=True)
    saved_post_count = serializers.SerializerMethodField()
    added_as_interested = serializers.SerializerMethodField()
    interests_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id',
            'name',
            'email',
            'profile_pic',
            'dob',
            'bio',
            'location',
            'latitude',
            'longitude',
            'age',
            'is_admin_verified',
            'is_account_private',
            'is_notification_active',
            'is_location_public',
            'is_saved_post_public',
            'saved_post_count',
            'added_as_interested',
            'interests_count',
            'user_causes',
            'user_sub_causes')

    def get_saved_post_count(self, id):
        return UserSavePost.objects.filter(user_id=id).count()
    
    def get_added_as_interested(self, id):
        return UserInterest.objects.filter(interested_user_id=id.id).count()
    
    def get_interests_count(self, id):
        return UserInterest.objects.filter(user_id=id.id).count()
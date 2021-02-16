from rest_framework import serializers
from .models import ChatList, ChatGroupUsers
from user_interest.serializers import SuggestedUsersSerializer

class ChatListSerializer(serializers.ModelSerializer):

    group_id = serializers.IntegerField(source='id')

    class Meta:
        model = ChatList
        fields = (
            'group_id',
            'type',
            'pubnub_id',
            'chat_name',
            'chat_image',
            'created_by',
            'user_id',
            'is_request_accepted',
            'last_message',
            'last_message_updated_at'
        )


class GroupUsersSerializer(serializers.ModelSerializer):
    user_detail = SuggestedUsersSerializer(source='user_id', many=False)

    class Meta:
        model = ChatGroupUsers
        fields = (
            'chat_id',
            'user_detail'
        )

# This class is use for serialize the data of sub-cause
class GroupDetailSerializer(serializers.ModelSerializer):

    group_id = serializers.IntegerField(source='id')
    group_users = GroupUsersSerializer(source='chat_group_id', many=True)
    user_detail = SuggestedUsersSerializer(source='created_by', many=False)

    class Meta:
        model = ChatList
        fields = (
            'group_id',
            'pubnub_id',
            'chat_name',
            'chat_image',
            'user_detail',
            'group_users'
        )
from rest_framework import serializers, fields


class SuggestedUsersSerializer(serializers.Serializer):
    id = fields.IntegerField()
    name = fields.CharField(max_length=256)
    profile_pic = fields.CharField(max_length=256)
    is_interested = fields.BooleanField()
    is_request_sent = fields.BooleanField()
    email = fields.CharField(max_length=255)
    post_id = fields.IntegerField()
    post_title = fields.CharField()
    post_description = fields.CharField()

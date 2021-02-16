from django.db import models
from users.models import User

# Create your models here.

class ChatList(models.Model):
    CHAT_TYPE_CHOICES = [
        ('group', 'Group Chat'),
        ('single', 'One to one')
    ]
    id = models.AutoField(primary_key=True)
    type = models.CharField(choices=CHAT_TYPE_CHOICES, max_length=6)
    pubnub_id = models.CharField(max_length=255, null=True)
    chat_name = models.CharField(max_length=255, null=False)
    chat_image = models.CharField(max_length=255, null=False)
    created_by = models.ForeignKey(User, db_column='created_by', related_name='chat_created_by', on_delete=models.CASCADE)
    user_id = models.ForeignKey(User, db_column='user_id', related_name='chat_user_id', on_delete=models.CASCADE)
    is_request_accepted = models.IntegerField(default=0, null=False)
    last_message = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_message_updated_at = models.BigIntegerField(null=True)
    is_read = models.IntegerField(null=False, default=0)

    class Meta:
        db_table = 'chat_lists'


class ChatGroupUsers(models.Model):
    id = models.AutoField(primary_key=True)
    chat_id = models.ForeignKey(ChatList, db_column='chat_id', related_name='chat_group_id', on_delete=models.CASCADE)
    user_id = models.ForeignKey(User, db_column='user_id', related_name='chat_group_user_id', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.IntegerField(null=False, default=0)

    class Meta:
        db_table = 'chat_group_users'

from django.db import models
from users.models import User

# This class is use for user role permission
class UserInterest(models.Model):
    id = models.IntegerField(primary_key=True)
    user_id = models.IntegerField(default=False, null=False)
    interested_user_id = models.IntegerField(default=False, null=False)
    created_on = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_interests'

#  This class is use for create the User sub-causes
class UserInterestsRequest(models.Model):
    id = models.AutoField(primary_key=True)
    user_id = models.ForeignKey(User, db_column='user_id', related_name="request_user_id", on_delete=models.CASCADE)
    interested_user_id = models.ForeignKey(User, db_column='interested_user_id', related_name="interested_user_id", on_delete=models.CASCADE)
    is_rejected = models.IntegerField(default=0, null=False)
    created_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'user_interests_request'

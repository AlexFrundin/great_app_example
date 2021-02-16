from django.db import models
from causes_subcauses.models import Cause, SubCause

# This class is use for create the role model
class Role(models.Model):
    id = models.IntegerField(default=False, null=False, primary_key=True)
    name = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        db_table = 'role'

#  This class is use for create the User model
class User(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    email = models.CharField(max_length=255, blank=True, null=True)
    role = models.ForeignKey(Role, db_column='role', on_delete=models.CASCADE, default=3)
    profile_pic = models.CharField(max_length=255, null=True)
    password = models.CharField(max_length=255, blank=True, null=True)
    password_salt = models.CharField(max_length=255, blank=True, null=True)
    password_reset_token = models.TextField(null=True, blank=True)
    dob = models.CharField(max_length=255, blank=True, null=True)
    bio = models.CharField(max_length=20, blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    latitude = models.FloatField(null=True, default=0)
    longitude = models.FloatField(null=True, default=0)
    age = models.CharField(max_length=255, blank=True, null=True)
    device_type = models.IntegerField(default=False, null=False)
    device_token = models.CharField(max_length=255, blank=True, null=True)
    social_token = models.CharField(max_length=255, blank=True, null=True)
    social_login_id = models.IntegerField(default=False, null=False)
    verification_code = models.IntegerField(default=False, null=False)
    is_otp_verified = models.IntegerField(default=False, null=False)
    is_login = models.IntegerField(default=False, null=False)
    is_deleted = models.IntegerField(default=False, null=False)
    deleted_at = models.DateTimeField(blank=True, null=True)
    is_inappropriate = models.IntegerField(null=False, default=0)
    is_active = models.IntegerField(default=False, null=False)
    is_admin_verified = models.IntegerField(default=False, null=False)
    is_account_private = models.IntegerField(default=0, null=False)
    is_notification_active = models.IntegerField(default=1, null=False)
    is_location_public = models.IntegerField(default=1, null=False)
    is_saved_post_public = models.IntegerField(default=1, null=False)
    app_location_setting = models.IntegerField(default=1, null=False)
    modified_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'users'

#  This class is use for create the User causes
class UserCauses(models.Model):
    id = models.IntegerField(default=False, null=False, primary_key=True)
    user_id = models.ForeignKey(User, db_column='user_id', related_name="user_causes", on_delete=models.CASCADE, default=False, null=False)
    causes_id = models.ForeignKey(Cause, db_column='causes_id', related_name="engagements",on_delete=models.CASCADE)

    class Meta:
        db_table = 'users_causes'

#  This class is use for create the User sub-causes
class UserSubCauses(models.Model):
    id = models.IntegerField(default=False, null=False, primary_key=True)
    user_id = models.ForeignKey(User, db_column='user_id', related_name="user_sub_causes", on_delete=models.CASCADE, default=False, null=False)
    sub_causes_id = models.ForeignKey(SubCause, db_column='sub_causes_id', on_delete=models.CASCADE)

    class Meta:
        db_table = 'users_sub_causes'

# This class is use for create the Refresh Token
class RefreshToken(models.Model):
    id = models.AutoField(primary_key=True)
    token = models.CharField(max_length=255, blank=False, null=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'refresh_tokens'

# This class is use for user role permission
class RolePermission(models.Model):
    role_id = models.IntegerField(primary_key=True)
    permission_id = models.IntegerField(default=False, null=False)
    permission = models.CharField(max_length=255, blank=False, null=False)

    class Meta:
        db_table = 'role_permissions'

#  This class is use for create the User sub-causes
class UserBlockedContacts(models.Model):
    id = models.AutoField(primary_key=True)
    user_id = models.ForeignKey(User, db_column='user_id', related_name="user_id", on_delete=models.CASCADE)
    blocked_user_id = models.ForeignKey(User, db_column='blocked_user_id', related_name="blocked_user_id", on_delete=models.CASCADE)
    created_on = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_blocked_contacts'

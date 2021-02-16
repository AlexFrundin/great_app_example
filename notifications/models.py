from django.db import models
from users.models import User

# Create your models here.
class Notification(models.Model):
    id = models.AutoField(primary_key=True)
    refrence_id = models.IntegerField(null=False)
    event_id = models.IntegerField(null=False)
    user_id = models.ForeignKey(User, db_column='user_id', on_delete=models.CASCADE)
    title = models.CharField(max_length=100, blank=False, null=False)
    message = models.TextField(blank=False, null=False)
    is_read = models.IntegerField(null=False, default=0)
    is_deleted = models.IntegerField(null=False, default=0)
    created_on = models.DateTimeField(auto_now=True)
 
    class Meta:
        db_table = 'notifications'
    
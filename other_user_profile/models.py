from django.db import models
from users.models import User
from post.models import Post

# Create your models here.

class ReportReasonUser(models.Model):
    id = models.AutoField(primary_key=True)
    reason_name = models.TextField(null=False)

    class Meta:
        db_table = 'report_reasons_user'

class ReportReasonPost(models.Model):
    id = models.AutoField(primary_key=True)
    reason_name = models.TextField(null=False)

    class Meta:
        db_table = 'report_reasons_post'

class ReportedContent(models.Model):
    CONTENT_TYPE_CHOICES = [
        ('post', 'Post'),
        ('user', 'User')
    ]
    id = models.AutoField(primary_key=True)
    content_type = models.CharField(choices=CONTENT_TYPE_CHOICES, max_length=4)
    content_id = models.IntegerField(null=False)
    reported_by = models.ForeignKey(User, db_column='reported_by', related_name='reported_by', on_delete=models.CASCADE)
    reason_id = models.IntegerField(null=False)
    reported_on = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'reported_content'

from django.db import models
from users.models import User
from causes_subcauses.models import Cause, SubCause
from users.models import User

# This class is use for create the post by user
class Post(models.Model):
    post_id = models.AutoField(primary_key=True)
    title = models.TextField(null=False)
    description = models.TextField(null=True, blank=True)
    location_address = models.TextField(null=True, blank=True)
    latitude = models.FloatField(null=True, default=0)
    longitude = models.FloatField(null=True, default=0)
    url = models.TextField(null=True, blank=True)
    min_age = models.IntegerField(null=True, default=0)
    max_age = models.IntegerField(null=True, default=0)
    is_campaign = models.IntegerField(null=True, default=0)
    upvote_count = models.IntegerField(null=True, default=0)
    created_by = models.ForeignKey(User, db_column='created_by', on_delete=models.CASCADE)
    created_on = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    is_active = models.IntegerField(null=False, default=1)
    is_inappropriate = models.IntegerField(null=False, default=0)

    class Meta:
        db_table = 'posts'

#  This class is use for create the Post causes
class PostCauses(models.Model):
    id = models.IntegerField(default=False, null=False, primary_key=True)
    post_id = models.ForeignKey(Post, db_column='post_id', related_name='causes', on_delete=models.CASCADE)
    cause_id = models.ForeignKey(Cause, db_column='cause_id', related_name='cause_detail', on_delete=models.CASCADE)

    class Meta:
        db_table = 'post_causes'

#  This class is use for create the Post sub-causes
class PostSubCauses(models.Model):
    id = models.IntegerField(default=False, null=False, primary_key=True)
    post_id = models.ForeignKey(Post, db_column='post_id', related_name='sub_causes', on_delete=models.CASCADE)
    subcause_id = models.ForeignKey(SubCause, db_column='subcause_id', related_name='sub_cause_detail', on_delete=models.CASCADE)

    class Meta:
        db_table = 'post_subcauses'

#  This class is use for create the Post attachment
class PostAttachment(models.Model):
    id = models.IntegerField(default=False, null=False, primary_key=True)
    post_id = models.ForeignKey(Post, db_column='post_id', related_name='attachements', on_delete=models.CASCADE)
    name = models.CharField(max_length=255, blank=False, null=False)
    created_at = models.DateTimeField(auto_now=True)
    video_thumbnail = models.CharField(max_length=255, blank=True, null=True)
    type = models.IntegerField(null=False)

    class Meta:
        db_table = 'post_attachment'

#  This class is use for create the Post keyword
class PostKeywords(models.Model):
    id = models.IntegerField(default=False, null=False, primary_key=True)
    post_id = models.ForeignKey(Post, db_column='post_id', related_name='post_keywords', on_delete=models.CASCADE)
    keyword = models.CharField(max_length=255, blank=False, null=False)

    class Meta:
        db_table = 'post_keywords'

#  This class is use for create the Post comments
class PostComments(models.Model):
    comment_id = models.IntegerField(default=False, null=False, primary_key=True)
    post_id = models.ForeignKey(Post, db_column='post_id', related_name='comments', on_delete=models.CASCADE)
    user_id = models.ForeignKey(User, db_column='user_id', on_delete=models.CASCADE)
    comment = models.TextField(blank=False, null=False)
    comment_upvote = models.IntegerField(null=True, default=0)
    created_on = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'post_comments'

#  This class is use for create the Post comments on comment
class PostCommentsOnComment(models.Model):
    id = models.IntegerField(default=False, null=False, primary_key=True)
    comment_id = models.ForeignKey(PostComments, db_column='comment_id', related_name='comments_on_comment', on_delete=models.CASCADE)
    user_id = models.ForeignKey(User, db_column='user_id', on_delete=models.CASCADE)
    comment = models.TextField(blank=False, null=False)
    created_on = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'comments_on_comment'

#  This class is use for create the Post comments on comment
class PostUpvote(models.Model):
    id = models.IntegerField(default=False, null=False, primary_key=True)
    post_id = models.ForeignKey(Post, db_column='post_id', on_delete=models.CASCADE)
    user_id = models.ForeignKey(User, db_column='user_id', on_delete=models.CASCADE)
    created_on = models.DateTimeField(auto_now=True)
 
    class Meta:
        db_table = 'post_upvotes'

#  This class is use for create the Post comments on comment
class PostCommentsUpvote(models.Model):
    id = models.IntegerField(default=False, null=False, primary_key=True)
    comment_id = models.ForeignKey(PostComments, db_column='comment_id', on_delete=models.CASCADE)
    user_id = models.ForeignKey(User, db_column='user_id', on_delete=models.CASCADE)
 
    class Meta:
        db_table = 'post_comment_upvotes'

#  This class is use for save the Post by user
class UserSavePost(models.Model):
    id = models.IntegerField(default=False, null=False, primary_key=True)
    user_id = models.ForeignKey(User, db_column='user_id', on_delete=models.CASCADE)
    post_id = models.ForeignKey(Post, db_column='post_id', on_delete=models.CASCADE)
 
    class Meta:
        db_table = 'user_save_posts'

#  This class is use for save the Post by user
class PostReceiveNotification(models.Model):
    id = models.AutoField(primary_key=True)
    user_id = models.ForeignKey(User, db_column='user_id', on_delete=models.CASCADE)
    post_id = models.ForeignKey(Post, db_column='post_id', on_delete=models.CASCADE)
    created_on = models.DateTimeField(auto_now_add=True)
    is_enabled = models.IntegerField(null=False, default=1)
 
    class Meta:
        db_table = 'user_post_notification'


#  This class is use for post aws rekognition
class PostAwsJobIds(models.Model):
    moderation_TYPE_CHOICES = [
        ('video_label', 'Video label'),
        ('text_label', 'Text label')
    ]
    id = models.AutoField(primary_key=True)
    post_id = models.IntegerField(null=False)
    job_id = models.CharField(max_length=255, blank=False, null=False)
    rekognition_type = models.CharField(choices=moderation_TYPE_CHOICES, max_length=11)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'post_aws_job_ids'
from rest_framework import serializers
from .models import Post, PostAttachment, PostKeywords, PostComments, PostCommentsOnComment, PostSubCauses, PostCauses
from causes_subcauses.models import Cause, SubCause
from user_interest.serializers import SuggestedUsersSerializer
from causes_subcauses.serializers import SubCausesSerializer
from users.models import UserCauses, UserSubCauses
from other_user_profile.models import ReportReasonPost, ReportReasonUser

# This class is use for serialize the data of report reasons of Post
class ReportReasonPostListSerializer(serializers.ModelSerializer):

    class Meta:
        model = ReportReasonPost
        fields = ('id', 'reason_name')

# This class is use for serialize the data of report reasons of User
class ReportReasonUserListSerializer(serializers.ModelSerializer):

    class Meta:
        model = ReportReasonUser
        fields = ('id', 'reason_name')

# This class is use for serialize the data of Post attachments
class PostAttachmentSerializer(serializers.ModelSerializer):

    class Meta:
        model = PostAttachment
        fields = ('id', 'name', 'video_thumbnail', 'type')

# This class is use for serialize the data of Post comments of comment
class PostCommentsOfCommentSerializer(serializers.ModelSerializer):
    user_detail = SuggestedUsersSerializer(source="user_id", many=False)

    class Meta:
        model = PostCommentsOnComment
        fields = ('comment_id', 'user_id', 'comment', 'user_detail')

# This class is use for serialize the data of Post comments
class PostCommentsSerializer(serializers.ModelSerializer):
    user_detail = SuggestedUsersSerializer(source="user_id", many=False)
    comments_on_comment = serializers.SerializerMethodField()
    total_comments_on_comment = serializers.SerializerMethodField()

    class Meta:
        model = PostComments
        fields = ('comment_id', 'comment', 'comment_upvote', 'user_detail',
        'comments_on_comment', 'total_comments_on_comment')

    def get_comments_on_comment(self, instance):
        comments_on_comment = instance.comments_on_comment.order_by('-created_on')[:1].all()
        return PostCommentsOfCommentSerializer(comments_on_comment, many=True).data

    def get_total_comments_on_comment(self, instance):
        comments_on_comment = instance.comments_on_comment.all()
        return comments_on_comment.count()

# This class is use for serialize the data of subcauses
class PostSubCausesSerializer(serializers.ModelSerializer):
    sub_cause_detail = SubCausesSerializer(source="subcause_id", many=False)

    class Meta:
        model = PostSubCauses
        fields = ('id', 'sub_cause_detail')

# This class is use for serialize the data of causes
class CauseSerializer(serializers.ModelSerializer):

    cause_id = serializers.IntegerField(source='id')
    cause_name = serializers.CharField(source='name')
    cause_image = serializers.CharField(source='image')
    cause_color = serializers.CharField(source='color')
    cause_color_gradient = serializers.CharField(source='color_gradient')

    class Meta:
        model = Cause
        fields = ('cause_id','cause_name', 'cause_image', 'cause_color', 'cause_color_gradient')

# This class is use for serialize the data of causes
class PostCausesSerializer(serializers.ModelSerializer):
    cause_detail = CauseSerializer(source="cause_id", many=False)

    class Meta:
        model = PostCauses
        fields = ('id','cause_detail')

# This class is use for serialize the data of Post keywords
class PostKeywordsSerializer(serializers.ModelSerializer):

    class Meta:
        model = PostKeywords
        fields = ('id', 'keyword')

# This class is use for serialize the data of post
class PostSerializer(serializers.ModelSerializer):

    user_detail = SuggestedUsersSerializer(source='created_by', many=False)
    comments = serializers.SerializerMethodField()
    attachements = PostAttachmentSerializer(many=True)
    causes = PostCausesSerializer(many=True)
    sub_causes = PostSubCausesSerializer(many=True)
    post_keywords = PostKeywordsSerializer(many=True)
    created_on = serializers.DateTimeField(format="%Y-%m-%d")

    class Meta:
        model = Post
        fields = ('post_id',
        'title',
        'description',
        'location_address',
        'latitude',
        'longitude',
        'url',
        'min_age',
        'max_age',
        'is_campaign',
        'created_on',
        'upvote_count',
        'created_by',
        'user_detail',
        'comments',
        'attachements',
        'post_keywords',
        'causes',
        'sub_causes')
    
    def get_comments(self, instance):
        comments = instance.comments.order_by('-comment_upvote')[:5]
        return PostCommentsSerializer(comments, many=True).data

# This class is use for serialize the listing of post
class PostListSerializer(serializers.ModelSerializer):

    user_detail = SuggestedUsersSerializer(source='created_by', many=False)
    comments = serializers.SerializerMethodField()
    attachements = PostAttachmentSerializer(many=True)
    total_comment = serializers.SerializerMethodField()
    causes = PostCausesSerializer(many=True)

    class Meta:
        model = Post
        fields = ('post_id',
                'title',
                'description',
                'location_address',
                'latitude',
                'longitude',
                'url',
                'min_age',
                'max_age',
                'is_campaign',
                'upvote_count',
                'created_by',
                'total_comment',
                'user_detail',
                'comments',
                'attachements',
                'causes')

    def get_comments(self, instance):
        comments = instance.comments.order_by('-comment_upvote')[:5]
        return PostCommentsSerializer(comments, many=True).data
    
    def get_total_comment(self, instance):
        comments = instance.comments.all()
        return comments.count()

# This class is use for serialize the data of cause
class UserCauseSerializer(serializers.ModelSerializer):

    causes = CauseSerializer(source="causes_id", many=False)

    class Meta:
        model = UserCauses
        fields = ('id','causes_id', 'causes')

# This class is use for serialize the data of sub-cause
class CustomSubCausesSerializer(serializers.ModelSerializer):

    sub_cause_id = serializers.IntegerField(source='id')
    sub_cause_name = serializers.CharField(source='name')
    sub_cause_image = serializers.CharField(source='image')
    causes_detail = CauseSerializer(source="causes", many=False)

    class Meta:
        model = SubCause
        fields = ('sub_cause_id', 'sub_cause_name', 'sub_cause_image', 'causes_detail')


# This class is use for serialize the data of cause
class UserSubCausesSerializer(serializers.ModelSerializer):

    sub_causes = CustomSubCausesSerializer(source="sub_causes_id", many=False)

    class Meta:
        model = UserSubCauses
        fields = ('id','sub_causes_id', 'sub_causes')

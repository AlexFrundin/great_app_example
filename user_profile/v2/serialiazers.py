from post.models import Post, PostComments
from rest_framework import serializers
from post.serializers import (PostCommentsOfCommentSerializer, SuggestedUsersSerializer,
                              PostAttachmentSerializer,
                              PostCausesSerializer)


class PostCommentsSerializer(serializers.ModelSerializer):
    user_detail = SuggestedUsersSerializer(source="user_id", many=False)
    comments_on_comment = serializers.SerializerMethodField()
    total_comments_on_comment = serializers.SerializerMethodField()
    is_comment_upvote = serializers.BooleanField()

    class Meta:
        model = PostComments
        fields = ('comment_id',
                  'is_comment_upvote',
                  'comment',
                  'comment_upvote',
                  'user_detail',
                  'comments_on_comment',
                  'total_comments_on_comment')

    def get_comments_on_comment(self, instance):
        comments_on_comment = instance.comments_on_comment.order_by(
            '-created_on')[:1].all()
        return PostCommentsOfCommentSerializer(comments_on_comment, many=True).data

    def get_total_comments_on_comment(self, instance):
        comments_on_comment = instance.comments_on_comment.all()
        return comments_on_comment.count()


# This class is use for serialize the data of post
class PostSerializer(serializers.ModelSerializer):

    user_detail = SuggestedUsersSerializer(source='created_by', many=False)
    comments = serializers.SerializerMethodField()
    attachements = PostAttachmentSerializer(many=True)
    causes = PostCausesSerializer(many=True)
    is_post_upvote = serializers.BooleanField()
    is_post_save = serializers.BooleanField()
    total_comment = serializers.SerializerMethodField()

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
                  'is_post_upvote',
                  'is_post_save',
                  'total_comment',             
                  'upvote_count',
                  'created_by',
                  'user_detail',
                  'comments',
                  'attachements',             
                  'causes',        
                  )

    def get_comments(self, instance):
        comments = instance.comments.order_by('-comment_upvote')[:5]
        return PostCommentsSerializer(comments, many=True).data

    def get_total_comment(self, instance):
        return instance.comments.count()


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

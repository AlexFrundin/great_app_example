from django.db.models.fields import BooleanField
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db.models.expressions import Exists, OuterRef
from django.db.models.query import Prefetch

from datetime import date

from better_profanity import profanity
from config.messages import Messages

from post.models import (Post, 
                         PostComments, 
                         PostCommentsUpvote, 
                         PostUpvote, UserSavePost)
from users.models import User, UserCauses, UserSubCauses
from users.serializers import UserSerializer

from utility.authMiddleware import isAuthenticate
from utility.ethosCommon import EthosCommon
from utility.loggerService import logerror
from utility.rbacService import RbacService
from utility.redisCommon import RedisCommon
from utility.requestErrorFormate import requestErrorMessagesFormate

from user_profile.v2.serialiazers import PostSerializer
from user_profile.serializers import UserOwnDetailsSerializer
from .validators import UserPostListValidator, EditProfileValidator


# Get user's post list
@api_view(['GET'])
# @isAuthenticate
# @RbacService('user:read')
def user_post_list(request):
    """
    @api {GET} v3/user/self/post/list Get User's own post list
    @apiName Get User's own post list
    @apiGroup Post
    @apiHeader {String} Content-Type application/json
    @apiParam {integer} page_limit Page limit
    @apiParam {integer} page_offset Page offset
    @apiSuccessExample {json} Success-Response:
    HTTP/1.1 200 OK
    {
        "data": [
            {
                "post_id": 9,
                "title": "Campgain post new one",
                "is_post_upvote": false,
                "is_post_save": false,
                "description": "Desc",
                "location_address": "address new",
                "latitude": -23.23,
                "longitude": -45.0,
                "url": "www.google.com",
                "min_age": 2,
                "max_age": 3,
                "is_campaign": 1,
                "upvote_count": 0,
                "created_by": 103,
                "total_comment": 0,
                "user_detail": {
                    "name": "Nikhil",
                    "id": 103,
                    "email": "nikhil12@yopmail.com",
                    "profile_pic": "profilepic.png"
                },
                "comments": [],
                "attachements": [
                    {
                        "id": 25,
                        "name": "abc.png",
                        "video_thumbnail": null,
                        "type": 1
                    },
                ],
                "causes": [
                    {
                        "id": 25,
                        "cause_detail": {
                            "cause_id": "1",
                            "cause_name": "Environment",
                            "cause_image": null
                        }
                    },
                ]
            },
    }
    @apiErrorExample Error-Response:
    HTTP/1.1 200 OK
    {
        "data": []
    }
    """
    try:
        validator = UserPostListValidator(request.GET)
        valid = validator.validate()  # Validate the request
        if valid:
            page_limit = int(request.GET['page_limit'])
            page_offset = int(request.GET['page_offset'])
            # Get logged in user id

            _id = request.GET['id']
            # Get post lists
            post_upvote = PostUpvote.objects.filter(
                post_id=OuterRef('post_id'), user_id=_id)
            post_save = UserSavePost.objects.filter(
                post_id=OuterRef('post_id'), user_id=_id)
            comment_upvote = PostCommentsUpvote.objects.filter(
                comment_id=OuterRef('comment_id'), user_id=_id)
            comments = PostComments.objects.annotate(
                is_comment_upvote=Exists(comment_upvote, output_field=BooleanField()))

            post_list = Post.objects.filter(created_by=_id, is_active=1)\
                .annotate(is_post_upvote=Exists(post_upvote, output_field=BooleanField()),
                          is_post_save=(Exists(post_save, output_field=BooleanField())))\
                .prefetch_related(Prefetch('comments', queryset=comments))\
                .order_by('-created_on')[page_offset:page_limit+page_offset]

            post_listing = PostSerializer(post_list, many=True).data

            return Response({'data': post_listing}, status=status.HTTP_200_OK)
        else:
            return Response({'error': requestErrorMessagesFormate(validator.get_message())}, status=status.HTTP_200_OK)
    except Exception as exception:
        logerror('user_profile/views.py/user_post_list', str(exception))
        return Response({'error': str(exception)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# get user own profile
@api_view(['GET'])
@isAuthenticate
@RbacService('user:read')
def user_own_profile(request):
    """
    @api {GET} v3/user/profile Get User Own profile
    @apiName Get User Own profile
    @apiGroup User
    @apiHeader {String} authorization Users unique access-token
    @apiSuccessExample {json} Success-Response:
    HTTP/1.1 200 OK
    {
        "id": 103,
        "name": "Nikhil",
        "email": "nikhil12@yopmail.com",
        "profile_pic": "profilepic.png",
        "dob": "1995",
        "bio": null,
        "location": null,
        "latitude": 0.0,
        "longitude": 0.0,
        "age": null,
        "is_admin_verified": 0,
        "is_account_private": 0,
        "is_notification_active": 1,
        "is_location_public": 1,
        "is_saved_post_public": 1,
        "saved_post_count": 1,
        "added_as_interested": 1,
        "interests_count": 0,
        "user_causes": [
            {
                "id": 180,
                "causes_id": 1,
                "causes": {
                    "cause_id": "1",
                    "cause_name": "Environment",
                    "cause_image": null
                }
            },
            {
                "id": 181,
                "causes_id": 2,
                "causes": {
                    "cause_id": "2",
                    "cause_name": "Child Welfare",
                    "cause_image": null
                }
            },
            {
                "id": 182,
                "causes_id": 3,
                "causes": {
                    "cause_id": "3",
                    "cause_name": "Women",
                    "cause_image": null
                }
            }
        ],
        "user_sub_causes": [
            {
                "id": 241,
                "sub_causes_id": 1,
                "sub_causes": {
                    "sub_cause_id": 1,
                    "sub_cause_name": "Forest",
                    "sub_cause_image": null,
                    "causes_detail": {
                        "cause_id": "1",
                        "cause_name": "Environment",
                        "cause_image": null
                    }
                }
            },
            {
                "id": 242,
                "sub_causes_id": 2,
                "sub_causes": {
                    "sub_cause_id": 2,
                    "sub_cause_name": "Activist",
                    "sub_cause_image": null,
                    "causes_detail": {
                        "cause_id": "1",
                        "cause_name": "Environment",
                        "cause_image": null
                    }
                }
            },
            {
                "id": 243,
                "sub_causes_id": 3,
                "sub_causes": {
                    "sub_cause_id": 3,
                    "sub_cause_name": "Women Subcauses 1",
                    "sub_cause_image": null,
                    "causes_detail": {
                        "cause_id": "3",
                        "cause_name": "Women",
                        "cause_image": null
                    }
                }
            }
        ]
    }
    """
    try:
        user_id = request.user_id

        redis_key = (RedisCommon.user_own_details) + str(user_id)  # Key in which we will store data

        user_info = User.objects.filter(id=user_id)
        if user_info:
            serializer = UserOwnDetailsSerializer(user_info, many=True)

            # Set data in Redis
            RedisCommon().set_data(redis_key, serializer.data[0])

            return Response(serializer.data[0], status=status.HTTP_200_OK)
        else:
            return Response({}, status=status.HTTP_200_OK)
    except Exception as exception:
        logerror('user_profile/views.py/user_own_profile', str(exception))
        return Response({'error': str(exception)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# get user own profile
@api_view(['POST'])
@isAuthenticate
@RbacService('profile:update')
def edit_profile(request):
    """
    @api {post} v1/user/profile/edit Edit user profile
    @apiName Edit user profile
    @apiGroup User
    @apiHeader {String} Content-Type application/json
    @apiParam {string} name full name
    @apiParam {string} profile_pic Profile pic
    @apiParam {string} location google location address
    @apiParam {float} latitude
    @apiParam {float} longitude
    @apiParam {text} bio
    @apiParam {string} dob date of birth => year only
    @apiParam {array} user_causes [1,2,3]
    @apiParam {array} user_sub_causes [1,2,3]
    @apiSuccessExample Success-Response:
    HTTP/1.1 201 Created
    {
        "message": "Profile updated successfully"
    }
    @apiErrorExample Error-Response:
    HTTP/1.1 200 OK
    {
        "error": "User has updated inappropriate content in his profile"
    }
    """
    try:
        validator = EditProfileValidator(request.data)
        valid = validator.validate()  # Validate the request
        if valid:
            is_profanity_valid = 1
            is_inappropriate = 0
            current_user_id = request.user_id

            age = None
            dob = None
            # calculate age from dob
            if request.data.get('dob'):
                dob = request.data.get('dob')
                current_year = date.today().year
                age = current_year - int(dob)

            # Check post title, description, keyword profanity
            if profanity.contains_profanity(request.data.get('bio')):
                is_profanity_valid = 0
                is_inappropriate = 1

            # update data in db
            user = User.objects.filter(id=current_user_id, is_active=1).update(
                name=request.data.get('name'),
                profile_pic=request.data.get('profile_pic'),
                dob=dob,
                bio=request.data.get('bio'),
                location=request.data.get('location'),
                latitude=float(request.data.get('latitude')),
                longitude=float(request.data.get('longitude')),
                age=age,
                is_active=is_profanity_valid,
                is_inappropriate=is_inappropriate
            )

            # remove causes and sub-causes before updating
            UserCauses.objects.filter(user_id=current_user_id).delete()
            UserSubCauses.objects.filter(user_id=current_user_id).delete()
            # insert causes
            _causes = request.data.get('user_causes')   
            causes = [UserCauses(user_id_id=current_user_id, cause_id_id=_id)
                        for _id in _causes]
            UserCauses.objects.bulk_create(causes)

            # insert sub-causes
            _sub_causes = request.data.get('user_sub_causes')
            sub_causes = [UserSubCauses(user_id_id=current_user_id, sub_cause_id=_id)
                            for _id in _sub_causes]
            UserSubCauses.objects.bulk_create(sub_causes)

            # Send email to admin in case of invalid content
            if is_profanity_valid == 0:
                user_data = User.objects.get(id=current_user_id)
                serializer = UserSerializer(user_data, many=False)
                EthosCommon.send_user_moderation_email(serializer.data)

            # Delete data from Redis
            redis_key = RedisCommon.user_own_details + str(current_user_id)
            RedisCommon().delete_data(redis_key)

            if is_profanity_valid == 0:
                return Response({'error': Messages.USER_HAS_INVALID_CONTENT}, status=status.HTTP_403_FORBIDDEN)

            return Response({'message': Messages.PROFILE_UPDATED}, status=status.HTTP_200_OK)
        else:
            return Response({'error': requestErrorMessagesFormate(validator.get_message())}, status=status.HTTP_200_OK)
    except Exception as exception:
        logerror('user_profile/views.py/edit_profile', str(exception))
        return Response({'error': str(exception)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

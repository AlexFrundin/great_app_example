from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status
from config.messages import Messages
from utility.ethosCommon import EthosCommon
from ethos_network.settings import EthosCommonConstants
from utility.requestErrorFormate import requestErrorMessagesFormate
from causes_subcauses.models import Cause, SubCause
from utility.authMiddleware import isAuthenticate
from utility.rbacService import RbacService
from users.models import User, UserCauses, UserSubCauses
from .serializers import UserOwnDetailsSerializer
from users.serializers import UserSerializer
from post.requestSchema import PostListValidator, create_engagement_validator
from post.views import post_detail_function
from post.models import (Post, PostCommentsUpvote, PostUpvote,
                        UserSavePost, PostCauses, PostSubCauses,
                        PostKeywords, PostAttachment, PostComments,
                        PostCommentsOnComment, UserSavePost, PostAwsJobIds)
from user_interest.models import UserInterest
from post.serializers import PostListSerializer
from post.views import check_keywords_contains_profanity, post_detail_function
from .requestSchema import EditProfileValidator, deletePostValidator, UserPostListValidator
from datetime import date
from other_user_profile.models import ReportedContent
from utility.redisCommon import RedisCommon
from utility.loggerService import logerror
from utility.contentModerationMiddleware import ContentDetect
from better_profanity import profanity
import redis
import _pickle
from utility.redisCommon import RedisCommon
import datetime
from datetime import datetime, timedelta


# get user own profile
@api_view(['GET'])
@isAuthenticate
@RbacService('user:read')
def user_own_profile(request):
    """
    @api {GET} v1/user/profile Get User Own profile
    @apiName Get User Own profile
    @apiGroup User
    @apiHeader {String} authorization Users unique access-token
    @apiSuccessExample {json} Success-Response:
    HTTP/1.1 200 OK
    {
        "id": 103,
        "name": "Nikhil",
        "email": "nikhil12@yopmail.com",        "profile_pic": "profilepic.png",
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

        redis_object = redis.Redis(EthosCommonConstants.REDIS_HOST)  # Redis object
        redis_key = RedisCommon.user_own_details + str(user_id)  # Key in which we will store data

        # Check if already exist in Redis then don't need to call SQL
        if redis_object.get(redis_key):
            print('Getting data from redis...')
            user_details = _pickle.loads(redis_object.get(redis_key))
            saved_post_count = RedisCommon().get_data(RedisCommon.user_saved_post_count + str(user_id))
            interests_count = RedisCommon().get_data(RedisCommon.user_interests_count + str(user_id))
            added_as_interested_count = RedisCommon().get_data(RedisCommon.user_added_as_interested_count + str(user_id))

            # Get updated causes
            for cause_detail in user_details['user_causes']:
                cause_id = cause_detail['causes']['cause_id']
                cause_redis_data = RedisCommon().get_data(RedisCommon.cause_details + str(cause_id))
                if cause_redis_data:
                    cause_detail['causes'] = _pickle.loads(cause_redis_data)

            # Get updated subcause
            for subcause_detail in user_details['user_sub_causes']:
                subcause_id = subcause_detail['sub_causes']['sub_cause_id']
                subcause_redis_data = RedisCommon().get_data(RedisCommon.subcause_details + str(subcause_id))

                # Update cause data in sub-causes array
                cause_details = subcause_detail['sub_causes']['causes_detail']
                cause_id = cause_details['cause_id']
                cause_redis_data = RedisCommon().get_data(RedisCommon.cause_details + str(cause_id))
                if cause_redis_data:
                    subcause_detail['sub_causes']['causes_detail'] = _pickle.loads(cause_redis_data)

                if subcause_redis_data:
                    cause_details = subcause_detail['sub_causes']['causes_detail']
                    subcause_detail['sub_causes'] = _pickle.loads(subcause_redis_data)
                    subcause_detail['sub_causes']['causes_detail'] = cause_details

            user_details['saved_post_count'] = int(saved_post_count)
            user_details['interests_count'] = int(interests_count)
            user_details['added_as_interested'] =  int(added_as_interested_count)
            return Response(user_details, status=status.HTTP_200_OK)

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
        return Response({'error':str(exception)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Get user's post list
@api_view(['GET'])
@isAuthenticate
@RbacService('user:read')
def user_post_list(request):
    """
    @api {GET} v1/user/self/post/list Get User's own post list
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
                    {
                        "id": 26,
                        "name": "xyz.png",
                        "video_thumbnail": "xyz.png",
                        "type": 2
                    },
                    {
                        "id": 27,
                        "name": "xyz.png",
                        "video_thumbnail": "xyz.png",
                        "type": 2
                    }
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
                    {
                        "id": 26,
                        "cause_detail": {
                            "cause_id": "2",
                            "cause_name": "Child Welfare",
                            "cause_image": null
                        }
                    },
                    {
                        "id": 27,
                        "cause_detail": {
                            "cause_id": "3",
                            "cause_name": "Women",
                            "cause_image": null
                        }
                    }
                ]
            },
            {
                "post_id": 10,
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
                        "id": 28,
                        "name": "abc.png",
                        "video_thumbnail": null,
                        "type": 1
                    },
                    {
                        "id": 29,
                        "name": "xyz.png",
                        "video_thumbnail": "xyz.png",
                        "type": 2
                    },
                    {
                        "id": 30,
                        "name": "xyz.png",
                        "video_thumbnail": "xyz.png",
                        "type": 2
                    }
                ],
                "causes": [
                    {
                        "id": 28,
                        "cause_detail": {
                            "cause_id": "1",
                            "cause_name": "Environment",
                            "cause_image": null
                        }
                    },
                    {
                        "id": 29,
                        "cause_detail": {
                            "cause_id": "2",
                            "cause_name": "Child Welfare",
                            "cause_image": null
                        }
                    },
                    {
                        "id": 30,
                        "cause_detail": {
                            "cause_id": "3",
                            "cause_name": "Women",
                            "cause_image": null
                        }
                    }
                ]
            }
        ]
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
            current_user_id = request.user_id
            # Get post lists
            post_list = Post.objects.filter(created_by=current_user_id, is_active=1).all().order_by('-created_on')[page_offset:page_limit+page_offset]
            serializer = PostListSerializer(post_list, many=True)
            post_listing = []
            for post_data in serializer.data:
                is_post_upvote = PostUpvote.objects.filter(post_id=post_data['post_id'], user_id=current_user_id).exists()
                is_post_save = UserSavePost.objects.filter(post_id=post_data['post_id'], user_id=current_user_id).exists()
                post_comments_data = []
                for post_comment in post_data['comments']:
                    is_comment_upvote = PostCommentsUpvote.objects.filter(comment_id=post_comment['comment_id'], user_id=request.user_id).exists()
                    post_comments_data.append({
                        "comment_id": post_comment['comment_id'],
                        "is_comment_upvote": is_comment_upvote,
                        "comment": post_comment['comment'],
                        "comment_upvote": post_comment['comment_upvote'],
                        "user_detail": post_comment['user_detail'],
                        "comments_on_comment": post_comment['comments_on_comment'],
                        "total_comments_on_comment": post_comment['total_comments_on_comment']
                    })
                post_details = {
                    "post_id": post_data['post_id'],
                    "title": post_data['title'],
                    "is_post_upvote": is_post_upvote,
                    "is_post_save": is_post_save,
                    "description": post_data['description'],
                    "location_address": post_data['location_address'],
                    "latitude": post_data['latitude'],
                    "longitude": post_data['longitude'],
                    "url": post_data['url'],
                    "min_age": post_data['min_age'],
                    "max_age": post_data['max_age'],
                    "is_campaign": post_data['is_campaign'],
                    "upvote_count": post_data['upvote_count'],
                    "created_by": post_data['created_by'],
                    "total_comment": post_data['total_comment'],
                    "user_detail": post_data['user_detail'],
                    "comments":post_comments_data,
                    "attachements": post_data['attachements'],
                    "causes": post_data['causes']
                }
                post_listing.append(post_details)
            if len(serializer.data) > 0:
                return Response({'data':post_listing}, status=status.HTTP_200_OK)
            else:
                return Response({'data':[]}, status=status.HTTP_200_OK)
        else:
            return Response({'error':requestErrorMessagesFormate(validator.get_message())}, status=status.HTTP_200_OK)
    except Exception as exception:
        logerror('user_profile/views.py/user_post_list', str(exception))
        return Response({'error':str(exception)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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
            if not request.data.get('dob') == '':
                dob = request.data.get('dob')
                current_year = date.today().year
                age = current_year - int(request.data.get('dob'))

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

            # get inserted user id
            user_obj = User.objects.get(id=current_user_id)

            # remove causes and sub-causes before updating
            UserCauses.objects.filter(user_id=current_user_id).delete()
            UserSubCauses.objects.filter(user_id=current_user_id).delete()

            # insert causes
            user_causes = request.data.get('user_causes')
            if len(user_causes) > 0:
                for cause_id in user_causes:
                    cause = Cause.objects.get(id=cause_id)
                    user_causes = UserCauses.objects.create(
                        user_id=user_obj,
                        causes_id=cause,
                    )

            # insert sub-causes
            user_sub_causes = request.data.get('user_sub_causes')
            if len(user_sub_causes) > 0:
                for sub_cause_id in user_sub_causes:
                    sub_cause = SubCause.objects.get(id=sub_cause_id)
                    user_sub_causes = UserSubCauses.objects.create(
                        user_id=user_obj,
                        sub_causes_id=sub_cause
                    )

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
            return Response({'error':requestErrorMessagesFormate(validator.get_message())}, status=status.HTTP_200_OK)
    except Exception as exception:
        logerror('user_profile/views.py/edit_profile', str(exception))
        return Response({'error':str(exception)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@isAuthenticate
@RbacService('post:write')
def edit_post(request):
    """
    @api {POST} v1/user/post/edit Edit own Post
    @apiName Edit own Post
    @apiGroup Post
    @apiHeader {String} authorization Users unique access-token
    @apiParam {integer} post_id Post id
    @apiParam {string} title Post title required
    @apiParam {string} description Post Description required
    @apiParam {string} location_address Location name
    @apiParam {double} latitude Latitude
    @apiParam {double} longitude Longitude
    @apiParam {integer} is_campaign 0 for Engagement post/1 for Campaign post
    @apiParam {integer} min_age required (in case of engagement send 0)
    @apiParam {integer} max_age required (in case of engagement send 0)
    @apiParam {string} url required (in case of engagement send blank string)
    @apiParam {list} post_keywords required ["keyword1","keyword2"] (in case of engagement send blank list)
    @apiParam {list} post_causes required [1,2,3] (id of causes)
    @apiParam {list} post_sub_causes required [1,2,3] (id of subcauses)
    @apiParam {list} post_attachment all key required [{"name":"abc.png","type":1,"thumbnail":""},] (type 1 for image, 2 for video)
    @apiSuccessExample Success-Response:
    HTTP/1.1 200 OK
    {
        "message": "Post updated successfully"
    }
    @apiSuccessExample Success-Response:
    HTTP/1.1 200 OK
    {
        "message": "You don't have permission to edit this post"
    }
    """
    try:
        validator = create_engagement_validator(request.data)
        valid = validator.validate()  # validate the request
        if valid:
            is_post_valid = 1
            invalid_content_type = ''
            is_attachment_valid = True
            is_inappropriate = 0
            post_id = request.data.get('post_id')
            current_user_id = request.user_id

            if Post.objects.filter(post_id = post_id, created_by=current_user_id).exists():
                post_obj = Post.objects.get(post_id=post_id)

                post_attachment = request.data.get('post_attachment')
                if len(post_attachment) > 3:
                    return Response({'message': Messages.MAX_ATTACHMENT}, status=status.HTTP_200_OK)
                else:
                    # Attachment validation
                    for attachment in post_attachment:
                        # check whether attachment is valid. 1 => image, 2 => video
                        if attachment['type'] == 1:
                            attachment_ext = EthosCommon.get_file_extention(attachment['name'])
                            if attachment_ext not in EthosCommonConstants.ACCEPTED_IMG_TYPES:
                                is_attachment_valid = False
                        if attachment['type'] == 2:
                            attachment_ext = EthosCommon.get_file_extention(attachment['name'])
                            if attachment_ext not in EthosCommonConstants.ACCEPTED_VIDEO_TYPES:
                                is_attachment_valid = False

                if not is_attachment_valid:
                    return Response({'error': Messages.INVALID_MEDIA_TYPE}, status=status.HTTP_200_OK)

                # Check attachments moderation
                if len(post_attachment):
                    # Create object of content middleware
                    content_moderation = ContentDetect()

                    for attachment in post_attachment:
                        if attachment['type'] == 1:  # Check image validation
                            image_valid = content_moderation.detect_image_labels(attachment['name'])
                            if 'error' in image_valid:
                                return Response({'error': image_valid['error']}, status=status.HTTP_200_OK)
                            else:
                                if len(image_valid['result']) > 0:
                                    is_post_valid = 0
                                    invalid_content_type = 'Images'
                                    is_inappropriate = 1

                # Check post title, description, keyword profanity
                if profanity.contains_profanity(request.data.get('title')) or \
                        profanity.contains_profanity(request.data.get('description')) or \
                        check_keywords_contains_profanity(request.data.get('post_keywords')):
                    is_post_valid = 0
                    invalid_content_type = 'Title or Description or Keywords'
                    is_inappropriate = 1

                # update post
                Post.objects.filter(post_id=post_id).update(
                    title=request.data.get('title'),
                    description=request.data.get('description'),
                    location_address=request.data.get('location_address'),
                    latitude=request.data.get('latitude'),
                    longitude=request.data.get('longitude'),
                    is_campaign=request.data.get('is_campaign'),
                    url=request.data.get('url'),
                    min_age=request.data.get('min_age'),
                    max_age=request.data.get('max_age'),
                    is_active=is_post_valid,
                    is_inappropriate=is_inappropriate
                )
                PostKeywords.objects.filter(post_id=post_id).delete()
                post_keywords = request.data.get('post_keywords')
                if len(post_keywords) > 0:
                    for keyword in post_keywords:        
                        PostKeywords.objects.create(
                            post_id = post_obj,
                            keyword = keyword                     
                        )

                # delete causes subcauses
                PostCauses.objects.filter(post_id=post_id).delete()
                PostSubCauses.objects.filter(post_id=post_id).delete()

                # insert causes
                post_causes = request.data.get('post_causes')
                if len(post_causes) > 0:
                    for cause_id in post_causes:
                        cause = Cause.objects.get(id=cause_id)
                        PostCauses.objects.create(
                            post_id=post_obj,
                            cause_id=cause
                        )
                
                # insert sub-causes
                post_sub_causes = request.data.get('post_sub_causes')
                if len(post_sub_causes) > 0:
                    for sub_cause_id in post_sub_causes:
                        sub_cause = SubCause.objects.get(id=sub_cause_id)
                        PostSubCauses.objects.create(
                            post_id=post_obj,
                            subcause_id=sub_cause
                        )

                # delete attachments
                PostAttachment.objects.filter(post_id=post_id).delete()

                # insert attachments
                if len(post_attachment):
                    for attachment in post_attachment:
                        # check whether attachment is image or video
                        # 1 for image, 2 for video
                        if attachment['type'] == 1:
                            PostAttachment.objects.create(
                                post_id=post_obj,
                                name=attachment['name'],
                                type=1
                            )
                        else:
                            PostAttachment.objects.create(
                                post_id=post_obj,
                                name=attachment['name'],
                                type=2,
                                video_thumbnail=attachment['thumbnail']
                            )

                # Update data in Redis
                redis_key = RedisCommon.post_details + str(post_id)  # Key in which we will store data
                post_details = post_detail_function(post_id, current_user_id)
                RedisCommon().set_data(redis_key, post_details)

                # Get and insert jobIds into DB to AWS Rekognition
                if attachment['type'] == 2:
                    video_job_id = content_moderation.detect_video_labels(attachment['name'])
                    video_label_job_id = content_moderation.detect_video_text_labels(attachment['name'])

                    if 'error' in video_job_id:
                        return Response({'error': video_job_id['error']}, status=status.HTTP_200_OK)
                    elif 'error' in video_label_job_id:
                        return Response({'error': video_label_job_id['error']}, status=status.HTTP_200_OK)
                    else:
                        if len(video_job_id['result']) > 0:
                            PostAwsJobIds.objects.create(
                                post_id=post_id,
                                job_id=video_job_id['result'],
                                rekognition_type='video_label'
                            )
                        if len(video_label_job_id['result']) > 0:
                            PostAwsJobIds.objects.create(
                                post_id=post_id,
                                job_id=video_label_job_id['result'],
                                rekognition_type='text_label'
                            )

                # Send email to admin in case of invalid content
                if is_post_valid == 0:
                    post_details = post_detail_function(post_id, request.user_id)
                    EthosCommon.send_content_moderation_email(post_details, invalid_content_type)
                    return Response({'message': Messages.POST_SUBMITTED_TO_APPROVAL}, status=status.HTTP_200_OK)

                return Response({'message': Messages.POST_UPDATED}, status=status.HTTP_200_OK)
            else:
                return Response({'message': Messages.POST_UPDATED_NOT_PERMISSION}, status=status.HTTP_200_OK)
        else:
            return Response({'error':requestErrorMessagesFormate(validator.get_message())}, status=status.HTTP_200_OK)
    except Exception as exception:
        logerror('user_profile/views.py/edit_post', str(exception))
        return Response({'error':str(exception)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['DELETE'])
@isAuthenticate
@RbacService('post:write')
def delete_post(request):
    """
    @api {DELETE} v1/user/post/delete delete own Post
    @apiName delete own Post
    @apiGroup Post
    @apiHeader {String} authorization Users unique access-token
    @apiParam {integer} post_id Post id
    @apiSuccessExample Success-Response:
    HTTP/1.1 200 OK
    {
        "message": "Post deleted successfully"
    }
    @apiSuccessExample Success-Response:
    HTTP/1.1 200 OK
    {
        "message": "You don't have permission to delete this post"
    }
    """
    try:
        validator = deletePostValidator(request.GET)
        valid = validator.validate()  # validate the request
        if valid:
            post_id = int(request.GET['post_id'])
            current_user_id = request.user_id
            if Post.objects.filter(post_id = post_id, created_by=current_user_id).exists():
                ReportedContent.objects.filter(content_type='post', content_id=post_id).delete()
                Post.objects.filter(post_id=post_id).delete()
                return Response({'message': Messages.POST_DELETED}, status=status.HTTP_200_OK)
            else:
                return Response({'message': Messages.POST_DELETED_NOT_PERMISSION}, status=status.HTTP_200_OK)
        else:
            return Response({'error':requestErrorMessagesFormate(validator.get_message())}, status=status.HTTP_200_OK)
    except Exception as exception:
        logerror('user_profile/views.py/delete_post', str(exception))
        return Response({'error':str(exception)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Get user's saved post list
@api_view(['GET'])
@isAuthenticate
@RbacService('post:read')
def user_saved_post_list(request):
    """
    @api {GET} v1/user/self/saved/post/list Get User's own saved post list
    @apiName Get User's own saved post list
    @apiGroup Post
    @apiHeader {String} Content-Type application/json
    @apiParam {integer} page_limit Page limit
    @apiParam {integer} page_offset Page offset
    @apiSuccessExample {json} Success-Response:
    HTTP/1.1 200 OK
    {
        "data": [
            {
                "post_id": 1,
                "title": "Campgain post new one",
                "is_post_upvote": false,
                "is_post_save": true,
                "description": "Desc",
                "location_address": "address new",
                "latitude": -23.23,
                "longitude": -45.0,
                "url": "",
                "min_age": 0,
                "max_age": 0,
                "is_campaign": 0,
                "upvote_count": 5,
                "created_by": 84,
                "total_comment": 9,
                "user_detail": {
                    "name": "Vivek Chaudhary",
                    "id": 84,
                    "email": "rits.chaudhary1992@gmail.com",
                    "profile_pic": ""
                },
                "comments": [
                    {
                        "comment_id": 1,
                        "is_comment_upvote": false,
                        "comment": "hello",
                        "comment_upvote": 0,
                        "user_detail": {
                            "name": "Vivek Chaudhary",
                            "id": 84,
                            "email": "rits.chaudhary1992@gmail.com",
                            "profile_pic": ""
                        },
                        "comments_on_comment": [
                            {
                                "comment_id": 1,
                                "user_id": 102,
                                "comment": "comment on comment via API",
                                "user_detail": {
                                    "name": "Nikhil",
                                    "id": 102,
                                    "email": "nikhil1@techaheadcorp.com",
                                    "profile_pic": "profilepic.png"
                                }
                            }
                        ],
                        "total_comments_on_comment": 1
                    },
                    {
                        "comment_id": 2,
                        "is_comment_upvote": false,
                        "comment": "hi",
                        "comment_upvote": 0,
                        "user_detail": {
                            "name": "Vivek Chaudhary",
                            "id": 84,
                            "email": "rits.chaudhary1992@gmail.com",
                            "profile_pic": ""
                        },
                        "comments_on_comment": [],
                        "total_comments_on_comment": 0
                    },
                    {
                        "comment_id": 3,
                        "is_comment_upvote": false,
                        "comment": "new hello",
                        "comment_upvote": 0,
                        "user_detail": {
                            "name": "Vivek Chaudhary",
                            "id": 84,
                            "email": "rits.chaudhary1992@gmail.com",
                            "profile_pic": ""
                        },
                        "comments_on_comment": [],
                        "total_comments_on_comment": 0
                    },
                    {
                        "comment_id": 4,
                        "is_comment_upvote": false,
                        "comment": "new comment via API",
                        "comment_upvote": 0,
                        "user_detail": {
                            "name": "Nikhil",
                            "id": 102,
                            "email": "nikhil1@techaheadcorp.com",
                            "profile_pic": "profilepic.png"
                        },
                        "comments_on_comment": [],
                        "total_comments_on_comment": 0
                    },
                    {
                        "comment_id": 5,
                        "is_comment_upvote": false,
                        "comment": "another comment via API",
                        "comment_upvote": 0,
                        "user_detail": {
                            "name": "Nikhil",
                            "id": 102,
                            "email": "nikhil1@techaheadcorp.com",
                            "profile_pic": "profilepic.png"
                        },
                        "comments_on_comment": [],
                        "total_comments_on_comment": 0
                    }
                ],
                "attachements": [
                    {
                        "id": 4,
                        "name": "abc.png",
                        "video_thumbnail": null,
                        "type": 1
                    },
                    {
                        "id": 40,
                        "name": "abc.png",
                        "video_thumbnail": null,
                        "type": 1
                    },
                    {
                        "id": 42,
                        "name": "xyz.png",
                        "video_thumbnail": "xyz.png",
                        "type": 2
                    }
                ],
                "causes": [
                    {
                        "id": 44,
                        "cause_detail": {
                            "cause_id": "1",
                            "cause_name": "Environment",
                            "cause_image": null,
                            "cause_color": null
                        }
                    },
                    {
                        "id": 45,
                        "cause_detail": {
                            "cause_id": "2",
                            "cause_name": "Child Welfare",
                            "cause_image": null,
                            "cause_color": null,
                            "cause_color_gradient": "#fafafa"
                        }
                    },
                    {
                        "id": 46,
                        "cause_detail": {
                            "cause_id": "3",
                            "cause_name": "Women",
                            "cause_image": null,
                            "cause_color": null,
                            "cause_color_gradient": "#fafafa"
                        }
                    }
                ]
            }
        ]
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
            current_user_id = request.user_id

            # Get post lists
            post_ids = list(UserSavePost.objects.filter(user_id=current_user_id).values_list('post_id', flat=True).distinct())
            post_list = Post.objects.filter(post_id__in=post_ids, is_active=1).all().order_by('-created_on')[page_offset:page_limit+page_offset]
            serializer = PostListSerializer(post_list, many=True)
            post_listing = []
            for post_data in serializer.data:
                is_post_upvote = PostUpvote.objects.filter(post_id=post_data['post_id'], user_id=current_user_id).exists()
                is_post_save = UserSavePost.objects.filter(post_id=post_data['post_id'], user_id=current_user_id).exists()
                post_comments_data = []
                for post_comment in post_data['comments']:
                    is_comment_upvote = PostCommentsUpvote.objects.filter(comment_id=post_comment['comment_id'], user_id=request.user_id).exists()
                    post_comments_data.append({
                        "comment_id": post_comment['comment_id'],
                        "is_comment_upvote": is_comment_upvote,
                        "comment": post_comment['comment'],
                        "comment_upvote": post_comment['comment_upvote'],
                        "user_detail": post_comment['user_detail'],
                        "comments_on_comment": post_comment['comments_on_comment'],
                        "total_comments_on_comment": post_comment['total_comments_on_comment']
                    })
                post_details = {
                    "post_id": post_data['post_id'],
                    "title": post_data['title'],
                    "is_post_upvote": is_post_upvote,
                    "is_post_save": is_post_save,
                    "description": post_data['description'],
                    "location_address": post_data['location_address'],
                    "latitude": post_data['latitude'],
                    "longitude": post_data['longitude'],
                    "url": post_data['url'],
                    "min_age": post_data['min_age'],
                    "max_age": post_data['max_age'],
                    "is_campaign": post_data['is_campaign'],
                    "upvote_count": post_data['upvote_count'],
                    "created_by": post_data['created_by'],
                    "total_comment": post_data['total_comment'],
                    "user_detail": post_data['user_detail'],
                    "comments":post_comments_data,
                    "attachements": post_data['attachements'],
                    "causes": post_data['causes']
                }
                post_listing.append(post_details)
            if len(serializer.data) > 0:
                return Response({'data':post_listing}, status=status.HTTP_200_OK)
            else:
                return Response({'data':[]}, status=status.HTTP_200_OK)
        else:
            return Response({'error':requestErrorMessagesFormate(validator.get_message())}, status=status.HTTP_200_OK)
    except Exception as exception:
        logerror('user_profile/views.py/user_saved_post_list', str(exception))
        return Response({'error':str(exception)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Delete user profile
@api_view(['GET'])
@isAuthenticate
@RbacService('user:profile:delete')
def user_delete_profile(request):
    """
    @api {GET} v1/user/profile/delete Delete profile
    @apiName Delete profile
    @apiGroup Post
    @apiHeader {String} Content-Type application/json
    @apiSuccessExample {json} Success-Response:
    HTTP/1.1 200 OK
    {
        "message": "Your request to delete profile has been accepted and will be processed after 15 days"
    }
    @apiErrorExample Error-Response:
    HTTP/1.1 200 OK
    {
        "error": "Used does not exist"
    }
    """
    try:
        current_user_id = request.user_id
        user_info = User.objects.filter(id=current_user_id)
        if user_info:
            User.objects.filter(id=current_user_id, is_active=1).update(
                is_deleted=1,
                deleted_at=datetime.now()
            )
            return Response({'message': Messages.PROFILE_DELETED}, status=status.HTTP_200_OK)
        else:
            return Response({'error': Messages.USER_NOT_EXIST}, status=status.HTTP_200_OK)
    except Exception as exception:
        logerror('user_profile/views.py/user_delete_profile', str(exception))
        return Response({'error': str(exception)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Delete user data 15 days ago
def delete_user_data():
    try:
        n = 15
        date_n_days_ago = datetime.now() - timedelta(days=n)

        # Get users who have deleted their account before 15 days ago
        users_list = User.objects.filter(
            is_deleted=1,
            deleted_at__lte=date_n_days_ago
        ).values_list('id', flat=True).distinct()

        if len(users_list) > 0:
            for user_id in users_list:
                UserInterest.objects.filter(user_id=user_id).delete()
                UserInterest.objects.filter(interested_user_id=user_id).delete()
                ReportedContent.objects.filter(content_type='user', content_id=user_id).delete()
                User.objects.filter(id=user_id, is_deleted=1).delete()
            return True

    except Exception as exception:
        logerror('user_profile/views.py/delete_user_data', str(exception))
        return Response({'error': str(exception)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
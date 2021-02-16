import json
from django.shortcuts import render
from utility.authMiddleware import isAuthenticate
from utility.ethosCommon import EthosCommon
from .requestSchema import (create_engagement_validator, post_details_validator, 
                            PostListValidator, UpvoteUsersListValidator,
                            post_comment_by_user_validator, post_upvote_validator,
                            post_comments_validator, SavePostValidator,
                            ReportPostValidator, ReportReasonListValidator,
                            PostReceiveNotificationValidator)
from .models import (Post, PostCauses,
                    PostSubCauses, PostAttachment,
                    PostKeywords, PostComments, UserSavePost,
                    PostCommentsOnComment, PostUpvote, PostCommentsUpvote,
                    PostReceiveNotification, PostAwsJobIds)
from causes_subcauses.models import Cause, SubCause
from users.models import User, UserCauses, UserSubCauses
from user_interest.models import UserInterest, UserInterestsRequest
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status
from config.messages import Messages
from utility.requestErrorFormate import requestErrorMessagesFormate
from .serializers import (PostSerializer, PostCommentsOfCommentSerializer,
                          PostAttachmentSerializer, PostListSerializer,
                          PostKeywordsSerializer, PostCommentsSerializer,
                          UserCauseSerializer, UserSubCausesSerializer,
                          ReportReasonPostListSerializer,ReportReasonUserListSerializer)
from user_interest.serializers import SuggestedUsersSerializer
from ethos_network.settings import EthosCommonConstants
from utility.rbacService import RbacService
from collections import OrderedDict
from django.db.models import F
from other_user_profile.models import ReportReasonPost, ReportReasonUser, ReportedContent
from utility.contentModerationMiddleware import ContentDetect
from better_profanity import profanity
from utility.fcmController import GetNotification
import redis
import _pickle
from utility.redisCommon import RedisCommon
from utility.loggerService import logerror

# Create your views here.

@api_view(['POST'])
@isAuthenticate
@RbacService('post:create')
def create_post(request):
    """
    @api {POST} v1/user/post/create Create Post
    @apiName Create Post
    @apiGroup Post
    @apiHeader {String} authorization Users unique access-token.
    @apiParam {string} title Post title required
    @apiParam {string} description Post Description required
    @apiParam {string} location_address Location name
    @apiParam {double} latitude Latitude
    @apiParam {double} longitude Longitude
    @apiParam {integer} is_campaign 0 => Engagement, 1 => Campaign
    @apiParam {integer} min_age required (in case of engagement send 0)
    @apiParam {integer} max_age required (in case of engagement send 0)
    @apiParam {string} url required (in case of engagement send blank string)
    @apiParam {list} post_keywords required ["keyword1","keyword2"] (in case of engagement send blank list)
    @apiParam {list} post_causes required [1,2,3] (id of causes)
    @apiParam {list} post_sub_causes required [1,2,3] (id of subcauses)
    @apiParam {list} post_attachment all key required [{"name":"abc.png","type":1,"thumbnail":""},] (type 1 for image, 2 for video)
    @apiSuccessExample Success-Response:
    HTTP/1.1 201 OK
    {
        "message": "Post has been created successfully",
    }
    HTTP/1.1 201 OK
    {
        "error": "Your post has been submitted to Admin for approval",
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

            "----------------------Bagfix--------------------"
            content_moderation = ContentDetect()
            # Check attachments moderation
            if len(post_attachment):

                "----------------------"
                # Create object of content middleware
                # content_moderation = ContentDetect()

                for attachment in post_attachment:
                    if attachment['type'] == 1: # Check image validation
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

            # Get user info
            user = User.objects.get(id=request.user_id)

            Post.objects.create(
                title=request.data.get('title'),
                description=request.data.get('description'),
                location_address=request.data.get('location_address'),
                latitude=request.data.get('latitude'),
                longitude=request.data.get('longitude'),
                is_campaign=request.data.get('is_campaign'),
                created_by=user,
                url=request.data.get('url'),
                min_age=request.data.get('min_age'),
                max_age=request.data.get('max_age'),
                is_active=is_post_valid,
                is_inappropriate=is_inappropriate
            )
            post_id = Post.objects.latest('post_id').post_id
            post = Post.objects.get(post_id=post_id)

            # insert keywords
            post_keywords = request.data.get('post_keywords')
            # data message for notification
            data_message = {
                "body": user.name+Messages.POST_CREATED_MESSAGE,
                "title": Messages.POST_CREATED_TITLE,
                "reference_id": 3,
                "click_action": "NOTIFICATION_CLICK",
                "event_id": post_id
            }
            "---------------------------------------------------"
            if len(post_keywords) > 0:
                for keyword in post_keywords:        
                    PostKeywords.objects.create(
                        post_id = post,
                        keyword = keyword                     
                    )

            # insert causes
            post_causes = request.data.get('post_causes')
            "------------------------------------------"
            if len(post_causes) > 0:
                for cause_id in post_causes:
                    cause = Cause.objects.get(id=cause_id)
                    PostCauses.objects.create(
                        post_id=post,
                        cause_id=cause
                    )

            # insert sub-causes
            "-------------------------------------------------"
            post_sub_causes = request.data.get('post_sub_causes')
            if len(post_sub_causes) > 0:
                for sub_cause_id in post_sub_causes:
                    sub_cause = SubCause.objects.get(id=sub_cause_id)
                    PostSubCauses.objects.create(
                        post_id=post,
                        subcause_id=sub_cause
                    )

            # insert attachments
            if len(post_attachment):
                "-------------------------------------------"
                for attachment in post_attachment:
                    # check whether attachment is image or video
                    # 1 for image, 2 for video
                    if attachment['type'] == 1:
                        PostAttachment.objects.create(
                            post_id=post,
                            name=attachment['name'],
                            type=1
                        )
                    else:
                        PostAttachment.objects.create(
                            post_id=post,
                            name=attachment['name'],
                            type=2,
                            video_thumbnail=attachment['thumbnail']
                        )

            # Get and insert jobIds into DB to AWS Rekognition
            if attachment['type'] == 2:
                "--------------------------Fix---------------------"
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
                return Response({'message': Messages.POST_SUBMITTED_TO_APPROVAL}, status=status.HTTP_201_CREATED)
            else:
                # interested user ids
                interested_user_ids = list(UserInterest.objects.filter(interested_user_id=request.user_id).values_list('user_id', flat=True).distinct())
                device_tokens = GetNotification().getDeviceToken(interested_user_ids)
                for user_id in interested_user_ids:
                    GetNotification().addNotification(user_id, Messages.POST_CREATED_TITLE, user.name+Messages.POST_CREATED_MESSAGE, 3, post_id)

                if len(device_tokens) > 0:
                    GetNotification().send_push_notification(
                        device_tokens,
                        Messages.POST_CREATED_TITLE,
                        user.name+Messages.POST_CREATED_MESSAGE,
                        data_message
                    )

            return Response({'message': Messages.POST_CREATED}, status=status.HTTP_201_CREATED)
        else:
            return Response({'error':requestErrorMessagesFormate(validator.get_message())}, status=status.HTTP_200_OK)
    except Exception as exception:
        logerror('post/views.py/create_post', str(exception))
        return Response({'error':str(exception)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@isAuthenticate
@RbacService('post:read')
def post_detail(request):
    """
    @api {GET} v1/user/post/detail?post_id= Get Post details
    @apiName Post details
    @apiGroup Post
    @apiHeader {String} authorization Users unique access-token.
    @apiParam {integer} post_id query param
    @apiSuccessExample {json} Success-Response:
    HTTP/1.1 200 OK
    {
        "post_id": 1,
        "title": "Campgain post",
        "is_post_upvote": true,
        "is_post_save": true,
        "description": "Desc",
        "location_address": "address",
        "latitude": 28.6863,
        "longitude": 77.2218,
        "url": "www.google.com",
        "min_age": 2,
        "max_age": 3,
        "is_campaign": 1,
        "upvote_count": 2,
        "created_by": 84,
        "user_detail": {
            "name": "Vivek Chaudhary",
            "id": 84,
            "email": "rits.chaudhary1992@gmail.com",
            "profile_pic": ""
        },
        "comments": [
            {
                "comment_id": 2,
                "is_comment_upvote": true,
                "comment": "hi",
                "comment_upvote": 5,
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
                "comment_upvote": 3,
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
                "comment_id": 1,
                "is_comment_upvote": false,
                "comment": "hello",
                "comment_upvote": 2,
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
                "total_comments_on_comment": 2
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
        "attachements": [],
        "post_keywords": [
            {
                "id": 1,
                "keyword": "keyword1"
            },
            {
                "id": 2,
                "keyword": "keyword2"
            }
        ],
        "causes": [
            {
                "id": 1,
                "cause_detail": {
                    "cause_id": "1",
                    "cause_name": "Environment",
                    "cause_image": null
                }
            }
        ],
        "sub_causes": [
            {
                "id": 1,
                "sub_cause_detail": {
                    "cause_id": 1,
                    "sub_cause_id": 1,
                    "sub_cause_name": "Forest",
                    "sub_cause_image": null
                }
            },
            {
                "id": 2,
                "sub_cause_detail": {
                    "cause_id": 1,
                    "sub_cause_id": 2,
                    "sub_cause_name": "Activist",
                    "sub_cause_image": null
                }
            },
            {
                "id": 3,
                "sub_cause_detail": {
                    "cause_id": 3,
                    "sub_cause_id": 3,
                    "sub_cause_name": "Women Subcauses 1",
                    "sub_cause_image": null
                }
            }
        ]
    }
    @apiErrorExample Error-Response:
    HTTP/1.1 404 Not Found
    {
        "error": "Post does not exist"
    }
    """
    try:
        validator = post_details_validator(request.GET)
        valid = validator.validate()  # Validate the request
        if valid:
            post_id = int(request.GET['post_id'])
            current_user_id = request.user_id

            redis_object = redis.Redis(EthosCommonConstants.REDIS_HOST) # Redis object
            redis_key = RedisCommon.post_details + str(post_id) # Key in which we will store data

            # Check if already exist in Redis then don't need to call SQL
            if redis_object.get(redis_key):
                print('Getting data from redis...')
                post_details = _pickle.loads(redis_object.get(redis_key))
                post_upvote_users = redis_object.lrange(RedisCommon.post_upvote_users + str(post_id), 0, -1)
                save_post_users = redis_object.lrange(RedisCommon.save_post_users + str(post_id), 0, -1)
                upvote_post_count = RedisCommon().get_data(RedisCommon.upvote_post_count + str(post_id))

                # check if user has already upvote post or not
                is_post_upvote = False
                for user_id in post_upvote_users:
                    if current_user_id == int(user_id.decode('utf-8')):
                        is_post_upvote = True
                        break

                # check if user has already save post or not
                is_post_save = False
                for user_id in save_post_users:
                    if current_user_id == int(user_id.decode('utf-8')):
                        is_post_save = True
                        break

                # check if user has already upvote comment or not
                all_comments = post_details['comments']
                for comment in all_comments:

                    upvote_comment_count = RedisCommon().get_data(RedisCommon.upvote_comment_count + str(comment['comment_id']))
                    comment_upvote_users = redis_object.lrange(RedisCommon.comment_upvote_users + str(comment['comment_id']), 0, -1)
                    is_comment_upvote = False

                    for user_id in comment_upvote_users:
                        if current_user_id == int(user_id.decode('utf-8')):
                            is_comment_upvote = True
                            break

                    # Update comment_upvote status based on current user
                    comment['is_comment_upvote'] = is_comment_upvote

                    # Update comment_upvote count
                    comment['comment_upvote'] = upvote_comment_count

                post_details['is_post_upvote'] = is_post_upvote
                post_details['is_post_save'] = is_post_save
                post_details['upvote_count'] = int(upvote_post_count)

                # Get updated causes
                for cause_detail in post_details['causes']:
                    cause_id = cause_detail['cause_detail']['cause_id']
                    cause_redis_data = RedisCommon().get_data(RedisCommon.cause_details + str(cause_id))
                    if cause_redis_data:
                        cause_detail['cause_detail'] = _pickle.loads(cause_redis_data)

                # Get updated subcause
                for subcause_detail in post_details['sub_causes']:
                    subcause_id = subcause_detail['sub_cause_detail']['sub_cause_id']
                    subcause_redis_data = RedisCommon().get_data(RedisCommon.subcause_details + str(subcause_id))
                    if subcause_redis_data:
                        subcause_detail['sub_cause_detail'] = _pickle.loads(subcause_redis_data)

                return Response(post_details, status=status.HTTP_200_OK)

            if Post.objects.filter(post_id=post_id, is_active=1).exists():
                response = post_detail_function(post_id, request.user_id)

                # Set data in Redis
                RedisCommon().set_data(redis_key, response)

                return Response(response, status=status.HTTP_200_OK)
            else:
                return Response({'error':Messages.INVALID_POST_ID}, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({'error':requestErrorMessagesFormate(validator.get_message())}, status=status.HTTP_200_OK)
    except Exception as exception:
        logerror('post/views.py/post_detail', str(exception))
        return Response({'error':str(exception)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Get post details with top 5 comments based on upvotes
def post_detail_function(post_id, user_id):

    try:
        # Get Post details
        post_details = Post.objects.get(post_id=post_id)
        serializer = PostSerializer(post_details, many=False)
        post_data = serializer.data

        is_post_save = False
        is_post_upvote = PostUpvote.objects.filter(post_id=post_id, user_id=user_id).exists()

        post_comments_data = []
        "------------------------notOptimisize---------------------"
        for post_comment in post_data['comments']:

            is_comment_upvote = PostCommentsUpvote.objects.filter(comment_id=post_comment['comment_id'], user_id=user_id).exists()
            is_post_save = UserSavePost.objects.filter(post_id=post_id, user_id=user_id).exists()

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
            "created_on": post_data['created_on'],
            "upvote_count": post_data['upvote_count'],
            "created_by": post_data['created_by'],
            "user_detail": post_data['user_detail'],
            "comments":post_comments_data,
            "attachements": post_data['attachements'],
            "post_keywords": post_data['post_keywords'],
            "causes": post_data['causes'],
            "sub_causes": post_data['sub_causes']
        }
        return post_details
    except Exception as exception:
        logerror('post/views.py/post_detail_function', str(exception))
        return Response({'error':str(exception)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Get post list
@api_view(['POST'])
@isAuthenticate
@RbacService('post:read')
def list_post(request):
    """
    @api {POST} v1/user/post/list Get post list
    @apiName Get post list
    @apiGroup Post
    @apiHeader {String} Content-Type application/json
    @apiParam {integer} page_limit Page limit
    @apiParam {integer} page_offset Page offset
    @apiParam {list} causes [1,2,3] blank list in case of no filter
    @apiParam {list} subcauses [1,2,3] blank list in case of no filter
    @apiParam {float} latitude default -> 0
    @apiParam {float} longitude default -> 0
    @apiParam {integer} distance default -> 0
    @apiParam {integer} home_search default -> 1
    @apiSuccessExample {json} Success-Response:
    HTTP/1.1 200 OK
    {
        "data": [
            {
                "post_id": 1,
                "title": "Campgain post",
                "is_post_upvote": false,
                "is_post_save": true,
                "description": "Desc",
                "location_address": "address",
                "latitude": 28.6863,
                "longitude": 77.2218,
                "url": "www.google.com",
                "min_age": 2,
                "max_age": 3,
                "is_campaign": 1,
                "upvote_count": 2,
                "created_by": 84,
                "total_comment": 13,
                "user_detail": {
                    "name": "Vivek Chaudhary",
                    "id": 84,
                    "email": "rits.chaudhary1992@gmail.com",
                    "profile_pic": ""
                },
                "comments": [
                    {
                        "comment_id": 2,
                        "is_comment_upvote": false,
                        "comment": "hi",
                        "comment_upvote": 5,
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
                        "comment_upvote": 3,
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
                        "comment_id": 1,
                        "is_comment_upvote": false,
                        "comment": "hello",
                        "comment_upvote": 2,
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
                        "total_comments_on_comment": 2
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
                "attachements": [],
                "causes": [
                    {
                        "id": 1,
                        "cause_detail": {
                            "cause_id": "1",
                            "cause_name": "Environment",
                            "cause_image": null
                        }
                    }
                ]
            },
            {
                "post_id": 2,
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
                "created_by": 84,
                "total_comment": 0,
                "user_detail": {
                    "name": "Vivek Chaudhary",
                    "id": 84,
                    "email": "rits.chaudhary1992@gmail.com",
                    "profile_pic": ""
                },
                "comments": [],
                "attachements": [
                    {
                        "id": 4,
                        "name": "abc.png",
                        "video_thumbnail": null,
                        "type": 1
                    },
                    {
                        "id": 5,
                        "name": "xyz.png",
                        "video_thumbnail": "xyz.png",
                        "type": 2
                    },
                    {
                        "id": 6,
                        "name": "xyz.png",
                        "video_thumbnail": "xyz.png",
                        "type": 2
                    }
                ],
                "causes": [
                    {
                        "id": 4,
                        "cause_detail": {
                            "cause_id": "1",
                            "cause_name": "Environment",
                            "cause_image": null
                        }
                    },
                    {
                        "id": 5,
                        "cause_detail": {
                            "cause_id": "2",
                            "cause_name": "Child Welfare",
                            "cause_image": null
                        }
                    },
                    {
                        "id": 6,
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
        validator = PostListValidator(request.data)
        valid = validator.validate()  # Validate the request
        if valid:
            page_limit = request.data.get('page_limit')
            page_offset = request.data.get('page_offset')
            causes = request.data.get('causes')
            subcauses = request.data.get('subcauses')
            latitude = float(request.data.get('latitude'))
            longitude = float(request.data.get('longitude'))
            distance = request.data.get('distance')
            home_search = request.data.get('home_search')

            post_causes = PostCauses.objects.filter(cause_id__in=causes).values_list('post_id', flat=True).distinct()
            post_subcauses = PostSubCauses.objects.filter(subcause_id__in=subcauses).values_list('post_id', flat=True).distinct()
            post_ids = list(set(list(post_causes)+list(post_subcauses)))

            if len(post_ids) == 0 and len(causes) == 0 and len(subcauses) == 0:
                post_ids = list(Post.objects.filter().all().values_list('post_id', flat=True).distinct())
            
            # if location based listing then
            if len(post_ids) > 0 and distance > 0:
                post_id_array = []
                new_post_list = Post.objects.raw('SELECT post_id, ( 6371 * acos( cos( radians(%s) ) * cos( radians( latitude ) ) * cos( radians( longitude ) - radians(%s) ) + sin( radians(%s) ) * sin( radians( latitude ) ) ) ) AS distance FROM posts WHERE post_id IN %s AND is_active=1 HAVING distance < %s ORDER BY distance', [latitude, longitude, latitude, post_ids, distance])
                for p in new_post_list:
                    post_id_array.append(p.post_id)
                post_ids = post_id_array

            # Get logged in user id
            current_user_id = request.user_id
            user_interest_ids = UserInterest.objects.filter(
                user_id=current_user_id
            ).values_list(
                'interested_user_id',
                flat=True
            ).distinct().order_by('interested_user_id').reverse()

            # Get post lists
            "--------------------notOptimis--------------------"
            if distance > 0:
                post_list = Post.objects.filter(
                    is_active=1,
                    post_id__in=post_ids
                ).all().order_by('-created_on')[page_offset:page_limit+page_offset]
            else:
                # if user comes from search screen then no need to take user-interests into account
                if home_search == 0:
                    post_list = Post.objects.filter(
                        is_active=1,
                        post_id__in=post_ids
                    ).all().order_by('-created_on')[page_offset:page_limit+page_offset]
                else:
                    post_list = Post.objects.filter(
                        created_by__in=user_interest_ids,
                        is_active=1,
                        post_id__in=post_ids
                    ).all().order_by('-created_on')[page_offset:page_limit + page_offset]

            serializer = PostListSerializer(post_list, many=True)
            post_listing = []
            for post_data in serializer.data:
                is_post_upvote = PostUpvote.objects.filter(post_id=post_data['post_id'], user_id=request.user_id).exists()
                is_post_save = UserSavePost.objects.filter(post_id=post_data['post_id'], user_id=request.user_id).exists()
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

            return Response({'data': post_listing}, status=status.HTTP_200_OK)
        else:
            return Response({'error':requestErrorMessagesFormate(validator.get_message())}, status=status.HTTP_200_OK)
    except Exception as exception:
        logerror('post/views.py/list_post', str(exception))
        return Response({'error':str(exception)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Get post comments
@api_view(['GET'])
@isAuthenticate
@RbacService('post:read')
def post_comments(request):
    """
    @api {GET} /v1/user/post/comments?page_limit=&page_offset=&post_id=&comment_id= Get Post comments
    @apiName Post comments
    @apiGroup Post
    @apiHeader {String} authorization Users unique access-token.
    @apiParam {integer} post_id query param
    @apiParam {integer} page_limit query param
    @apiParam {integer} page_offset query param
    @apiParam {integer} comment_id query param in case of comments of comment listing send comment_id other wise 0
    @apiSuccessExample {json} Success-Response:
    HTTP/1.1 200 OK
    {
        "data": [
            {
                "comment_id": 2,
                "is_comment_upvote": true,
                "comment": "hi",
                "comment_upvote": 5,
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
                "comment_id": 1,
                "is_comment_upvote": false,
                "comment": "hello",
                "comment_upvote": 2,
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
                "total_comments_on_comment": 2
            }
        ]
    }
    HTTP/1.2 200 OK Comment of comment listing on based on comment id
    {
        "data": [
            {
                "comment_id": 1,
                "user_id": 84,
                "comment": "hello yaar",
                "user_detail": {
                    "name": "Vivek Chaudhary",
                    "id": 84,
                    "email": "rits.chaudhary1992@gmail.com",
                    "profile_pic": ""
                }
            },
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
        ]
    }
    @apiErrorExample Error-Response:
    HTTP/1.1 404 Not Found
    {
        "error": "Post does not exist"
    }
    """
    try:
        validator = post_comments_validator(request.GET)
        valid = validator.validate()  # Validate the request
        if valid:
            post_id = int(request.GET['post_id'])
            comment_id = int(request.GET['comment_id'])
            page_limit = int(request.GET['page_limit'])
            page_offset = int(request.GET['page_offset'])
            if Post.objects.filter(post_id=post_id).exists():
                if comment_id:
                    post_comments_on_comment_details = PostCommentsOnComment.objects.filter(comment_id=comment_id).all()[page_offset:page_limit+page_offset]
                    post_comments_on_comment_serializer = PostCommentsOfCommentSerializer(post_comments_on_comment_details, many=True)
                    return_response = {
                        'data': post_comments_on_comment_serializer.data
                    }
                else:
                    post_comments_details = PostComments.objects.filter(post_id=post_id).all().order_by('-comment_upvote')[page_offset:page_limit+page_offset]
                    post_comment_serializer = PostCommentsSerializer(post_comments_details, many=True)
                    post_comment_data = post_comment_serializer.data
                    post_comments_data = []
                    for post_comment in post_comment_data:
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
                    return_response = {
                        'data': post_comments_data
                    }
                return Response(return_response, status=status.HTTP_200_OK)
            else:
                return Response({'error':Messages.INVALID_POST_ID}, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({'error':requestErrorMessagesFormate(validator.get_message())}, status=status.HTTP_200_OK)
    except Exception as exception:
        logerror('post/views.py/post_comments', str(exception))
        return Response({'error':str(exception)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Get list of users who has upvote post
@api_view(['GET'])
@isAuthenticate
@RbacService('post:read')
def upvote_users(request):
    """
    @api {GET} v1/user/post/list/upvote-users List of users who have upvote post
    @apiName List of users who have upvote post
    @apiGroup Post
    @apiHeader {String} Content-Type application/json
    @apiParam {integer} page_limit Page limit
    @apiParam {integer} page_offset Page offset
    @apiParam {string} data_id Id of `post` or `comment`
    @apiParam {string} data_type Type `post` or `comment`
    @apiSuccessExample {json} Success-Response:
    HTTP/1.1 200 OK
    {
        "data": [
            {
                "name": "test",
                "id": 12,
                "email": "test123@yopmail.com",
                "profile_pic": "",
                "is_interested": 1,
                "is_request_sent": false
            },
            {
                "name": "Test 03",
                "id": 2,
                "email": "test03@yopmail.com",
                "profile_pic": "profilepic.png",
                "is_interested": 0,
                "is_request_sent": false
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
        validator = UpvoteUsersListValidator(request.GET)
        valid = validator.validate()  # Validate the request
        if valid:
            page_limit = int(request.GET['page_limit'])
            page_offset = int(request.GET['page_offset'])
            data_id = int(request.GET['data_id'])
            data_type = request.GET['data_type']

            # Get logged in user id
            current_user_id = request.user_id

            # Get users list who have upvote the post
            if data_type == 'post':
                upvote_user_ids = PostUpvote.objects.filter(
                    post_id=data_id
                ).values_list(
                    'user_id',
                    flat=True
                ).distinct().order_by('user_id').reverse()

             # Get users list who have upvote the comment
            if data_type == 'comment':
                upvote_user_ids = PostCommentsUpvote.objects.filter(
                    comment_id=data_id
                ).values_list(
                    'user_id',
                    flat=True
                ).distinct().order_by('user_id').reverse()

            # Get logged in user interested users list
            user_interest_ids = UserInterest.objects.filter(
                user_id=current_user_id
            ).values_list(
                'interested_user_id',
                flat=True
            ).distinct().order_by('interested_user_id').reverse()

            # Get user details who have upvote the post
            user_list = User.objects.filter(
                id__in=upvote_user_ids,
                is_deleted=0
            ).values().order_by('id').reverse()[page_offset:page_offset+page_limit]
            serializer = SuggestedUsersSerializer(user_list, many=True)

            response = []
            for data in serializer.data:
                if data['id'] in user_interest_ids:
                    is_interested = 1
                else:
                    is_interested = 0

                is_request_sent = UserInterestsRequest.objects.filter(
                    user_id=current_user_id, interested_user_id=data['id']
                ).exists()

                response.append({
                    'name':data['name'],
                    'id':data['id'],
                    'email':data['email'],
                    'profile_pic':data['profile_pic'],
                    'is_interested':is_interested,
                    'is_request_sent': is_request_sent
                })            

            if len(response) > 0:

                return Response({'data':response}, status=status.HTTP_200_OK)
            else:
                return Response({'data':[]}, status=status.HTTP_200_OK)
        else:
            return Response({'error':requestErrorMessagesFormate(validator.get_message())}, status=status.HTTP_200_OK)
    except Exception as exception:
        logerror('post/views.py/upvote_users', str(exception))
        return Response({'error':str(exception)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# add post comment or comment of comment by user
@api_view(['POST'])
@isAuthenticate
@RbacService('post:comment:create')
def post_comment_add(request):
    """
    @api {POST} v1/user/post/comment/add add Post comments
    @apiName add post comments
    @apiGroup Post
    @apiHeader {String} authorization Users unique access-token.
    @apiParam {integer} post_id
    @apiParam {integer} comment_id comment_id value for comment on comment otherwise 0
    @apiParam {integer} type 1 for comment and 2 for comment on comment
    @apiParam {text} comment
    @apiSuccessExample {json} Success-Response:
    HTTP/1.1 201 OK
    {
        "comment_id": 9
    }
    @apiErrorExample Error-Response:
    HTTP/1.1 404 Not Found
    {
        "error": "Post does not exist"
    }
    """
    try:
        validator = post_comment_by_user_validator(request.data)
        valid = validator.validate()  # Validate the request
        if valid:
            if Post.objects.filter(post_id=request.data.get('post_id')).exists():
                # data message for notification

                data_message = {
                    "reference_id": 1,
                    'event_id': int(request.data.get('post_id'))
                }

                post = Post.objects.get(post_id=request.data.get('post_id'))
                user = User.objects.get(id=request.user_id)

                # Check comment profanity and update comment in DB
                profanity.load_censor_words()
                censored_text = profanity.censor(request.data.get('comment'))

                # type 1 for post comment 2 for comment of comment
                if int(request.data.get('type')) == 1:
                    PostComments.objects.create(
                        post_id=post,
                        user_id=user,
                        comment=censored_text
                    )
                    comment_obj = PostComments.objects.latest('comment_id')
                    comment_id = comment_obj.comment_id
                    response = {
                        "comment_id": comment_id
                    }
                else:
                    comment = PostComments.objects.get(comment_id=request.data.get('comment_id'))
                    PostCommentsOnComment.objects.create(
                        comment_id=comment,
                        user_id=user,
                        comment=censored_text
                    )
                    comment_obj = PostCommentsOnComment.objects.latest('id')
                    comment_on_comment_id = comment_obj.id
                    response = {
                        "comment_on_comment_id": comment_on_comment_id
                    }

                # Redis stuff
                redis_object = redis.Redis(EthosCommonConstants.REDIS_HOST) # Redis object
                redis_key = RedisCommon.post_details + str(request.data.get('post_id')) # Key in which we will store data

                # Check if already exist in Redis then update comments in redis
                if redis_object.get(redis_key):

                    # Get post comments
                    post_comments = PostComments.objects.filter(
                        post_id=request.data.get('post_id')
                    ).order_by('-comment_upvote')[:5]
                    serializer = PostCommentsSerializer(post_comments, many=True)

                    post_details = _pickle.loads(redis_object.get(redis_key))
                    post_details['comments'] = serializer.data
                    RedisCommon().set_data(redis_key, post_details)

                # Send Notification to post owner
                user_id = post.created_by.id
                if user_id != request.user_id:
                    data_message['body'] = user.name+Messages.COMMENT_POST_MESSAGE
                    data_message['title'] = Messages.COMMENT_POST_TITLE
                    device_tokens = GetNotification().getDeviceToken([user_id])

                    # add notification to list
                    GetNotification().addNotification(
                        user_id,
                        Messages.COMMENT_POST_TITLE,
                        user.name + Messages.COMMENT_POST_MESSAGE,
                        1,
                        int(request.data.get('post_id'))
                    )
                    
                    if len(device_tokens) > 0:

                        # send push notification to user
                        GetNotification().send_push_notification(
                            device_tokens,
                            Messages.COMMENT_POST_TITLE,
                            user.name+Messages.COMMENT_POST_MESSAGE,
                            data_message
                        )

                # Send Notification to interested user in post
                update_dict = {
                    "body": user.name+Messages.COMMENT_INTEREST_POST_MESSAGE,
                    "title": Messages.COMMENT_POST_TITLE
                }

                data_message.update(update_dict)
                interested_user_ids = list(PostReceiveNotification.objects.filter(post_id=int(request.data.get('post_id')), is_enabled=1).values_list('user_id', flat=True).distinct())
                device_tokens = GetNotification().getDeviceToken(interested_user_ids)

                for user_id in interested_user_ids:
                    GetNotification().addNotification(
                        user_id,
                        Messages.COMMENT_POST_TITLE,
                        user.name + Messages.COMMENT_INTEREST_POST_MESSAGE,
                        1,
                        int(request.data.get('post_id'))
                    )

                if len(device_tokens) > 0:

                    # send push notification to user
                    GetNotification().send_push_notification(
                        device_tokens,
                        Messages.COMMENT_POST_TITLE,
                        user.name + Messages.COMMENT_INTEREST_POST_MESSAGE,
                        data_message
                    )
                return Response(response, status=status.HTTP_201_CREATED)
            else:
                return Response({'error':Messages.INVALID_POST_ID}, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({'error':requestErrorMessagesFormate(validator.get_message())}, status=status.HTTP_200_OK)
    except Exception as exception:
        logerror('post/views.py/post_comment_add', str(exception))
        return Response({'error':str(exception)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# post upvote and comment upvote by user
@api_view(['POST'])
@isAuthenticate
@RbacService('post:write')
def post_comment_upvote(request):
    """
    @api {POST} v1/user/post/post-comment/upvote Upvote the post and comment
    @apiName Upvote comment and post
    @apiGroup Post
    @apiHeader {String} authorization Users unique access-token.
    @apiParam {integer} post_id required
    @apiParam {integer} comment_id comment_id value for comment upvote otherwise 0
    @apiParam {integer} type 1 for post upvote and 2 for comment upvote
    @apiSuccessExample {json} Success-Response:
    HTTP/1.1 201 OK
    {
        "post_upvote_count": 1
    }
    HTTP/2.1 201 OK
    {
        "comment_upvote_count": 0
    }
    @apiErrorExample Error-Response:
    HTTP/3.1 404 Not Found
    {
        "error": "Post does not exist"
    }
    """
    try:
        validator = post_upvote_validator(request.data)
        valid = validator.validate()  # Validate the request
        if valid:
            redis_object = redis.Redis(EthosCommonConstants.REDIS_HOST)  # Redis object

            if Post.objects.filter(post_id=request.data.get('post_id')).exists():
                post = Post.objects.get(post_id=request.data.get('post_id'))
                user = User.objects.get(id=request.user_id)
                # type 1 for post upvote 2 for comment upvote
                if int(request.data.get('type')) == 1:

                    post_upvote_users = RedisCommon.post_upvote_users + str(request.data.get('post_id'))
                    upvote_post_count = RedisCommon.upvote_post_count  + str(request.data.get('post_id'))

                    # check whether this user already upvote this post once.
                    post_upvote_count = PostUpvote.objects.filter(post_id=request.data.get('post_id'), user_id=request.user_id).count()
                    if post_upvote_count > 0:
                        PostUpvote.objects.filter(post_id=request.data.get('post_id'), user_id=request.user_id).delete()
                        Post.objects.filter(post_id=request.data.get('post_id')).update(upvote_count=F('upvote_count')-1)
                        post_values = Post.objects.filter(post_id=request.data.get('post_id')).values()
                        response = {
                            "post_upvote_count": post_values[0]['upvote_count']
                        }

                        # Remove upvote user from list
                        redis_object.lrem(post_upvote_users, 0, request.user_id)
                        redis_object.decr(upvote_post_count) # decrease upvote count

                        return Response(response, status=status.HTTP_200_OK)
                    PostUpvote.objects.create(
                        post_id=post,
                        user_id=user
                    )
                    Post.objects.filter(post_id=request.data.get('post_id')).update(upvote_count=F('upvote_count')+1)
                    post_values = Post.objects.filter(post_id=request.data.get('post_id')).values()

                    # Remove and then Add upvote user into list
                    redis_object.lrem(post_upvote_users, 0, request.user_id) # to protect duplicacy
                    redis_object.lpush(post_upvote_users, request.user_id)
                    redis_object.incr(upvote_post_count) # increase upvote count

                    response = {
                        "post_upvote_count": post_values[0]['upvote_count']
                    }
                else:

                    comment_upvote_users = RedisCommon.comment_upvote_users + str(request.data.get('comment_id'))
                    upvote_comment_count = RedisCommon.upvote_comment_count + str(request.data.get('comment_id'))

                    # check whether this user already upvote this post once.
                    comment_upvote_count = PostCommentsUpvote.objects.filter(comment_id=request.data.get('comment_id'), user_id=request.user_id).count()
                    if comment_upvote_count > 0:
                        PostCommentsUpvote.objects.filter(comment_id=request.data.get('comment_id'), user_id=request.user_id).delete()
                        PostComments.objects.filter(comment_id=request.data.get('comment_id')).update(comment_upvote=F('comment_upvote')-1)
                        post_comment_values = PostComments.objects.filter(comment_id=request.data.get('comment_id')).values()
                        response = {
                            "comment_upvote_count": post_comment_values[0]['comment_upvote']
                        }

                        # Remove upvote user from list
                        redis_object.lrem(comment_upvote_users, 0, request.user_id)
                        redis_object.decr(upvote_comment_count)  # decrease upvote count

                        return Response(response, status=status.HTTP_200_OK)
                    comment = PostComments.objects.get(comment_id=request.data.get('comment_id'))
                    PostCommentsUpvote.objects.create(
                        comment_id=comment,
                        user_id=user
                    )
                    PostComments.objects.filter(comment_id=request.data.get('comment_id')).update(comment_upvote=F('comment_upvote')+1)
                    post_comment_values = PostComments.objects.filter(comment_id=request.data.get('comment_id')).values()
                    response = {
                        "comment_upvote_count": post_comment_values[0]['comment_upvote']
                    }

                    # Remove and then Add upvote user into list
                    redis_object.lrem(comment_upvote_users, 0, request.user_id)  # to protect duplicacy
                    redis_object.lpush(comment_upvote_users, request.user_id)
                    redis_object.incr(upvote_comment_count)  # increase upvote count

                return Response(response, status=status.HTTP_200_OK)
            else:
                return Response({'error':Messages.INVALID_POST_ID}, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({'error':requestErrorMessagesFormate(validator.get_message())}, status=status.HTTP_200_OK)
    except Exception as exception:
        logerror('post/views.py/post_comment_upvote', str(exception))
        return Response({'error':str(exception)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# engagement count by cause id
def causes_engagement_count(cause_id, post_ids = []):

    try:
        if len(post_ids) > 0:
            return PostCauses.objects.filter(cause_id=cause_id, post_id__in=post_ids).count()

        post_ids = PostCauses.objects.filter(
            cause_id=cause_id
        ).values_list('post_id', flat=True).distinct()

        return Post.objects.filter(post_id__in=post_ids, is_active=1).count()
    except Exception as exception:
        logerror('post/views.py/causes_engagement_count', str(exception))
        return Response({'error':str(exception)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)    

# engagement count by sub cause id
def sub_causes_engagement_count(subcause_id, post_ids = []):

    try:
        if len(post_ids) > 0:
            return PostSubCauses.objects.filter(subcause_id=subcause_id, post_id__in=post_ids).count()

        post_ids = PostSubCauses.objects.filter(
            subcause_id=subcause_id
        ).values_list('post_id', flat=True).distinct()

        return Post.objects.filter(post_id__in=post_ids, is_active=1).count()
    except Exception as exception:
        logerror('post/views.py/sub_causes_engagement_count', str(exception))
        return Response({'error':str(exception)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)    


# get user based causes sub causes list
@api_view(['GET'])
@isAuthenticate
@RbacService('post:read')
def user_causes_list(request):
    """
    @api {GET} v1/user/post/causes/subcauses Cause subcauses list by user
    @apiName Cause subcauses list bu User
    @apiGroup Post
    @apiHeader {String} authorization Users unique access-token
    @apiSuccessExample {json} Success-Response:
    HTTP/1.1 200 OK
    {
        "user_causes": [
            {
                "id": 177,
                "cause": {
                    "cause_id": "1",
                    "cause_name": "Environment",
                    "cause_image": null
                },
                "engagement_count": 7
            },
            {
                "id": 178,
                "cause": {
                    "cause_id": "2",
                    "cause_name": "Child Welfare",
                    "cause_image": null
                },
                "engagement_count": 6
            }
        ],
        "user_sub_causes": [
            {
                "id": 238,
                "sub_causes": {
                    "sub_cause_id": 1,
                    "sub_cause_name": "Forest",
                    "sub_cause_image": null,
                    "causes_detail": {
                        "cause_id": "1",
                        "cause_name": "Environment",
                        "cause_image": null
                    }
                },
                "engagement_count": 7
            },
            {
                "id": 239,
                "sub_causes": {
                    "sub_cause_id": 2,
                    "sub_cause_name": "Activist",
                    "sub_cause_image": null,
                    "causes_detail": {
                        "cause_id": "1",
                        "cause_name": "Environment",
                        "cause_image": null
                    }
                },
                "engagement_count": 7
            },
            {
                "id": 240,
                "sub_causes": {
                    "sub_cause_id": 3,
                    "sub_cause_name": "Women Subcauses 1",
                    "sub_cause_image": null,
                    "causes_detail": {
                        "cause_id": "3",
                        "cause_name": "Women",
                        "cause_image": null
                    }
                },
                "engagement_count": 7
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
        if UserCauses.objects.filter(user_id=request.user_id).exists():

            user_causes = UserCauses.objects.filter(user_id=request.user_id).all()  # fetch the from database
            causes_serializer = UserCauseSerializer(user_causes, many=True)  # serialize the data
            user_causes = []
            for cause in causes_serializer.data:
                ordered_cause = dict(OrderedDict(cause))
                user_causes.append(
                    {
                        "id":ordered_cause['id'],
                        "cause": ordered_cause['causes'],
                        "engagement_count": causes_engagement_count(ordered_cause['causes_id'])
                    }
                )
            user_sub_causes = UserSubCauses.objects.filter(user_id=request.user_id).all()
            sub_causes_serializer = UserSubCausesSerializer(user_sub_causes, many=True)  # serialize the data
            user_sub_causes_array = []
            for sub_cause in sub_causes_serializer.data:
                ordered_sub_cause = dict(OrderedDict(sub_cause))
                user_sub_causes_array.append(
                    {
                        "id":ordered_sub_cause['id'],
                        "sub_causes": ordered_sub_cause['sub_causes'],
                        "engagement_count": sub_causes_engagement_count(ordered_sub_cause['sub_causes_id'])
                    }
                )
            response = {
                'user_causes': user_causes,
                'user_sub_causes': user_sub_causes_array
            }

            return Response({'data':response}, status=status.HTTP_200_OK)
        else:
            return Response({'data':[]}, status=status.HTTP_200_OK)
    except Exception as exception:
        logerror('post/views.py/user_causes_list', str(exception))
        return Response({'error':str(exception)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# save post by user
@api_view(['POST'])
@isAuthenticate
@RbacService('post:save')
def user_post_save(request):
    """
    @api {POST} v1/user/post/save Save Post
    @apiName Save Post
    @apiGroup Post
    @apiHeader {String} authorization Users unique access-token.
    @apiParam {integer} post_id
    @apiSuccessExample {json} Success-Response:
    HTTP/1.1 200 OK
    {
        "save_post_id": 1
    }
    @apiErrorExample Success-Response:
    HTTP/1.1 200 OK
    {
        "message": "Post removed from saved post section"
    }
    """
    try:
        validator = SavePostValidator(request.data)
        valid = validator.validate()  # Validate the request
        if valid:
            user_id = request.user_id
            post_id = request.data.get('post_id')

            redis_object = redis.Redis(EthosCommonConstants.REDIS_HOST)  # Redis object
            redis_key = RedisCommon.save_post_users + str(post_id)

            if UserSavePost.objects.filter(user_id=user_id, post_id=post_id).exists():
                UserSavePost.objects.filter(user_id=user_id, post_id=post_id).delete()

                # Remove upvote user from list
                redis_object.lrem(redis_key, 0, user_id)
                redis_object.decr(RedisCommon.user_saved_post_count + str(user_id))  # decrease upvote count

                return Response({'message':Messages.REMOVE_POST_SAVED}, status=status.HTTP_200_OK)
            user_obj = User.objects.get(id=user_id)
            post_obj = Post.objects.get(post_id=post_id)
            UserSavePost.objects.create(
                user_id = user_obj,
                post_id = post_obj
            )
            user_save_post_obj = UserSavePost.objects.latest('id')

            # Remove and then Add upvote user into list
            redis_object.lrem(redis_key, 0, request.user_id)  # to protect duplicacy
            redis_object.lpush(redis_key, request.user_id)
            redis_object.incr(RedisCommon.user_saved_post_count + str(user_id))  # increase upvote count

            return Response({'save_post_id':user_save_post_obj.id}, status=status.HTTP_200_OK)
        else:
            return Response({'error':requestErrorMessagesFormate(validator.get_message())}, status=status.HTTP_200_OK)
    except Exception as exception:
        logerror('post/views.py/user_post_save', str(exception))
        return Response({'error':str(exception)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# report post and report user
@api_view(['POST'])
@isAuthenticate
@RbacService('report:post')
def report_post(request):
    """
    @api {POST} v1/user/post/report Report post
    @apiName Report Post
    @apiGroup Post
    @apiHeader {String} authorization Users unique access-token.
    @apiParam {integer} post_id id of post which you want to report
    @apiParam {integer} reason_id reason id from reason list
    @apiSuccessExample {json} Success-Response:
    HTTP/1.1 200 OK
    {
        "reported_id": 2
    }
    HTTP/1.1 200 OK
    {
        "message": "You have already report this post"
    }
    """
    try:
        validator = ReportPostValidator(request.data)
        valid = validator.validate()  # Validate the request
        if valid:
            logged_in_user_id = request.user_id
            reason_id = request.data.get('reason_id')
            post_id = request.data.get('post_id')

            # if user alreday reported this post than return
            if ReportedContent.objects.filter(content_id=post_id, reported_by=logged_in_user_id, content_type='post').exists():
                return Response({'message':Messages.ALREADY_REPORT_POST}, status=status.HTTP_200_OK)
            logged_in_user_obj = User.objects.get(id=logged_in_user_id)

            # insert report objects
            ReportedContent.objects.create(
                content_id=post_id,
                content_type='post',
                reported_by=logged_in_user_obj,
                reason_id=reason_id
            )
            reported_id = ReportedContent.objects.latest('id').id
            return Response({'reported_id': reported_id}, status=status.HTTP_200_OK)
        else:
            return Response({'error':requestErrorMessagesFormate(validator.get_message())}, status=status.HTTP_200_OK)
    except Exception as exception:
        logerror('post/views.py/report_post', str(exception))
        return Response({'error':str(exception)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@isAuthenticate
@RbacService('post:read')
def report_option_list(request):
    """
    @api {GET} v1/user/post/report/list?page_limit=&page_offset= Report options list
    @apiName Report options list
    @apiGroup Post
    @apiHeader {String} authorization Users unique access-token
    @apiHeader {integer} page_limit
    @apiHeader {integer} page_offset
    @apiHeader {string} report_type `post` for Post Report Listing
                                    `user` for User Report Listing
    @apiSuccessExample {json} Success-Response:
    HTTP/1.1 200 OK
    {
        "data": [
            {
                "id": 5,
                "reason_name": "Report reason 1"
            },
            {
                "id": 6,
                "reason_name": "Report reason 2"
            },
            {
                "id": 7,
                "reason_name": "Report reason 3"
            },
            {
                "id": 8,
                "reason_name": "Report reason 4"
            }
        ]
    }
    HTTP/1.1 200 OK
    {
        "data": []
    }
    """
    try:
        validator = ReportReasonListValidator(request.GET)
        valid = validator.validate()  # Validate the request
        if valid:
            page_limit = int(request.GET['page_limit'])
            page_offset = int(request.GET['page_offset'])
            report_type = request.GET['report_type']
            if report_type == 'post':
                reason_info = ReportReasonPost.objects.filter().all()[page_offset:page_limit+page_offset]
                serializer = ReportReasonPostListSerializer(reason_info, many=True)
                return Response({'data':serializer.data}, status=status.HTTP_200_OK)
            if report_type == 'user':
                reason_info = ReportReasonUser.objects.filter().all()[page_offset:page_limit+page_offset]
                serializer = ReportReasonUserListSerializer(reason_info, many=True)
                return Response({'data':serializer.data}, status=status.HTTP_200_OK)
        else:
            return Response({'error':requestErrorMessagesFormate(validator.get_message())}, status=status.HTTP_200_OK)
    except Exception as exception:
        logerror('post/views.py/report_option_list', str(exception))
        return Response({'error':str(exception)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Check keywords profanity
def check_keywords_contains_profanity( post_keywords):
    if len(post_keywords)> 0:
        for keyword in post_keywords:
            if profanity.contains_profanity(keyword):
                return True
    return False

# report post and report user
@api_view(['POST'])
@isAuthenticate
@RbacService('post:notification')
def receive_post_notification(request):
    """
    @api {POST} v1/user/post/receive/notification Receive Post notification
    @apiName Receive Post notification
    @apiGroup Post
    @apiHeader {String} authorization Users unique access-token.
    @apiParam {integer} post_id id of post which you want to receive notification
    @apiSuccessExample {json} Success-Response:
    HTTP/1.1 200 OK
    {
        "message": "Enable notification of this post"
    }
    HTTP/1.1 200 OK
    {
        "message": "Disable notification of this post"
    }
    """
    try:
        validator = PostReceiveNotificationValidator(request.data)
        valid = validator.validate()  # Validate the request
        if valid:
            logged_in_user_id = request.user_id
            post_id = request.data.get('post_id')
            if PostReceiveNotification.objects.filter(user_id=logged_in_user_id, post_id=post_id).exists():
                post_receive_obj = PostReceiveNotification.objects.filter(user_id=logged_in_user_id, post_id=post_id).values()
                # if user alreday enable the receive notification button then disbale it

                status_to_update = 0
                msg = Messages.DISABLE_POST_NOTIFICATION
                # if user disable the receive notification button then enable it

                if post_receive_obj[0]['is_enabled'] == 0:
                    status_to_update = 1
                    msg = Messages.ENABLE_POST_NOTIFICATION
                # update status of post notification

                PostReceiveNotification.objects.filter(
                    user_id=logged_in_user_id, post_id=post_id
                ).update(is_enabled=status_to_update)
                return Response({'message': msg}, status=status.HTTP_200_OK)
            
            # if new post notification added
            user_obj = User.objects.get(id=logged_in_user_id)
            post_obj = Post.objects.get(post_id=post_id)
            PostReceiveNotification.objects.create(
                user_id=user_obj,
                post_id=post_obj
            )
            return Response({'message': Messages.ENABLE_POST_NOTIFICATION}, status=status.HTTP_200_OK)
        else:
            return Response({'error': requestErrorMessagesFormate(validator.get_message())}, status=status.HTTP_200_OK)
    except Exception as exception:
        logerror('post/views.py/receive_post_notification', str(exception))
        return Response({'error': str(exception)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

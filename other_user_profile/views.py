from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status
from config.messages import Messages
from utility.requestErrorFormate import requestErrorMessagesFormate
from utility.authMiddleware import isAuthenticate
from utility.rbacService import RbacService
from .requestSchema import (OtherUserProfile, OtherUserPosts,
                            ReportUserProfile, OtherUserSavedPostListValidator)
from .serializers import OtherUserBasicDetailsSerializer, OtherUserAllDetailsSerializer
from .models import ReportReasonUser, ReportedContent
from users.models import User, UserBlockedContacts, UserCauses, UserSubCauses
from user_interest.models import UserInterest, UserInterestsRequest
from post.models import Post, PostUpvote, UserSavePost, PostCommentsUpvote, UserSavePost
from post.serializers import PostListSerializer
from user_interest.serializers import SuggestedUsersSerializer
from utility.loggerService import logerror
from ethos_network.settings import EthosCommonConstants
import redis
import _pickle
from utility.redisCommon import RedisCommon


# Create your views here.
# get other user's profile
@api_view(['GET'])
@isAuthenticate
@RbacService('user:read')
def other_user_profile(request):
    """
    @api {GET} v1/other/user/basic/profile?user_id= Get Other User's basic information
    @apiName Get Other User's basic information
    @apiGroup Other User
    @apiHeader {String} authorization Users unique access-token
    @apiHeader {integer} user_id User id
    @apiSuccessExample {json} Success-Response:
    HTTP/1.1 200 OK
    {
        "id": 102,
        "name": "Nikhil",
        "profile_pic": "profilepic.png",
        "is_admin_verified": 0,
        "is_account_private": 0,
        "is_saved_post_public": 1,
        "saved_post_count": 0,
        "added_as_interested": 0,
        "interests_count": 0,
        "is_blocked": false,
        "is_add_as_interest": false,
        "is_request_sent": true
    }
    """
    try:
        # test git 
        validator = OtherUserProfile(request.GET)
        valid = validator.validate()  # Validate the request
        if valid:
            current_user_id = request.user_id
            user_id = request.GET['user_id']
            if UserBlockedContacts.objects.filter(user_id=user_id, blocked_user_id=current_user_id).exists():
                return Response({'message': Messages.YOU_BLOCKED_BY_USER}, status=status.HTTP_200_OK)
            user_info = User.objects.filter(id=user_id)
            if user_info:
                is_blocked = UserBlockedContacts.objects.filter(user_id=current_user_id, blocked_user_id=user_id).exists()
                is_add_as_interest = UserInterest.objects.filter(user_id=current_user_id, interested_user_id=user_id).exists()
                is_user_reported = ReportedContent.objects.filter(content_id=user_id, reported_by=current_user_id, content_type='user').exists()
                is_request_sent = UserInterestsRequest.objects.filter(user_id=current_user_id, interested_user_id=user_id).exists()
                serializer = OtherUserBasicDetailsSerializer(user_info, many=True)
                serializer.data[0].update({'is_blocked': is_blocked})
                serializer.data[0].update({'is_add_as_interest': is_add_as_interest})
                serializer.data[0].update({'is_user_reported': is_user_reported})
                serializer.data[0].update({'is_request_sent': is_request_sent})
                if User.objects.filter(id=user_id, is_account_private=0).exists():
                    if UserInterest.objects.filter(user_id=current_user_id, interested_user_id=user_id).exists():
                        all_serializer = OtherUserAllDetailsSerializer(user_info, many=True)
                        if all_serializer.data[0]['is_location_public'] == 0:
                            del all_serializer.data[0]['location']
                        serializer.data[0].update(all_serializer.data[0])
                return Response(serializer.data[0], status=status.HTTP_200_OK)
            else:
                return Response({}, status=status.HTTP_200_OK)
        else:
            return Response({'error':requestErrorMessagesFormate(validator.get_message())}, status=status.HTTP_200_OK)
    except Exception as exception:
        logerror('other_user_profile/views.py/other_user_profile', str(exception))
        return Response({'error':str(exception)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# get other user's profile
@api_view(['GET'])
@isAuthenticate
@RbacService('post:read')
def other_user_posts(request):
    """
    @api {GET} v1/other/user/posts?user_id=&page_limit=&page_offset= Get Other User's post listing
    @apiName Get Other User's post listing
    @apiGroup Other User
    @apiHeader {String} authorization Users unique access-token
    @apiHeader {integer} user_id User id
    @apiHeader {integer} page_limit
    @apiHeader {integer} page_offset
    @apiSuccessExample {json} Success-Response:
    HTTP/1.1 200 OK
    {
        "data": [
            {
                "post_id": 7,
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
                "created_by": 102,
                "total_comment": 0,
                "user_detail": {
                    "name": "Nikhil",
                    "id": 102,
                    "email": "nikhil1@techaheadcorp.com",
                    "profile_pic": "profilepic.png"
                },
                "comments": [],
                "attachements": [
                    {
                        "id": 19,
                        "name": "abc.png",
                        "video_thumbnail": null,
                        "type": 1
                    },
                    {
                        "id": 20,
                        "name": "xyz.png",
                        "video_thumbnail": "xyz.png",
                        "type": 2
                    },
                    {
                        "id": 21,
                        "name": "xyz.png",
                        "video_thumbnail": "xyz.png",
                        "type": 2
                    }
                ],
                "causes": [
                    {
                        "id": 20,
                        "cause_detail": {
                            "cause_id": "2",
                            "cause_name": "Child Welfare",
                            "cause_image": null,
                            "cause_color": null
                        }
                    },
                    {
                        "id": 21,
                        "cause_detail": {
                            "cause_id": "3",
                            "cause_name": "Women",
                            "cause_image": null,
                            "cause_color": null
                        }
                    }
                ]
            },
            {
                "post_id": 8,
                "title": "Campgain post new one today",
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
                "created_by": 102,
                "total_comment": 0,
                "user_detail": {
                    "name": "Nikhil",
                    "id": 102,
                    "email": "nikhil1@techaheadcorp.com",
                    "profile_pic": "profilepic.png"
                },
                "comments": [],
                "attachements": [
                    {
                        "id": 22,
                        "name": "abc.png",
                        "video_thumbnail": null,
                        "type": 1
                    },
                    {
                        "id": 23,
                        "name": "xyz.png",
                        "video_thumbnail": "xyz.png",
                        "type": 2
                    },
                    {
                        "id": 24,
                        "name": "xyz.png",
                        "video_thumbnail": "xyz.png",
                        "type": 2
                    }
                ],
                "causes": [
                    {
                        "id": 22,
                        "cause_detail": {
                            "cause_id": "1",
                            "cause_name": "Environment",
                            "cause_image": null,
                            "cause_color": null
                        }
                    },
                    {
                        "id": 23,
                        "cause_detail": {
                            "cause_id": "2",
                            "cause_name": "Child Welfare",
                            "cause_image": null,
                            "cause_color": null
                        }
                    },
                    {
                        "id": 24,
                        "cause_detail": {
                            "cause_id": "3",
                            "cause_name": "Women",
                            "cause_image": null,
                            "cause_color": null
                        }
                    }
                ]
            }
        ]
    }
    """
    try:
        validator = OtherUserPosts(request.GET)
        valid = validator.validate()  # Validate the request
        if valid:
            current_user_id = request.user_id
            user_id = int(request.GET['user_id'])
            page_limit = int(request.GET['page_limit'])
            page_offset = int(request.GET['page_offset'])
            if UserBlockedContacts.objects.filter(user_id=user_id, blocked_user_id=current_user_id).exists():
                return Response({'message': Messages.YOU_BLOCKED_BY_USER}, status=status.HTTP_200_OK)
            # post listing
            post_list = Post.objects.filter(created_by=user_id, is_active=1).all().order_by('-created_on')[page_offset:page_limit+page_offset]
            serializer = PostListSerializer(post_list, many=True)
            post_listing = []
            for post_data in serializer.data:
                is_post_upvote = PostUpvote.objects.filter(post_id=post_data['post_id'], user_id=current_user_id).exists()
                is_post_save = UserSavePost.objects.filter(post_id=post_data['post_id'], user_id=current_user_id).exists()
                post_comments_data = []
                for post_comment in post_data['comments']:
                    is_comment_upvote = PostCommentsUpvote.objects.filter(comment_id=post_comment['comment_id'], user_id=current_user_id).exists()
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
        logerror('other_user_profile/views.py/other_user_posts', str(exception))
        return Response({'error':str(exception)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# get other user's profile
@api_view(['GET'])
@isAuthenticate
@RbacService('user:read')
def suggessted_users_list(request):
    """
    @api {GET} v1/other/user/suggestion/list Get suggestion user list
    @apiName Get suggestion user list
    @apiGroup Other User
    @apiHeader {String} authorization Users unique access-token
    @apiHeader {integer} user_id User id
    @apiHeader {integer} page_limit
    @apiHeader {integer} page_offset
    @apiSuccessExample {json} Success-Response:
    HTTP/1.1 200 OK
    {
        "data": [
            {
                "name": "Jitendra Singh",
                "id": 2,
                "email": "test03@yopmail.com",
                "profile_pic": "profilepic.png",
                "is_request_sent": false
            },
            {
                "name": "Test 06",
                "id": 3,
                "email": "test06@yopmail.com",
                "profile_pic": "profilepic.png",
                "is_request_sent": false
            }
        ]
    }
    """
    try:
        validator = OtherUserPosts(request.GET)
        valid = validator.validate()  # Validate the request
        if valid:
            current_user_id = request.user_id
            user_id = int(request.GET['user_id'])
            page_limit = int(request.GET['page_limit'])
            page_offset = int(request.GET['page_offset'])

            if UserBlockedContacts.objects.filter(user_id=user_id, blocked_user_id=current_user_id).exists():
                return Response({'message': Messages.YOU_BLOCKED_BY_USER}, status=status.HTTP_200_OK)

            # get causes ids of logged in user and user which profile is seen by logged in user
            causes_ids = list(UserCauses.objects.filter(
                user_id__in=[current_user_id, user_id]
            ).values_list('causes_id', flat=True).distinct())

            # get sub-causes ids of logged in user and user which profile is seen by logged in user
            subcauses_ids = list(UserSubCauses.objects.filter(
                user_id__in=[current_user_id, user_id]
            ).values_list('sub_causes_id', flat=True).distinct())

            # get causes user ids
            causes_user_ids = list(UserCauses.objects.filter(
                causes_id__in=causes_ids
            ).values_list('user_id', flat=True).distinct())

            # get sub-causes user ids
            subcauses_user_ids = list(UserSubCauses.objects.filter(
                sub_causes_id__in=subcauses_ids
            ).values_list('user_id', flat=True).distinct())

            # users who added user as interests
            users_added_as_interests = list(UserInterest.objects.filter(
                interested_user_id=user_id
            ).values_list('user_id', flat=True).distinct())

            # user ids from causes_user_ids and subcauses_user_ids
            causes_subcauses_interest_user_ids = list(set(causes_user_ids + subcauses_user_ids + users_added_as_interests))

            # get user ids of users whom logged in user already added as interest( need to be exclued from user_ids)
            added_as_interest_user_ids = list(UserInterest.objects.filter(
                user_id=current_user_id
            ).values_list('interested_user_id', flat=True).distinct())
            added_as_interest_user_ids.append(current_user_id)
            added_as_interest_user_ids.append(user_id)
            # user ids from causes_user_ids and subcauses_user_ids
            final_user_ids = list(set(causes_subcauses_interest_user_ids) - set(added_as_interest_user_ids))

            user_info = User.objects.filter(
                id__in=final_user_ids,
                is_active=1,
                is_deleted=0,
                role=3
            )[page_offset:page_limit+page_offset]

            response = []
            if user_info:

                # Get logged in user interested users list
                user_interest_ids = UserInterest.objects.filter(
                    user_id=current_user_id
                ).values_list(
                    'interested_user_id',
                    flat=True
                ).distinct().order_by('interested_user_id').reverse()

                serializer = SuggestedUsersSerializer(user_info, many=True)

                for data in serializer.data:
                    if data['id'] in user_interest_ids:
                        is_interested = 1
                    else:
                        is_interested = 0

                    is_request_sent = UserInterestsRequest.objects.filter(
                        user_id=current_user_id, interested_user_id=data['id']
                    ).exists()

                    response.append({
                        'name': data['name'],
                        'id': data['id'],
                        'email': data['email'],
                        'profile_pic': data['profile_pic'],
                        'is_request_sent': is_request_sent
                    })

                return Response({'data':response}, status=status.HTTP_200_OK)
            else:
                return Response({'data':[]}, status=status.HTTP_200_OK)
        else:
            return Response({'error':requestErrorMessagesFormate(validator.get_message())}, status=status.HTTP_200_OK)
    except Exception as exception:
        logerror('other_user_profile/views.py/suggessted_users_list', str(exception))
        return Response({'error':str(exception)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# get other user's full profile if user has public account
@api_view(['GET'])
@isAuthenticate
@RbacService('user:read')
def other_user_full_profile(request):
    """
    @api {GET} v1/other/user/full/profile?user_id= Get Other User's full information
    @apiName Get Other User's full information
    @apiGroup Other User
    @apiHeader {String} authorization Users unique access-token
    @apiHeader {integer} user_id User id
    @apiSuccessExample {json} Success-Response:
    HTTP/1.1 200 OK
    {
        "id": 102,
        "name": "Nikhil",
        "profile_pic": "profilepic.png",
        "dob": "1995",
        "location": null,
        "bio": null,
        "age": null,
        "is_admin_verified": 0,
        "is_location_public": 1,
        "user_causes": [
            {
                "id": 177,
                "causes_id": 1,
                "causes": {
                    "cause_id": "1",
                    "cause_name": "Environment",
                    "cause_image": null,
                    "cause_color": null
                }
            },
            {
                "id": 178,
                "causes_id": 2,
                "causes": {
                    "cause_id": "2",
                    "cause_name": "Child Welfare",
                    "cause_image": null,
                    "cause_color": null
                }
            }
        ],
        "user_sub_causes": [
            {
                "id": 238,
                "sub_causes_id": 1,
                "sub_causes": {
                    "sub_cause_id": 1,
                    "sub_cause_name": "Forest",
                    "sub_cause_image": null,
                    "causes_detail": {
                        "cause_id": "1",
                        "cause_name": "Environment",
                        "cause_image": null,
                        "cause_color": null
                    }
                }
            },
            {
                "id": 239,
                "sub_causes_id": 2,
                "sub_causes": {
                    "sub_cause_id": 2,
                    "sub_cause_name": "Activist",
                    "sub_cause_image": null,
                    "causes_detail": {
                        "cause_id": "1",
                        "cause_name": "Environment",
                        "cause_image": null,
                        "cause_color": null
                    }
                }
            },
            {
                "id": 240,
                "sub_causes_id": 3,
                "sub_causes": {
                    "sub_cause_id": 3,
                    "sub_cause_name": "Women Subcauses 1",
                    "sub_cause_image": null,
                    "causes_detail": {
                        "cause_id": "3",
                        "cause_name": "Women",
                        "cause_image": null,
                        "cause_color": null
                    }
                }
            }
        ],
        "is_add_as_interest": true
    }
    HTTP/1.1 200 OK
    {
        "message": "This User blocked you"
    }
    {
        "message": "User has a private account"
    }
    {
        "message": "You have not added this user as interest"
    }
    """
    try:
        validator = OtherUserProfile(request.GET)
        valid = validator.validate()  # Validate the request
        if valid:

            current_user_id = request.user_id
            user_id = int(request.GET['user_id'])

            redis_object = redis.Redis(EthosCommonConstants.REDIS_HOST)  # Redis object
            redis_key = RedisCommon.other_user_profile + str(user_id)  # Key in which we will store data

            # Check if already exist in Redis then don't need to call SQL
            if redis_object.get(redis_key):
                print('Getting data from redis...')
                other_user_details = _pickle.loads(redis_object.get(redis_key))
                user_interests_users = redis_object.lrange(RedisCommon.user_interests_users + str(current_user_id), 0, -1)

                # check if user has already added as interested
                is_add_as_interest = False
                for other_user_id in user_interests_users:
                    if user_id == int(other_user_id.decode('utf-8')):
                        is_add_as_interest = True
                        break

                other_user_details['is_add_as_interest'] = is_add_as_interest

                # Get updated causes
                for cause_detail in other_user_details['user_causes']:
                    cause_id = cause_detail['causes']['cause_id']
                    cause_redis_data = RedisCommon().get_data(RedisCommon.cause_details + str(cause_id))
                    if cause_redis_data:
                        cause_detail['causes'] = _pickle.loads(cause_redis_data)

                # Get updated subcause
                for subcause_detail in other_user_details['user_sub_causes']:
                    subcause_id = subcause_detail['sub_causes']['sub_cause_id']
                    subcause_redis_data = RedisCommon().get_data(RedisCommon.subcause_details + str(subcause_id))

                    # Update cause data in sub-causes array
                    cause_details = subcause_detail['sub_causes']['causes_detail']
                    cause_id = cause_details['cause_id']
                    cause_redis_data = RedisCommon().get_data(RedisCommon.cause_details + str(cause_id))
                    if cause_redis_data:
                        subcause_detail['sub_causes']['causes_detail'] = _pickle.loads(cause_redis_data)

                    if subcause_redis_data:
                        subcause_detail['sub_causes'] = _pickle.loads(subcause_redis_data)
                        subcause_detail['sub_causes']['causes_detail'] = cause_details

                return Response(other_user_details, status=status.HTTP_200_OK)

            if UserBlockedContacts.objects.filter(user_id=user_id, blocked_user_id=current_user_id).exists():
                return Response({'message': Messages.YOU_BLOCKED_BY_USER}, status=status.HTTP_200_OK)

            if User.objects.filter(id=user_id, is_account_private=1).exists():
                return Response({'message': Messages.USER_HAS_PRIVATE_ACCOUNT}, status=status.HTTP_200_OK)

            if not UserInterest.objects.filter(user_id=current_user_id, interested_user_id=user_id).exists():
                return Response({'message': Messages.ADD_AS_INTEREST_BEFORE}, status=status.HTTP_200_OK)

            user_info = User.objects.filter(id=user_id)
            if user_info:
                is_add_as_interest = UserInterest.objects.filter(user_id=current_user_id, interested_user_id=user_id).exists()
                serializer = OtherUserAllDetailsSerializer(user_info, many=True)
                serializer.data[0].update({'is_add_as_interest': is_add_as_interest})

                if serializer.data[0]['is_location_public'] == 0:
                    del serializer.data[0]['location']

                # Set data in Redis
                RedisCommon().set_data(redis_key, serializer.data[0])

                return Response(serializer.data[0], status=status.HTTP_200_OK)
            else:
                return Response({}, status=status.HTTP_200_OK)
        else:
            return Response({'error':requestErrorMessagesFormate(validator.get_message())}, status=status.HTTP_200_OK)
    except Exception as exception:
        logerror('other_user_profile/views.py/other_user_full_profile', str(exception))
        return Response({'error':str(exception)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# report post and report user
@api_view(['POST'])
@isAuthenticate
@RbacService('report:user')
def report_user(request):
    """
    @api {POST} v1/other/user/report Report other user
    @apiName Report other user
    @apiGroup Other User
    @apiHeader {String} authorization Users unique access-token.
    @apiParam {integer} reason_id reason id from reasons list
    @apiParam {integer} user_id which you want to report
    @apiSuccessExample {json} Success-Response:
    HTTP/1.1 200 OK
    {
        "reported_id": 3
    }
    HTTP/1.1 200 OK
    {
        "message": "You have already report this user"
    }
    """
    try:
        validator = ReportUserProfile(request.data)
        valid = validator.validate()  # Validate the request
        if valid:
            logged_in_user_id = request.user_id
            reason_id = request.data.get('reason_id')
            user_id = request.data.get('user_id')

            # if user alreday reported this user than return
            if ReportedContent.objects.filter(content_id=user_id, reported_by=logged_in_user_id, content_type='user').exists():
                return Response({'message':Messages.ALREADY_REPORT_USER}, status=status.HTTP_200_OK)
            user_obj = User.objects.get(id=user_id)
            logged_in_user_obj = User.objects.get(id=logged_in_user_id)

            # insert report objects
            ReportedContent.objects.create(
                content_type='user',
                content_id=user_id,
                reported_by=logged_in_user_obj,
                reason_id=reason_id
            )
            reported_id = ReportedContent.objects.latest('id').id
            return Response({'reported_id': reported_id}, status=status.HTTP_200_OK)
        else:
            return Response({'error':requestErrorMessagesFormate(validator.get_message())}, status=status.HTTP_200_OK)
    except Exception as exception:
        logerror('other_user_profile/views.py/report_user', str(exception))
        return Response({'error':str(exception)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# get other user's profile
@api_view(['GET'])
@isAuthenticate
@RbacService('post:read')
def other_user_saved_posts(request):
    """
    @api {GET} v1/other/user/saved/posts?user_id=&page_limit=&page_offset= Get Other User's saved post listing
    @apiName Get Other User's saved post listing
    @apiGroup Other User
    @apiHeader {String} authorization Users unique access-token
    @apiHeader {integer} user_id User id
    @apiHeader {integer} page_limit
    @apiHeader {integer} page_offset
    @apiSuccessExample {json} Success-Response:
    HTTP/1.1 200 OK
    {
        "data": [
            {
                "post_id": 1,
                "title": "Campgain post new one",
                "is_post_upvote": false,
                "is_post_save": false,
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
                            "cause_color": null
                        }
                    },
                    {
                        "id": 46,
                        "cause_detail": {
                            "cause_id": "3",
                            "cause_name": "Women",
                            "cause_image": null,
                            "cause_color": null
                        }
                    }
                ]
            }
        ]
    }
    HTTP/1.1 200 OK
    {
        "message": "You have been blocked by this user"
    }
    HTTP/1.1 200 OK
    {
        "message": "Saved posts are private"
    }
    """
    try:
        validator = OtherUserSavedPostListValidator(request.GET)
        valid = validator.validate()  # Validate the request
        if valid:
            current_user_id = request.user_id
            user_id = int(request.GET['user_id'])
            page_limit = int(request.GET['page_limit'])
            page_offset = int(request.GET['page_offset'])
            # if user blocked logged in user
            if UserBlockedContacts.objects.filter(user_id=user_id, blocked_user_id=current_user_id).exists():
                return Response({'message': Messages.YOU_BLOCKED_BY_USER}, status=status.HTTP_200_OK)
            # if user has saved post private
            if User.objects.filter(id=user_id, is_saved_post_public=0).exists():
                return Response({'message': Messages.USER_HAS_PRIVATE_POSTS}, status=status.HTTP_200_OK)

            # post ids listing
            post_ids = list(UserSavePost.objects.filter(user_id=user_id).values_list('post_id', flat=True).distinct())
            post_list = Post.objects.filter(post_id__in=post_ids, is_active=1).all()[page_offset:page_limit+page_offset]
            serializer = PostListSerializer(post_list, many=True)
            post_listing = []
            for post_data in serializer.data:
                is_post_upvote = PostUpvote.objects.filter(post_id=post_data['post_id'], user_id=current_user_id).exists()
                is_post_save = UserSavePost.objects.filter(post_id=post_data['post_id'], user_id=current_user_id).exists()
                post_comments_data = []
                for post_comment in post_data['comments']:
                    is_comment_upvote = PostCommentsUpvote.objects.filter(comment_id=post_comment['comment_id'], user_id=current_user_id).exists()
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
        logerror('other_user_profile/views.py/other_user_saved_posts', str(exception))
        return Response({'error':str(exception)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

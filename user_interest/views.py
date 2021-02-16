import random as r
import hashlib
import base64
import secrets
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status
import redis
import _pickle
from config.messages import Messages
from utility.requestErrorFormate import requestErrorMessagesFormate
from ethos_network.settings import EthosCommonConstants
from users.models import User, UserCauses, UserSubCauses, UserBlockedContacts
from notifications.models import Notification
from .models import UserInterest, UserInterestsRequest
from .serializers import SuggestedUsersSerializer
from .requestSchema import AddRemoveInterestValidator, UserListValidator, ApproveRejectValidator
from utility.authMiddleware import isAuthenticate
from utility.rbacService import RbacService
from utility.fcmController import GetNotification
from utility.loggerService import logerror
import redis
from utility.redisCommon import RedisCommon

# This method is used to get list of suggested users
@api_view(['POST'])
def suggsted_users(request):
    """
    @api {POST} v1/user/interest/suggested-users Get list of suggested users
    @apiName Get list of suggested users
    @apiGroup User Interest
    @apiParam {integer} user_id User Id
    @apiParam {list} email_list ["abc@gmail.com","def@gmail.com","xxx@gmail.com"]
    @apiParam {integer} page_limit Page limit
    @apiParam {integer} page_offset Page offset
    @apiSuccessExample {json} Success-Response:
    HTTP/1.1 200 OK
    {
        "data": [
            {
                "name": "Test 30",
                "id": 33,
                "email": "test30@yopmail.com",
                "profile_pic": "profilepic.png",
                "is_interested": 1,
                "is_request_sent": false
            },
            {
                "name": "Jitendra Singh",
                "id": 32,
                "email": "test25@yopmail.com",
                "profile_pic": "profilepic.png",
                "is_interested": 1,
                "is_request_sent": false
            },
            {
                "name": "Test 24",
                "id": 31,
                "email": "test24@yopmail.com",
                "profile_pic": "profilepic.png",
                "is_interested": 0,
                "is_request_sent": false
            }
        ]
    }
    @apiErrorExample Error-Response:
    HTTP/1.1 200 OK
    {
        "error": "User does not exist"
    }
    """
    try:
        validator = UserListValidator(request.data)
        valid = validator.validate()  # validate the request

        if valid:
            current_user_id = int(request.data['user_id'])
            email_list = request.data['email_list']
            page_limit = int(request.data['page_limit'])
            page_offset = int(request.data['page_offset'])

            # if user does not exists
            if not User.objects.filter(id=current_user_id).exists():
                return Response({'error': Messages.USER_NOT_EXIST}, status=status.HTTP_200_OK)

            user_interest = UserInterest.objects.filter(
                user_id=current_user_id
            ).values_list('interested_user_id', flat=True).distinct()
            response = []

            if len(email_list) > 0:
                user_list = User.objects.filter(
                    email__in=email_list,
                    is_deleted=0,
                    is_active=1
                ).values().exclude(id=current_user_id).order_by('id').reverse()
                serializer = SuggestedUsersSerializer(user_list, many=True)

                if len(serializer.data) > 0:

                    for data in serializer.data:
                        if data['id'] in user_interest:
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

                    return Response({'data': response}, status=status.HTTP_200_OK)
                else:
                    response = get_suggested_users_list(current_user_id, user_interest, page_limit, page_offset)
                    
                    return Response({'data': response}, status=status.HTTP_200_OK)
            else:
                response = get_suggested_users_list(current_user_id, user_interest, page_limit, page_offset)
                
                return Response({'data': response}, status=status.HTTP_200_OK)
        else:
            return Response({'error': requestErrorMessagesFormate(validator.get_message())}, status=status.HTTP_200_OK)
    except Exception as exception:
        logerror('user_interest/views.py/suggsted_users', str(exception))
        return Response({'error': str(exception)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Get users suggested list based on user prefered cause and sub-causes
def get_suggested_users_list(current_user_id, user_interest, page_limit, page_offset):
    try:
        # Get logged in user causes list
        causes_array = []
        causes_data = UserCauses.objects.filter(user_id=current_user_id).values()
        if len(causes_data) > 0:
            for res_causes in causes_data:
                causes_array.append(res_causes['causes_id_id'])

        # Get logged in user sub-causes list
        subcauses_array = []
        subcauses_data = UserSubCauses.objects.filter(user_id=current_user_id).values()
        if len(subcauses_data) > 0:
            for res_subcauses in subcauses_data:
                subcauses_array.append(res_subcauses['sub_causes_id_id'])

        # Get users list who has same causes like current users
        user_list_causes = UserCauses.objects.filter(
            causes_id__in=causes_array
        ).values_list('user_id', flat=True).distinct()

        # Get users list who has same sub-causes like current users
        user_list_subcauses = UserSubCauses.objects.filter(
            sub_causes_id__in=subcauses_array
        ).values_list('user_id', flat=True).distinct()

        # Combine and remove duplicate user_id
        result_list = list(set(user_list_causes) | set(user_list_subcauses))

        result_list.sort(reverse=True)

        response = []
        user_list = User.objects.filter(
            id__in=result_list[page_offset:page_limit+page_offset],
            is_deleted=0,
            is_active=1
        ).values().order_by('id').reverse()
        serializer = SuggestedUsersSerializer(user_list, many=True)

        for data in serializer.data:
            if data['id'] in user_interest:
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

        return response
    except Exception as exception:
        logerror('user_interest/views.py/get_suggested_users_list', str(exception))
        return Response({'error':str(exception)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# This method is used to add/remove as an interest
@api_view(['POST'])
def add_remove(request):
    """
    @api {POST} v1/user/interest/add-remove Add/Remove user from interest
    @apiName Add/Remove user from interest
    @apiGroup User Interest
    @apiParam {integer} user_id User Id
    @apiParam {integer} interested_user_id Interested User Id to add or remove from interest list
    @apiSuccessExample {json} Success-Response:
    HTTP/1.1 200 OK
    {
        "interested_user_id": 31
    }
    """
    try:
        validator = AddRemoveInterestValidator(request.data)
        valid = validator.validate()  # validate the request
        
        if valid:

            current_user_id = int(request.data['user_id'])
            interested_user_id = int(request.data['interested_user_id'])

            redis_object = redis.Redis(EthosCommonConstants.REDIS_HOST)  # Redis object
            user_interests_count = RedisCommon.user_interests_count + str(current_user_id)
            added_as_interested_count = RedisCommon.user_added_as_interested_count + str(interested_user_id)
            user_interests_users = RedisCommon.user_interests_users + str(current_user_id)

            data_message = {
                "body": "Data body is running",
                "title": "Data Title",
                "click_action": "NOTIFICATION_CLICK",
                "reference_id": 4,
                'event_id': 0
            }

            if interested_user_id == current_user_id:
                return Response({'error': Messages.INTEREST_SAME_USER}, status=status.HTTP_200_OK)

            if UserBlockedContacts.objects.filter(user_id=current_user_id, blocked_user_id=interested_user_id).exists():
                return Response({'error': Messages.YOU_BLOCKED_THIS_USER}, status=status.HTTP_200_OK)

            user_info = User.objects.filter(id=current_user_id).values()
            if user_info:

                user_interest = UserInterest.objects.filter(
                    user_id=current_user_id,
                    interested_user_id=interested_user_id
                ).values()

                # If already exist then delete
                if user_interest:
                    UserInterest.objects.filter(
                        user_id=current_user_id,
                        interested_user_id=interested_user_id
                    ).delete()

                    redis_object.lrem(user_interests_users, 0, interested_user_id) # Remove interested users from list
                    redis_object.decr(user_interests_count) # decrease interests_count
                    redis_object.decr(added_as_interested_count)  # decrease added as interests_count
                else:
                    user_obj = User.objects.get(id=current_user_id)
                    interested_user_obj = User.objects.get(id=interested_user_id)
                    device_tokens = GetNotification().getDeviceToken([interested_user_id])

                    # if interested user has private account
                    if User.objects.filter(id=interested_user_id, is_account_private=1).exists():

                        # if user already send a request to interested user but he has not taken any action on it
                        if UserInterestsRequest.objects.filter(user_id=current_user_id,interested_user_id=interested_user_id).exists():
                            return Response({"is_request_sent":True}, status=status.HTTP_200_OK)
                        UserInterestsRequest.objects.create(
                            user_id=user_obj,
                            interested_user_id=interested_user_obj
                        )
                        update_dict = {
                            'body': user_obj.name+Messages.INTEREST_REQUEST_MESSAGE,
                            'title': Messages.INTEREST_REQUEST_TITLE,
                            'event_id': current_user_id
                        }
                        data_message.update(update_dict)
                        GetNotification().addNotification(interested_user_id, Messages.INTEREST_REQUEST_TITLE, user_obj.name+Messages.INTEREST_REQUEST_MESSAGE, 4, current_user_id)

                        if len(device_tokens) > 0:
                            GetNotification().send_push_notification(
                                device_tokens,
                                Messages.INTEREST_REQUEST_TITLE,
                                user_obj.name+Messages.INTEREST_REQUEST_MESSAGE,
                                data_message
                            )

                        return Response({"is_request_sent":True}, status=status.HTTP_200_OK)
                    else:
                        update_dict = {
                            'body': user_obj.name+Messages.INTEREST_ADDED_MESSAGE,
                            'title': Messages.INTEREST_ADDED_TITLE,
                            'reference_id': 2,
                            'event_id': current_user_id
                        }
                        data_message.update(update_dict)
                        UserInterest.objects.create(
                            user_id=current_user_id,
                            interested_user_id=interested_user_id
                        )

                        redis_object.lrem(user_interests_users, 0, interested_user_id)  # to protect duplicacy
                        redis_object.lpush(user_interests_users, interested_user_id)
                        redis_object.incr(user_interests_count)  # increase interests_count
                        redis_object.incr(added_as_interested_count)  # increase added as interests_count

                        GetNotification().addNotification(interested_user_id, Messages.INTEREST_ADDED_TITLE, user_obj.name+Messages.INTEREST_ADDED_MESSAGE, 2, current_user_id)

                        if len(device_tokens) > 0:
                            GetNotification().send_push_notification(
                                device_tokens,
                                Messages.INTEREST_ADDED_TITLE,
                                user_obj.name+Messages.INTEREST_ADDED_MESSAGE,
                                data_message
                            )

                # interests count
                interests_count = UserInterest.objects.filter(interested_user_id=interested_user_id).count()

                return Response({"interests_count":interests_count}, status=status.HTTP_200_OK)
            else:
                return Response({'error': Messages.USER_NOT_EXIST}, status=status.HTTP_200_OK)
        else:
            return Response({'error':requestErrorMessagesFormate(validator.get_message())}, status=status.HTTP_200_OK)
    except Exception as exception:
        logerror('user_interest/views.py/add_remove', str(exception))
        return Response({'error':str(exception)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# This method is used to add/remove as an interest
@api_view(['POST'])
@isAuthenticate
@RbacService('interest:approve:reject')
def approve_reject_request(request):
    """
    @api {POST} v1/user/interest/approve-reject Approve/Reject interest request
    @apiName Approve/Reject interest request
    @apiGroup User Interest
    @apiParam {integer} event_id User Id
    @apiParam {integer} is_approve 0-> in case of reject 1-> in case of approve
    @apiHeader {String} authorization Users unique access-token
    @apiSuccessExample {json} Success-Response:
    HTTP/1.1 200 OK
    {
        "message": "Added as interest request approved"
    }
    """
    try:
        validator = ApproveRejectValidator(request.data)
        valid = validator.validate()  # validate the request
        
        if valid:

            user_id = int(request.data['event_id'])
            is_approve = request.data['is_approve']
            interested_user_id = request.user_id
            message = Messages.REQUEST_REJECTED

            redis_object = redis.Redis(EthosCommonConstants.REDIS_HOST)  # Redis object
            user_interests_count = RedisCommon.user_interests_count + str(user_id)
            added_as_interested_count = RedisCommon.user_added_as_interested_count + str(interested_user_id)
            user_interests_users = RedisCommon.user_interests_users + str(user_id)

            if UserInterestsRequest.objects.filter(user_id=user_id,interested_user_id=interested_user_id).exists():
                if is_approve == 1 and not UserInterest.objects.filter(user_id=user_id, interested_user_id=interested_user_id).exists():
                    UserInterest.objects.create(
                        user_id=user_id,
                        interested_user_id=interested_user_id
                    )
                    message = Messages.REQUEST_APPROVED

                    redis_object.lrem(user_interests_users, 0, interested_user_id)  # to protect duplicity
                    redis_object.lpush(user_interests_users, interested_user_id)
                    redis_object.incr(user_interests_count)  # increase interests_count
                    redis_object.incr(added_as_interested_count)  # increase added as interests_count
                elif is_approve == 1 and UserInterest.objects.filter(user_id=user_id, interested_user_id=interested_user_id).exists():
                    message = Messages.USER_ALREADY_ADDED_AS_INTEREST

                user_obj = User.objects.get(id=user_id)
                interested_user_obj = User.objects.get(id=interested_user_id)

                UserInterestsRequest.objects.filter(
                    user_id=user_obj,
                    interested_user_id=interested_user_obj
                ).delete()

                # If user reject the request then delete from notification list to protect from loop
                Notification.objects.filter(
                    refrence_id=4,
                    user_id=interested_user_id,
                    event_id=user_id
                ).delete()

                return Response({"message":message}, status=status.HTTP_200_OK)
            else:
                return Response({'message': Messages.INVALID_REQUEST}, status=status.HTTP_200_OK)
        else:
            return Response({'error':requestErrorMessagesFormate(validator.get_message())}, status=status.HTTP_200_OK)
    except Exception as exception:
        logerror('user_interest/views.py/approve_reject_request', str(exception))
        return Response({'error':str(exception)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

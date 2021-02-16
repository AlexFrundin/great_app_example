from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status
from config.messages import Messages
from utility.requestErrorFormate import requestErrorMessagesFormate
from utility.authMiddleware import isAuthenticate
from utility.rbacService import RbacService
from .requestSchema import (SendRequestValidator, CreateGroupValidator, AddRemoveGroupValidator,
                            GroupDetailsValidator, EditGroupValidator, ApproverejectValidator,
                            ChatListValidator, UpdateLastMessageValidator, LeaveGroupValidator)
from .models import ChatList, ChatGroupUsers
from .serializers import GroupDetailSerializer, ChatListSerializer
from users.models import User
from utility.loggerService import logerror
from utility.fcmController import GetNotification
from ethos_network.settings import EthosCommonConstants
from django.db.models import Q
from datetime import datetime
import calendar
import time
from notifications.models import Notification

# Create your views here.
@api_view(['POST'])
@isAuthenticate
@RbacService('chat:request')
def send_request(request):
    """
    @api {POST} v1/user/chat/request Send chat request
    @apiName Send Chat request
    @apiGroup Chat
    @apiHeader {String} authorization Users unique access-token
    @apiParam {integer} user_id Which you want to send chat request
    @apiSuccessExample Success-Response:
    HTTP/1.1 201 OK
    {
        "message": "Chat request send"
    }
    HTTP/1.1 201 OK
    {
        "group_id": 21,
        "type": "single",
        "pubnub_id": "pubnub_1598254251",
        "chat_name": "",
        "chat_image": "",
        "created_by": 120,
        "user_id": 102,
        "is_request_accepted": 0,
        "last_message": "Hey there..",
        "last_message_updated_at": 1598265996
    }
    """
    try:
        validator = SendRequestValidator(request.data)
        valid = validator.validate()  # validate the request
        if valid:
            user_id = request.data.get('user_id')
            logged_user_id = request.user_id

            if ChatList.objects.filter(created_by=logged_user_id, user_id=user_id).exists():
                chat_data = ChatList.objects.get(created_by=logged_user_id, user_id=user_id)
                serializer = ChatListSerializer(chat_data, many=False)

                id = serializer.data['user_id'] if logged_user_id == serializer.data['created_by'] else serializer.data['created_by']
                user_obj = User.objects.get(id=id)

                # prepare response
                response = {
                    "group_id": serializer.data["group_id"],
                    "type": serializer.data["type"],
                    "pubnub_id": serializer.data["pubnub_id"],
                    "chat_name": user_obj.name,
                    "chat_image": user_obj.profile_pic,
                    "created_by": serializer.data["created_by"],
                    "user_id": serializer.data["user_id"],
                    "is_request_accepted": serializer.data["is_request_accepted"],
                    "last_message": serializer.data["last_message"],
                    "last_message_updated_at": serializer.data["last_message_updated_at"]
                }

                return Response(response, status=status.HTTP_200_OK)
            elif ChatList.objects.filter(created_by=user_id, user_id=logged_user_id).exists():
                chat_data = ChatList.objects.get(created_by=user_id, user_id=logged_user_id)
                serializer = ChatListSerializer(chat_data, many=False)

                id = serializer.data['user_id'] if logged_user_id == serializer.data['created_by'] else serializer.data['created_by']
                user_obj = User.objects.get(id=id)

                # prepare response
                response = {
                    "group_id": serializer.data["group_id"],
                    "type": serializer.data["type"],
                    "pubnub_id": serializer.data["pubnub_id"],
                    "chat_name": user_obj.name,
                    "chat_image": user_obj.profile_pic,
                    "created_by": serializer.data["created_by"],
                    "user_id": serializer.data["user_id"],
                    "is_request_accepted": serializer.data["is_request_accepted"],
                    "last_message": serializer.data["last_message"],
                    "last_message_updated_at": serializer.data["last_message_updated_at"]
                }

                return Response(response, status=status.HTTP_200_OK)

            user_obj = User.objects.get(id=user_id)
            logged_user_obj = User.objects.get(id=logged_user_id)

            ChatList.objects.create(
                type = 'single',
                pubnub_id=create_pubnub_id(),
                created_by = logged_user_obj,
                user_id = user_obj,
                last_message_updated_at=calendar.timegm(time.gmtime())
            )

            data_message = {
                "reference_id": 5,
                'event_id': int(logged_user_id),
                'title': Messages.CHAT_REQUEST_TITLE,
                'body': logged_user_obj.name + Messages.CHAT_REQUEST_MESSAGE
            }
            device_tokens = GetNotification().getDeviceToken([user_id])
            GetNotification().addNotification(
                user_id,
                Messages.CHAT_REQUEST_TITLE,
                logged_user_obj.name + Messages.CHAT_REQUEST_MESSAGE,
                5,
                logged_user_id
            )

            if len(device_tokens) > 0:
                GetNotification().send_push_notification(
                    device_tokens,
                    Messages.CHAT_REQUEST_TITLE,
                    logged_user_obj.name+Messages.CHAT_REQUEST_MESSAGE,
                    data_message
                )
            return Response({'message': Messages.SEND_CHAT_REQUEST}, status=status.HTTP_200_OK)
        else:
            return Response({'error':requestErrorMessagesFormate(validator.get_message())}, status=status.HTTP_200_OK)
    except Exception as exception:
        logerror('chat/views.py/send_request', str(exception))
        return Response({'error':str(exception)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# approve or reject chat request
@api_view(['POST'])
@isAuthenticate
@RbacService('chat:request:action')
def approve_reject(request):
    """
    @api {POST} v1/user/chat/approve-reject Approve-reject chat request
    @apiName Approve-reject chat request
    @apiGroup Chat
    @apiHeader {String} authorization Users unique access-token
    @apiParam {integer} user_id event id from notification list
    @apiParam {integer} is_approve 1 -> accept 0 -> reject
    @apiSuccessExample Success-Response:
    HTTP/1.1 201 OK
    {
        "message": "Request accepted"
    }
    HTTP/1.1 201 OK
    {
        "message": "Request rejected"
    }
    """
    try:
        validator = ApproverejectValidator(request.data)
        valid = validator.validate()  # validate the request
        if valid:

            is_approve = request.data.get('is_approve')
            user_id = request.data.get('user_id')
            logged_user_id = request.user_id

            if ChatList.objects.filter(user_id=logged_user_id, created_by=user_id, is_request_accepted=1).exists():
                return Response({'error': Messages.CHAT_REQUEST_ALREADY_ACCEPTED}, status=status.HTTP_200_OK)

            if not ChatList.objects.filter(user_id=logged_user_id, created_by=user_id).exists():
                return Response({'error': Messages.NO_CHAT_REQUEST}, status=status.HTTP_200_OK)

            if int(is_approve) == 1:
                ChatList.objects.filter(created_by=user_id, user_id=logged_user_id).update(
                    is_request_accepted = 1,
                    last_message_updated_at=calendar.timegm(time.gmtime())
                )
                msg = Messages.CHAT_REQUEST_ACCEPTED
            else:
                msg = Messages.CHAT_REQUEST_REJECTED
                ChatList.objects.filter(created_by=user_id, user_id=logged_user_id).delete()

            return Response({'message': msg}, status=status.HTTP_200_OK)
        else:
            return Response({'error':requestErrorMessagesFormate(validator.get_message())}, status=status.HTTP_200_OK)
    except Exception as exception:
        logerror('chat/views.py/approve_reject', str(exception))
        return Response({'error':str(exception)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# chat list
@api_view(['GET'])
@isAuthenticate
@RbacService('chat:list')
def chat_list(request):
    """
    @api {POST} v1/user/chat/list Chat List
    @apiName Chat List
    @apiGroup Chat
    @apiHeader {String} authorization Users unique access-token
    @apiHeader {integer} page_limit
    @apiHeader {integer} page_offset
    @apiSuccessExample Success-Response:
    HTTP/1.1 201 OK
    {
        "data": [
            {
                "group_id": 16,
                "type": "single",
                "pubnub_id": null,
                "chat_name": "pawan singh rajput",
                "chat_image": "",
                "created_by": 120,
                "user_id": 103,
                "is_request_accepted": 0,
                "last_message": null,
                "last_message_updated_at": 1598254199
            },
            {
                "group_id": 15,
                "type": "group",
                "pubnub_id": "ABC55512",
                "chat_name": "Ethos Chat Group",
                "chat_image": "image1.jpg",
                "created_by": 120,
                "user_id": null,
                "is_request_accepted": 0,
                "last_message": "Hey there..",
                "last_message_updated_at": 1598254199
            }
        ]
    }
    HTTP/1.1 201 OK
    {
        "data": []
    }
    """
    try:
        validator = ChatListValidator(request.GET)
        valid = validator.validate()  # validate the request
        if valid:
            page_limit = int(request.GET['page_limit'])
            page_offset = int(request.GET['page_offset'])
            logged_user_id = request.user_id

            chat_ids = list(ChatGroupUsers.objects.filter(user_id=logged_user_id).values_list('chat_id', flat=True).distinct())
            chats = ChatList.objects.filter(
                Q(created_by=logged_user_id) |
                Q(user_id=logged_user_id) |
                Q(id__in=chat_ids)
            ).all().order_by('-last_message_updated_at')[page_offset:page_offset+page_limit]
            serializer = ChatListSerializer(chats, many=True)

            for data in serializer.data:
                if data['type'] == 'single':
                    id = data['user_id'] if logged_user_id == data['created_by'] else data['created_by']
                    user_obj = User.objects.get(id=id)
                    data.update({'chat_name': user_obj.name})
                    data.update({'chat_image': user_obj.profile_pic})

            # set is_read = 1
            Notification.objects.filter(user_id=logged_user_id).update(
                is_read=1
            )

            return Response({'data': serializer.data}, status=status.HTTP_200_OK)
        else:
            return Response({'error':requestErrorMessagesFormate(validator.get_message())}, status=status.HTTP_200_OK)
    except Exception as exception:
        logerror('chat/views.py/chat_list', str(exception))
        return Response({'error':str(exception)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Crate chat group
@api_view(['POST'])
@isAuthenticate
@RbacService('user:create:group')
def create_group(request):
    """
    @api {POST} v1/user/chat/group/create Create chat group
    @apiName Create chat group
    @apiGroup Chat
    @apiHeader {String} authorization Users unique access-token.
    @apiParam {string} group_name Group name
    @apiParam {string} group_image Group image
    @apiParam {list} users_id Users id's to add into group, Default => []
    @apiSuccessExample {json} Success-Response:
    HTTP/1.1 200 OK
    {
        "group_id": 12,
        "group_name": "Ethos Group 1",
        "pubnub_id": "ABC444",
        "group_image": "image1.jpg"
    }
    """
    try:
        validator = CreateGroupValidator(request.data)
        valid = validator.validate()  # Validate the request
        if valid:
            current_user_id = request.user_id
            group_name = request.data.get('group_name')
            group_image = request.data.get('group_image')
            users_id = request.data.get('users_id')

            # Create new group
            ChatList.objects.create(
                type="group",
                pubnub_id=create_pubnub_id(),
                chat_name=group_name,
                chat_image=group_image,
                created_by=User.objects.get(id=current_user_id),
                last_message_updated_at=calendar.timegm(time.gmtime())
            )
            inserted_chat_id = ChatList.objects.latest('id').id

            # Add users into groups
            if len(users_id) > 0:
                for insert_user_id in users_id:
                    ChatGroupUsers.objects.create(
                        chat_id=ChatList.objects.get(id=inserted_chat_id),
                        user_id=User.objects.get(id=insert_user_id)
                    )

            # Prepare response
            chat_group = ChatList.objects.get(id=inserted_chat_id)
            serializer = ChatListSerializer(chat_group, many=False)
            response = {
                "group_id": inserted_chat_id,
                'chat_name': group_name,
                'pubnub_id': serializer.data['pubnub_id'],
                'chat_image': group_image
            }

            # Send notification to users
            if len(users_id) > 0:

                # Get user info
                user = User.objects.get(id=current_user_id)

                # Save notification in DB
                for user_id in users_id:
                    GetNotification().addNotification(
                        user_id,
                        Messages.GROUP_CREATED,
                        user.name + Messages.ADDED_IN_GROUP,
                        6,
                        inserted_chat_id
                    )

                # data message for notification
                data_message = {
                    "body": user.name + Messages.ADDED_IN_GROUP,
                    "title": Messages.GROUP_CREATED,
                    "reference_id": 6,
                    "click_action": "NOTIFICATION_CLICK",
                    "event_id": inserted_chat_id
                }

                device_tokens = GetNotification().getDeviceToken(users_id)
                if len(device_tokens) > 0:
                    GetNotification().send_push_notification(
                        device_tokens,
                        Messages.GROUP_CREATED,
                        user.name + Messages.ADDED_IN_GROUP,
                        data_message
                    )

            return Response(response, status=status.HTTP_201_CREATED)
        else:
            return Response({'error':requestErrorMessagesFormate(validator.get_message())}, status=status.HTTP_200_OK)
    except Exception as exception:
        logerror('users/views.py/user_create_chat_group', str(exception))
        return Response({'error':str(exception)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Edit chat group
@api_view(['POST'])
@isAuthenticate
@RbacService('user:edit:group')
def edit_group(request):
    """
    @api {POST} v1/user/chat/group/edit Edit chat group
    @apiName Edit chat group
    @apiGroup Chat
    @apiHeader {String} authorization Users unique access-token.
    @apiParam {integer} group_id Group id
    @apiParam {string} group_name Group name
    @apiParam {string} group_image Group image
    @apiSuccessExample {json} Success-Response:
    HTTP/1.1 200 OK
    {
        "message": "Group details has been updated"
    }
    """
    try:
        validator = EditGroupValidator(request.data)
        valid = validator.validate()  # Validate the request
        if valid:
            current_user_id = request.user_id
            group_id = int(request.data.get('group_id'))
            group_name = request.data.get('group_name')
            group_image = request.data.get('group_image')

            if not ChatList.objects.filter(id=group_id, created_by=current_user_id).exists():
                return Response({'error': Messages.INVALID_REQUEST}, status=status.HTTP_200_OK)

            # Edit group details
            ChatList.objects.filter(id=group_id).update(
                chat_name=group_name,
                chat_image=group_image,
                updated_at=datetime.now()
            )

            # Prepare response
            # chat_group = ChatList.objects.get(id=group_id)
            # serializer = ChatListSerializer(chat_group, many=False)

            return Response({'message':Messages.GROUP_DETAILS_UPDATED}, status=status.HTTP_200_OK)
        else:
            return Response({'error':requestErrorMessagesFormate(validator.get_message())}, status=status.HTTP_200_OK)
    except Exception as exception:
        logerror('users/views.py/user_create_chat_group', str(exception))
        return Response({'error':str(exception)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Add/Remove member from group
@api_view(['POST'])
@isAuthenticate
@RbacService('user:edit:group')
def add_remove_member(request):
    """
    @api {POST} v1/user/chat/group/member/add-remove Add/Remove member from group
    @apiName Add/Remove member from group
    @apiGroup Chat
    @apiHeader {String} authorization User unique access-token.
    @apiParam {integer} group_id Group id
    @apiParam {list} users_id Users id's to add/remove from group
    @apiParam {integer} type Type 1 => Add, 2 => Remove
    @apiSuccessExample {json} Success-Response:
    HTTP/1.1 200 OK
    {
        "message": "New user has been added into group"
    }
    """
    try:
        validator = AddRemoveGroupValidator(request.data)
        valid = validator.validate()  # Validate the request
        if valid:
            current_user_id = request.user_id
            group_id = int(request.data.get('group_id'))
            action_type = int(request.data.get('type'))
            users_id = request.data.get('users_id')

            if not ChatList.objects.filter(id=group_id, created_by=current_user_id).exists():
                return Response({'error': Messages.INVALID_REQUEST}, status=status.HTTP_200_OK)

            # Add members to group
            if action_type == 1:
                message = Messages.NEW_MEMBER_ADD
                if len(users_id) > 0:
                    for add_user_id in users_id:
                        chat = ChatList.objects.get(id=group_id)
                        if not ChatGroupUsers.objects.filter(chat_id=group_id, user_id=add_user_id).exists():
                            user = User.objects.get(id=add_user_id)
                            ChatGroupUsers.objects.create(
                                chat_id=chat,
                                user_id=user
                            )

            # Remove members to group
            if action_type == 2:
                message = Messages.MEMBER_REMOVED
                if len(users_id) > 0:
                    for remove_user_id in users_id:
                        ChatGroupUsers.objects.filter(chat_id=group_id, user_id=remove_user_id).delete()

            return Response({'message': message}, status=status.HTTP_200_OK)
        else:
            return Response({'error': requestErrorMessagesFormate(validator.get_message())}, status=status.HTTP_200_OK)
    except Exception as exception:
        logerror('users/views.py/user_chat_group_add_remove', str(exception))
        return Response({'error': str(exception)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Get group details
@api_view(['GET'])
@isAuthenticate
@RbacService('user:detail:group')
def group_details(request):
    """
    @api {GET} v1/user/chat/group/detail Get group details
    @apiName Get group details
    @apiGroup Chat
    @apiHeader {String} authorization User unique access-token.
    @apiParam {integer} group_id Group id
    @apiSuccessExample {json} Success-Response:
    HTTP/1.1 200 OK
    {
        "group_id": 12,
        "pubnub_id": "ABC444",
        "group_name": "Ethos Group 1",
        "group_image": "image1.jpg",
        "user_detail": {
            "name": "Nikhil 1",
            "id": 120,
            "email": "nikhil12@techaheadcorp.com",
            "profile_pic": "profilepic.png",
            "bio": "Dummy Text",
            "modified_at": "2020-07-28"
        },
        "group_users": [
            {
                "chat_id": 12,
                "user_detail": {
                    "name": "Test 03",
                    "id": 2,
                    "email": "test03@yopmail.com",
                    "profile_pic": "jsdg",
                    "bio": "fgsdf",
                    "modified_at": "2020-07-20"
                }
            },
            {
                "chat_id": 12,
                "user_detail": {
                    "name": "Test 06",
                    "id": 3,
                    "email": "test06@yopmail.com",
                    "profile_pic": "profilepic.png",
                    "bio": null,
                    "modified_at": "2020-07-09"
                }
            },
            {
                "chat_id": 12,
                "user_detail": {
                    "name": "Test 04",
                    "id": 4,
                    "email": "test04@yopmail.com",
                    "profile_pic": "profilepic.png",
                    "bio": null,
                    "modified_at": "2020-07-09"
                }
            }
        ]
    }
    """
    try:
        validator = GroupDetailsValidator(request.GET)
        valid = validator.validate()  # Validate the request
        if valid:
            group_id = int(request.GET['group_id'])

            if not ChatList.objects.filter(id=group_id).exists():
                return Response({'error': Messages.GROUP_DOES_NOT_EXIST}, status=status.HTTP_404_NOT_FOUND)

            # Get group details
            group_detail = ChatList.objects.get(id=group_id)
            serializer = GroupDetailSerializer(group_detail, many=False)
            serializer.data['group_users'].append({
                'chat_id': serializer.data['group_id'],
                'user_detail': serializer.data['user_detail']
            })
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response({'error': requestErrorMessagesFormate(validator.get_message())}, status=status.HTTP_200_OK)
    except Exception as exception:
        logerror('users/views.py/user_chat_group_details', str(exception))
        return Response({'error': str(exception)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Update last message
@api_view(['POST'])
@isAuthenticate
@RbacService('user:edit:group')
def update_last_message(request):
    """
    @api {POST} v1/user/chat/group/update/message Update last message
    @apiName Update last message
    @apiGroup Chat
    @apiHeader {String} authorization User unique access-token.
    @apiParam {string} pubnub_id Pubnub id
    @apiParam {string} message Message
    @apiSuccessExample {json} Success-Response:
    HTTP/1.1 200 OK
    {
        "message": "Group last message has been updated"
    }
    """
    try:
        validator = UpdateLastMessageValidator(request.data)
        valid = validator.validate()  # Validate the request
        if valid:
            pubnub_id = request.data.get('pubnub_id')
            message = request.data.get('message')

            if not ChatList.objects.filter(pubnub_id=pubnub_id).exists():
                return Response({'error': Messages.GROUP_DOES_NOT_EXIST}, status=status.HTTP_404_NOT_FOUND)

            ChatList.objects.filter(pubnub_id=pubnub_id).update(
                last_message=message,
                last_message_updated_at=calendar.timegm(time.gmtime())
            )
            return Response({'message': Messages.LAST_MESSAGE_UPDATED}, status=status.HTTP_200_OK)
        else:
            return Response({'error': requestErrorMessagesFormate(validator.get_message())}, status=status.HTTP_200_OK)
    except Exception as exception:
        logerror('users/views.py/user_chat_group_update_last_message', str(exception))
        return Response({'error': str(exception)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Leave group
@api_view(['POST'])
@isAuthenticate
@RbacService('user:edit:group')
def leave_group(request):
    """
    @api {POST} v1/user/chat/group/leave Leave group
    @apiName Leave group
    @apiGroup Chat
    @apiHeader {String} authorization User unique access-token.
    @apiParam {integer} group_id Group id
    @apiSuccessExample {json} Success-Response:
    HTTP/1.1 200 OK
    {
        "message": "Group left successfully"
    }
    @apiErrorExample Error-Response:
    HTTP/1.1 200 OK
    {
        "error": "Group does not exist"
    }
    """
    try:
        validator = LeaveGroupValidator(request.data)
        valid = validator.validate()  # Validate the request
        if valid:
            group_id = int(request.data.get('group_id'))
            current_user_id = request.user_id

            # If admin is leaving group then we will assign next member as an admin
            if not ChatList.objects.filter(id=group_id).exists():
                return Response({'error': Messages.GROUP_DOES_NOT_EXIST}, status=status.HTTP_404_NOT_FOUND)

            # If admin is leaving group then we will assign next member as an admin
            if ChatList.objects.filter(id=group_id, created_by=current_user_id).exists():

                # Get members in a group
                group_users = ChatGroupUsers.objects.filter(
                    chat_id=group_id
                ).values_list('user_id', flat=True).order_by('created_at')[:1]

                # if there are more than one member in the group the assign new user as group admin
                if len(group_users) > 0:
                    new_admin_id = group_users[0]
                    user = User.objects.get(id=new_admin_id)
                    ChatList.objects.filter(id=group_id, created_by=current_user_id).update(
                        created_by=user
                    )
                    ChatGroupUsers.objects.filter(chat_id=group_id, user_id=new_admin_id).delete()
                else:
                    # if there is only admin then we need to also delete group
                    ChatList.objects.filter(id=group_id, created_by=current_user_id).delete()
            else:
                ChatGroupUsers.objects.filter(chat_id=group_id, user_id=current_user_id).delete()

            return Response({'message': Messages.GROUP_LEFT}, status=status.HTTP_200_OK)
        else:
            return Response({'error': requestErrorMessagesFormate(validator.get_message())}, status=status.HTTP_200_OK)
    except Exception as exception:
        logerror('users/views.py/user_chat_group_update_last_message', str(exception))
        return Response({'error': str(exception)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Create pub_nub Id
def create_pubnub_id():
    prefix = "pubnub_"
    timestamp = calendar.timegm(time.gmtime())
    return prefix + str(timestamp)
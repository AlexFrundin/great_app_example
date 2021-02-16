from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status
from config.messages import Messages
from utility.requestErrorFormate import requestErrorMessagesFormate
from utility.authMiddleware import isAuthenticate
from utility.rbacService import RbacService
from .requestSchema import NotificationListValidator
from .models import Notification
from .serializers import NoitifcationListSerializer
from utility.loggerService import logerror

# Create your views here.
# notification list
@api_view(['GET'])
@isAuthenticate
@RbacService('notification:read')
def notification_list(request):
    """
    @api {GET} v1/user/notification/list Notifications list
    @apiName Notifications list
    @apiGroup Notification
    @apiHeader {String} authorization Users unique access-token
    @apiHeader {integer} page_limit
    @apiHeader {integer} page_offset
    @apiSuccessExample {json} Success-Response:
    HTTP/1.1 200 OK
    {
        "data": [
            {
                "id": 1,
                "refrence_id": 1,
                "event_id": 1,
                "title": "hi",
                "message": "hey you",
                "is_read": 0,
                "is_deleted": 0,
                "created_on": "21 Aug 2020"
            }
        ]
    }
    """
    try:
        validator = NotificationListValidator(request.GET)
        valid = validator.validate()  # Validate the request
        if valid:
            current_user_id = request.user_id
            page_limit = int(request.GET['page_limit'])
            page_offset = int(request.GET['page_offset'])

            # notification listing
            notification_list = Notification.objects.filter(user_id=current_user_id).all().order_by('-created_on')[page_offset:page_limit+page_offset]
            serializer = NoitifcationListSerializer(notification_list, many=True)

            # set is_read = 1
            Notification.objects.filter(user_id=current_user_id).update(
                is_read=1
            )
            
            return Response({'data':serializer.data}, status=status.HTTP_200_OK)
        else:
            return Response({'error':requestErrorMessagesFormate(validator.get_message())}, status=status.HTTP_200_OK)
    except Exception as exception:
        logerror('notifications/views.py/notification_list', str(exception))
        return Response({'error':str(exception)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Clear notifications
@api_view(['POST'])
@isAuthenticate
@RbacService('notification:read')
def clear_notifiactions(request):
    """
    @api {POST} v1/user/notification/clear Clear Notifications
    @apiName Clear Notifications
    @apiGroup Notification
    @apiHeader {String} authorization Users unique access-token
    @apiHeader {integer} is_clear_all 1 for clear all notifications otherwise 0
    @apiHeader {list} notification_ids blank in case of `is_clear_all` 1
    @apiSuccessExample {json} Success-Response:
    HTTP/1.1 200 OK
    {
        "message": "Notifications removed successfully"
    }
    """
    try:
        current_user_id = request.user_id
        is_clear_all = request.data.get('is_clear_all')
        notification_ids = list(request.data.get('notification_ids'))
        # if is clear all 1 then clear all notifications
        if is_clear_all == 1:
            Notification.objects.filter(user_id=current_user_id).delete()
            return Response({'message':Messages.NOTIFICATION_REMOVED}, status=status.HTTP_200_OK)

        Notification.objects.filter(id__in=notification_ids, user_id=current_user_id).delete()
        return Response({'message':Messages.NOTIFICATION_REMOVED}, status=status.HTTP_200_OK)
    except Exception as exception:
        logerror('notifications/views.py/clear_notifiactions', str(exception))
        return Response({'error':str(exception)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Get notifications count
@api_view(['GET'])
@isAuthenticate
@RbacService('notification:read')
def get_notification_count(request):
    """
    @api {GET} v1/user/notification/count Get notification count
    @apiName Get notification count
    @apiGroup Notification
    @apiHeader {String} Content-Type application/json
    @apiSuccessExample {json} Success-Response:
    HTTP/1.1 200 OK
    {
        "notification_count": 2
    }
    """
    try:
        current_user_id = request.user_id
        notification_count = Notification.objects.filter(user_id=current_user_id, is_read=0).count()

        response = {
            "notification_count": notification_count
        }

        return Response(response, status=status.HTTP_200_OK)
    except Exception as exception:
        logerror('user_profile/views.py/user_delete_profile', str(exception))
        return Response({'error': str(exception)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

from rest_framework import status
from rest_framework.response import Response
from users.models import User
from notifications.models import Notification
from pyfcm import FCMNotification
from ethos_network.settings import FcmNotificationConstants

pushService = FCMNotification(api_key=FcmNotificationConstants.api_key)

class GetNotification():

    deviceToken = ''

    # get device token
    def getDeviceToken(self, userIds):
        try:
            device_tokens = User.objects.filter(id__in=userIds, is_login=1, is_deleted=0, is_active=1, is_notification_active=1).values('device_token', 'device_type')
            device_tokens_list = []
            for device_token in device_tokens:
                device_tokens_list.append({
                    'device_token': device_token['device_token'],
                    'device_type': device_token['device_type']
                })
            return device_tokens_list
        except BaseException as exception:
            return Response({'error':str(exception)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # add notification
    def addNotification(self, user_id, message_title, message_body, reference_id, event_id):
        try:
            user_obj = User.objects.get(id=user_id)
            Notification.objects.create(
                refrence_id = reference_id,
                event_id = event_id,
                user_id = user_obj,
                title = message_title,
                message = message_body
            )
        except BaseException as exception:
            return Response({'error':str(exception)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def send_push_notification(self, device_tokens, message_title, message_body, data_message):
        try:
            for data in device_tokens:
                if data['device_type'] == 1:

                    # device_type 1 for android
                    pushService.single_device_data_message(
                        registration_id=data['device_token'],
                        data_message=data_message
                    )
                elif data['device_type'] == 2:

                    # device_type 2 for IOS
                    pushService.notify_single_device(
                        registration_id=data['device_token'],
                        message_title=message_title,
                        message_body=message_body,
                        data_message=data_message,
                        sound="default"
                    )

        except BaseException as exception:
            return Response({'error':str(exception)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
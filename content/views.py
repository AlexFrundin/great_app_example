from django.http import HttpResponse
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from utility.loggerService import logerror
from utility.authMiddleware import isAuthenticate
from post.views import causes_engagement_count, sub_causes_engagement_count
from users.models import User, UserCauses, UserSubCauses
from causes_subcauses.models import Cause, SubCause
from utility.mailTemplates.emailTemplates import emailTemplates
from ethos_network.settings import EthosCommonConstants
from user_interest.serializers import SuggestedUsersSerializer
from causes_subcauses.serializers import CauseSerializer, SubCausesSerializer
from .models import StaticContent, Newsletter
from .serializers import StaticContentSerializer
from .requestSchema import SearchListValidator
import redis
import _pickle
from utility.redisCommon import RedisCommon

# This method default view in thee main screen
@api_view(['GET'])
def index(request):
    return HttpResponse('<center><h1>Welcome to ETHOS Network API server :)</h1></center>')

# This method is use to get the content list
@api_view(['GET'])
def static_content(request):
    """
    @api {GET} v1/user/content/list Content list
    @apiName Content list
    @apiGroup User
    @apiHeader {String} Content-Type application/json
    @apiSuccessExample {json} Success-Response:
    HTTP/1.1 200 OK
    {
        "about_us": "The standard Lorem Ipsum passage, used since the 1500s\r\n\"Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.",
        "privacy_policy": "Why do we use it?\r\nIt is a long established fact that a reader will be distracted by the readable content of a page when looking at its layout. The point of using Lorem Ipsum is that it has a more-or-less normal distribution of letters, as opposed to using 'Content here, content here', making it look like readable English. ",
        "terms_and_conditions": "What is Lorem Ipsum?\r\nLorem Ipsum is simply dummy text of the printing and typesetting industry. Lorem Ipsum has been the industry's standard dummy text ever since the 1500s, when an unknown printer took a galley of type and scrambled it to make a type specimen book. "
    }
    """
    try:

        redis_object = redis.Redis(EthosCommonConstants.REDIS_HOST)  # Redis object
        redis_key = RedisCommon.static_content  # Key in which we will store data

        # Check if already exist in Redis then don't need to call SQL
        if redis_object.get(redis_key):
            static_content = _pickle.loads(redis_object.get(redis_key))
            return Response(static_content, status=status.HTTP_200_OK)

        static_content = StaticContent.objects.all()
        serializer = StaticContentSerializer(static_content, many=True)

        # Set data in Redis
        RedisCommon().set_data(redis_key, serializer.data[0])

        return Response(serializer.data[0], status=status.HTTP_200_OK)
    except Exception as exception:
        logerror('content/views.py/static_content', str(exception))
        return Response({'error':str(exception)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def save_newsletter(request):
    """
    @api {POST} v1/user/content/save-newsletter Save- Newsletter
    @apiName Save- Newsletter
    @apiGroup Content
    @apiHeader {String} Content-Type application/json
    @apiParam {string} content Content
    @apiSuccessExample {json} Success-Response:
    HTTP/1.1 200 OK
    {
        "newsletter_id": 6
    }
    """
    try:
        content = request.data['content']

        if not Newsletter.objects.filter(content=content).exists(): 

            newsletter = Newsletter.objects.create(
                content=content,
            )
            newsletter.save()

            # Send email
            subject = "Newsletter Subscription"
            title = "Newsletter Subscription"
            message = '<p><strong>Hello Admin,</strong><p></br>'
            message += '<p>A user has below email subscribed the Ethos Newsletter<p>'
            message += '<p><strong>Email ID:' + content + '</strong><p>'

            emailFrom = EthosCommonConstants.EMAIL_HOST_USER
            emailTo = EthosCommonConstants.ADMIN_EMAIL_ID
            emailTemplates.sendLinkMail(subject, emailFrom, emailTo, message, title)

            # get inserted user id
            news_obj = Newsletter.objects.latest('id')
            latest_id = news_obj.id

            return Response({'newsletter_id': latest_id}, status=status.HTTP_201_CREATED)

        return Response({'error': 'You have already subscribed'}, status=status.HTTP_200_OK)
    except Exception as exception:
        logerror('content/views.py/save_newsletter', str(exception))
        return Response({'error':str(exception)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@isAuthenticate
def search_content(request):
    """
    @api {GET} v1/user/content/search Search user, cause & sub-cause
    @apiName Search user, cause & sub-cause
    @apiGroup Content
    @apiHeader {String} authorization User unique access-token.
    @apiParam {string} search_text Search text
    @apiSuccessExample {json} Success-Response:
    HTTP/1.1 200 OK
    {
        "data": [
            {
                "type": "user",
                "id": 107,
                "title": "Nikhil Env",
                "image": "profilepic.png"
            },
            {
                "type": "cause",
                "id": 1,
                "title": "Environment",
                "image": "environment.png",
                "engagement_count": 55
            },
            {
                "type": "subcause",
                "id": 11,
                "title": "sub7 Env",
                "image": "ethos/1596119367538.png",
                "engagement_count": 0,
                "cause_name": "Cause 7"
            }
        ]
    }
    """
    try:
        validator = SearchListValidator(request.GET)
        valid = validator.validate()  # Validate the request
        if valid:
            current_user_id = request.user_id
            search_text = request.GET['search_text']
            final_search_results = []

            # Search user
            users_list = User.objects.filter(name__icontains=search_text, is_deleted=0, is_active=1).all()
            user_serializer = SuggestedUsersSerializer(users_list, many=True)
            for user_details in user_serializer.data:
                final_search_results.append({
                    "type": "user",
                    "id": user_details['id'],
                    "title": user_details['name'],
                    "image": user_details['profile_pic']
                })

            # Search cause
            cause_list = Cause.objects.filter(name__icontains=search_text, is_deleted=0, is_active=1).all()
            cause_serializer = CauseSerializer(cause_list, many=True)

            # Get user causes ids
            user_causes_ids = UserCauses.objects.filter(
                user_id=current_user_id
            ).values_list('causes_id', flat=True).distinct()

            for cause_details in cause_serializer.data:

                # Check if user has already cause in profile
                is_cause_selected = 0
                if cause_details['cause_id'] in user_causes_ids:
                    is_cause_selected = 1

                final_search_results.append({
                    "type": "cause",
                    "id": cause_details['cause_id'],
                    "title": cause_details['cause_name'],
                    "image": cause_details['cause_image'],
                    "is_cause_selected": is_cause_selected,
                    "engagement_count": causes_engagement_count(cause_details['cause_id'])
                })

            # Search sub_cause
            sub_cause_list = SubCause.objects.filter(name__icontains=search_text, is_deleted=0, is_active=1).all()
            sub_cause_serializer = SubCausesSerializer(sub_cause_list, many=True)

            # Get user sub-causes ids
            user_subcauses_ids = UserSubCauses.objects.filter(
                user_id=current_user_id
            ).values_list('sub_causes_id', flat=True).distinct()

            for sub_cause_details in sub_cause_serializer.data:

                cause_details = Cause.objects.get(id=sub_cause_details['cause_id'])
                cause_serializer = CauseSerializer(cause_details, many=False)

                # Check if user has already sub-cause in profile
                is_cause_selected = 0
                if sub_cause_details['sub_cause_id'] in user_subcauses_ids:
                    is_cause_selected = 1

                final_search_results.append({
                    "type": "subcause",
                    "id": sub_cause_details['sub_cause_id'],
                    "title": sub_cause_details['sub_cause_name'],
                    "image": sub_cause_details['sub_cause_image'],
                    "is_cause_selected": is_cause_selected,
                    "engagement_count": sub_causes_engagement_count(sub_cause_details['sub_cause_id']),
                    "cause_name": cause_serializer.data['cause_name']
                })

            return Response({'data': final_search_results}, status=status.HTTP_200_OK)
        else:
            return Response({'error': requestErrorMessagesFormate(validator.get_message())}, status=status.HTTP_200_OK)
    except Exception as exception:
        logerror('content/views.py/content_search', str(exception))
        return Response({'error': str(exception)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

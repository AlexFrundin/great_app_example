from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status
import redis
import _pickle
from django.views.decorators.csrf import csrf_exempt
from utility.requestErrorFormate import requestErrorMessagesFormate
from ethos_network.settings import EthosCommonConstants
from .models import Cause, SubCause
from .requestSchema import ListValidator
from config.messages import Messages
from .serializers import CauseSerializer, SubCausesSerializer
from post.views import causes_engagement_count, sub_causes_engagement_count
from collections import OrderedDict
from utility.loggerService import logerror

@api_view(['GET'])
def causes_list(request):
    """
    @api {GET} v1/user/causes/list Cause subcauses list
    @apiName Cause subcauses list
    @apiGroup User
    @apiHeader {String} Content-Type application/json
    @apiParam {integer} page_limit Page limit
    @apiParam {string} page_offset Page offset
    @apiSuccessExample {json} Success-Response:
    HTTP/1.1 200 OK
    {
        "data": [
            {
                "cause_id": 1,
                "cause_name": "Environment",
                "cause_image": null,
                "cause_color": "#fafafa",
                "cause_color_gradient": "#fafafa",
                "engagement_count": 8,
                "sub_causes": [
                    {
                        "cause_id": 1,
                        "sub_cause_id": 1,
                        "cause_name": "Environment",
                        "sub_cause_name": "Forest",
                        "sub_cause_image": null,
                        "sub_cause_color": "#fafafa",
                        "sub_cause_color_gradient": "#fafafa",
                        "engagement_count": 8
                    },
                    {
                        "cause_id": 1,
                        "sub_cause_id": 2,
                        "cause_name": "Environment",
                        "sub_cause_name": "Activist",
                        "sub_cause_image": null,
                        "sub_cause_color": "#fafafa",
                        "sub_cause_color_gradient": "#fafafa",
                        "engagement_count": 8
                    }
                ]
            },
            {
                "cause_id": 2,
                "cause_name": "Child Welfare",
                "cause_image": null,
                "cause_color": "#fafafa",
                "cause_color_gradient": "#fafafa",
                "engagement_count": 7,
                "sub_causes": [
                    {
                        "cause_id": 2,
                        "sub_cause_id": 5,
                        "cause_name": "Child Welfare",
                        "sub_cause_name": "Child Subcauses 1",
                        "sub_cause_image": null,
                        "sub_cause_color": "#fafafa",
                        "sub_cause_color_gradient": "#fafafa",
                        "engagement_count": 0
                    },
                    {
                        "cause_id": 2,
                        "sub_cause_id": 6,
                        "cause_name": "Child Welfare",
                        "sub_cause_name": "Child Subcauses 2",
                        "sub_cause_image": null,
                        "sub_cause_color": "#fafafa",
                        "sub_cause_color_gradient": "#fafafa",
                        "engagement_count": 0
                    }
                ]
            },
            {
                "cause_id": 3,
                "cause_name": "Women",
                "cause_image": null,
                "cause_color": "#fafafa",
                "cause_color_gradient": "#fafafa",
                "engagement_count": 7,
                "sub_causes": [
                    {
                        "cause_id": 3,
                        "sub_cause_id": 3,
                        "cause_name": "Women",
                        "sub_cause_name": "Women Subcauses 1",
                        "sub_cause_image": null,
                        "sub_cause_color": "#fafafa",
                        "sub_cause_color_gradient": "#fafafa",
                        "engagement_count": 8
                    },
                    {
                        "cause_id": 3,
                        "sub_cause_id": 4,
                        "cause_name": "Women",
                        "sub_cause_name": "Women Subcauses 2",
                        "sub_cause_image": null,
                        "sub_cause_color": "#fafafa",
                        "sub_cause_color_gradient": "#fafafa",
                        "engagement_count": 0
                    }
                ]
            }
        ]
    }
    """
    try:
        validator = ListValidator(request.GET)
        valid = validator.validate()  # Validate the request
        if valid:
            # Redis object
            redis_object = redis.Redis(EthosCommonConstants.REDIS_HOST)
            # Key in which we will store data
            redis_key = 'causes_subcauses_list'

            # Check if already exist in Redis then don't need to call SQL
            # if redis_object.get(redis_key):
            #     response = _pickle.loads(redis_object.get(redis_key))
            #     return Response({'data':response}, status=status.HTTP_200_OK)

            if Cause.objects.filter(is_deleted=0, is_active=1).exists():

                causes = Cause.objects.filter(is_deleted=0, is_active=1).all()  # fetch the from database
                serializer = CauseSerializer(causes, many=True)  # serialize the data
                new_data = []
                for data in serializer.data:
                    ordered_data = dict(OrderedDict(data))
                    subcauses = []
                    for subcause in ordered_data['sub_causes']:
                        ordered_subcause = dict(OrderedDict(subcause))
                        if ordered_subcause['is_active'] == 1 and ordered_subcause['is_deleted'] == 0:
                            subcauses.append({
                                "cause_id": ordered_data['cause_id'],
                                "sub_cause_id": ordered_subcause['sub_cause_id'],
                                "cause_name": ordered_data['cause_name'],
                                "sub_cause_name": ordered_subcause['sub_cause_name'],
                                "sub_cause_image": ordered_subcause['sub_cause_image'],
                                "sub_cause_color": ordered_subcause['sub_cause_color'],
                                "sub_cause_color_gradient": ordered_subcause['sub_cause_color_gradient'],
                                "engagement_count": sub_causes_engagement_count(ordered_subcause['sub_cause_id'])
                            })
                    new_data.append(
                        {
                            "cause_id": ordered_data['cause_id'],
                            "cause_name": ordered_data['cause_name'],
                            "cause_image": ordered_data['cause_image'],
                            "cause_color": ordered_data['cause_color'],
                            "cause_color_gradient": ordered_data['cause_color_gradient'],
                            "engagement_count": causes_engagement_count(ordered_data['cause_id']),
                            "sub_causes": subcauses
                        }
                    )
                # Set data in Redis for 15 min
                redis_object.set(redis_key, _pickle.dumps(new_data))
                redis_object.expire(redis_key, EthosCommonConstants.REDIS_EXPIRATION)

                return Response({'data':new_data}, status=status.HTTP_200_OK)
            else:
                return Response({'data':[]}, status=status.HTTP_200_OK)
        else:
            return Response({'error':requestErrorMessagesFormate(validator.get_message())}, status=status.HTTP_200_OK)
    except Exception as exception:
        logerror('causes_subcauses/views.py/causes_list', str(exception))
        return Response({'error':str(exception)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
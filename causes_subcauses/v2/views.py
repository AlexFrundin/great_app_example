from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from causes_subcauses.models import Cause, SubCause
from causes_subcauses.v2.serializers import UserCauseSubcauseSerializer
from causes_subcauses.v2.validators import CausesValidator, SubCausesValidator
from users.models import User, UserCauses, UserSubCauses
from utility.authMiddleware import isAuthenticate
from utility.loggerService import logerror
from utility.requestErrorFormate import requestErrorMessagesFormate


@api_view(['POST'])
@isAuthenticate
def add_causes(request):
    """
    @api {POST} v2/user/causes/ Cause list
    @apiName Cause list
    @apiGroup User
    @apiHeader {String} Content-Type application/json
    @apiParam {integer} causes List of causes ids
    @apiSuccessExample Success-Response:
    HTTP/1.1 201 Created
    { }
    @apiErrorExample Error-Response:
    HTTP/1.1 200 OK
    {
        "error": "causes field required"
    }
    """
    try:
        validator = CausesValidator(request.data)
        # Get user info
        user = User.objects.get(id=request.user_id)
        if validator.validate():
            # insert causes
            user_causes = request.data.get('causes')
            if len(user_causes) > 0:
                for cause_id in user_causes:
                    cause = Cause.objects.get(id=cause_id)
                    if not UserCauses.objects.filter(user_id=user.id, causes_id=cause).exists():
                        UserCauses.objects.create(
                            user_id=user,
                            causes_id=cause,
                        )

            return Response({'data': user_causes}, status=status.HTTP_201_CREATED)
        else:
            return Response({'error': requestErrorMessagesFormate(validator.get_message())}, status=status.HTTP_200_OK)
    except Exception as exception:
        logerror('causes_subcauses/v2/views.py/add_causes', str(exception))
        return Response({'error': str(exception)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@isAuthenticate
def add_subcauses(request):
    """
    @api {POST} v2/user/causes/subcauses Subcause list
    @apiName Subcause list
    @apiGroup User
    @apiHeader {String} Content-Type application/json
    @apiParam {integer} subcauses List of subcauses ids
    @apiSuccessExample Success-Response:
    HTTP/1.1 201 Created
    { }
    @apiErrorExample Error-Response:
    HTTP/1.1 200 OK
    {
        "error": "subcauses field required"
    }
    """
    try:
        validator = SubCausesValidator(request.data)
        # Get user info
        user = User.objects.get(id=request.user_id)
        if validator.validate():
            # insert sub-causes
            user_sub_causes = request.data.get('subcauses')
            if len(user_sub_causes) > 0:
                for sub_cause_id in user_sub_causes:
                    sub_cause = SubCause.objects.get(id=sub_cause_id)
                    if not UserSubCauses.objects.filter(user_id=user.id, sub_causes_id=sub_cause).exists():
                        UserSubCauses.objects.create(
                            user_id=user,
                            sub_causes_id=sub_cause
                        )

            return Response({'data': user_sub_causes}, status=status.HTTP_201_CREATED)
        else:
            return Response({'error': requestErrorMessagesFormate(validator.get_message())}, status=status.HTTP_200_OK)
    except Exception as exception:
        logerror('causes_subcauses/v2/views.py/add_subcauses', str(exception))
        return Response({'error': str(exception)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@isAuthenticate
def user_cause_subcause_list(request):
    """
    @api {GET} v2/user/causes/subcauses Causes and Subcauses list
    @apiName Causes and Subcauses list
    @apiGroup User
    @apiHeader {String} Content-Type application/json
    @apiParam {integer} subcauses List of causes and subcauses ids
    @apiSuccessExample Success-Response:
    HTTP/1.1 200 Success
    {
        "user_causes": [
            {
                "id": 1,
                "name": "Health",
                "image": "1600439639671.png"
            }
        ],
        "user_sub_causes": [
            {
                "id": 1,
                "name": "Addiction",
                "image": "1600439639671.png",
                "cause_id": 1
            },
            {
                "id": 239,
                "name": "Equal Pay",
                "image": "1600870348477.png",
                "cause_id": 4
            }
        ]
    }
    @apiErrorExample Error-Response:
    HTTP/1.1 200 OK
    {
        "error": "user not found"
    }
    """
    try:
        user_id = request.user_id
        user_info = User.objects.filter(id=user_id)
        if user_info:
            serializer = UserCauseSubcauseSerializer(user_info, many=True)
            return Response(serializer.data[0], status=status.HTTP_200_OK)
        else:
            return Response({'error': 'User not found.'}, status=status.HTTP_200_OK)
    except Exception as exception:
        logerror('causes_subcauses/v2/views.py/user_cause_subcause_list', str(exception))
        return Response({'error': str(exception)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

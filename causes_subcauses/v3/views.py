from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db.models import Prefetch, Count

from causes_subcauses.models import Cause, SubCause
from causes_subcauses.v3.serializers import UserCauseSubcauseSerializer, CauseSerializer
from causes_subcauses.v2.validators import CausesValidator, SubCausesValidator, ListValidator
from users.models import User, UserCauses, UserSubCauses
from utility.authMiddleware import isAuthenticate
from utility.loggerService import logerror
from utility.requestErrorFormate import requestErrorMessagesFormate


@api_view(['POST'])
@isAuthenticate
def add_causes(request):
    """
    @api {POST} v3/user/causes/ Cause list
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

        if validator.validate():
            new_causes = request.data.get('causes')
            user = User.objects.get(id=request.user_id)
            old_causes = user.user_causes.values_list('causes_id', flat=True)
            add_causes = set(new_causes) - set(old_causes)
            to_create = [UserCauses(user_id_id= request.user_id, causes_id_id=subcause_id)
                        for subcause_id in add_causes]
            UserCauses.objects.bulk_create(to_create)

            return Response({'data': new_causes}, status=status.HTTP_201_CREATED)
        else:
            return Response({'error': requestErrorMessagesFormate(validator.get_message())}, status=status.HTTP_200_OK)
    except Exception as exception:
        logerror('causes_subcauses/v2/views.py/add_causes', str(exception))
        return Response({'error': str(exception)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@isAuthenticate
def add_subcauses(request):
    """
    @api {POST} v3/user/causes/subcauses Subcause list
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

        user = User.objects.get(id=request.user_id)
        if validator.validate():
            # insert sub-causes
            new_subcauses = request.data.get('subcauses')
            old_subcauses = user.user_sub_causes.values_list('sub_causes_id', flat=True)
            add_subcauses = set(new_subcauses) - set(old_subcauses)
            to_create = [UserSubCauses(user_id_id= request.user_id, sub_causes_id_id=subcause_id)
                        for subcause_id in add_subcauses]
            UserSubCauses.objects.bulk_create(to_create)
            return Response({'data': new_subcauses}, status=status.HTTP_201_CREATED)
        else:
            return Response({'error': requestErrorMessagesFormate(validator.get_message())}, status=status.HTTP_200_OK)
    except Exception as exception:
        logerror('causes_subcauses/v2/views.py/add_subcauses', str(exception))
        return Response({'error': str(exception)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@isAuthenticate
def user_cause_subcause_list(request):
    """
    @api {GET} v3/user/causes/subcauses Causes and Subcauses list
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


@api_view(['GET'])
def causes_list(request):
    """
    @api {GET} v3/user/causes/list Cause subcauses list
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
                    ...
                ]
            },
            ...
    }
    """
    try:
        validator = ListValidator(request.GET)
        valid = validator.validate()
        if valid:
            if Cause.objects.filter(is_deleted=0, is_active=1).exists():

                subcauses = SubCause.objects.filter(is_active=1, is_deleted=0)\
                .prefetch_related('sub_cause_detail').filter(sub_cause_detail__post_id__is_active=1)\
                .annotate(engagement_count=Count('sub_cause_detail'))

                causes = Cause.objects.filter(is_deleted=0, is_active=1)\
                .prefetch_related(Prefetch('causes_id', queryset=subcauses)).all()

                return Response({'data': CauseSerializer(causes, many=True).data}, status=status.HTTP_200_OK)

            return Response({'error':requestErrorMessagesFormate(validator.get_message())}, status=status.HTTP_200_OK)
    except Exception as exception:
        logerror('causes_subcauses/v2/views.py/causes_list', str(exception))
        return Response({'error':str(exception)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

from collections import OrderedDict
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status
from config.messages import Messages
from utility.authMiddleware import isAuthenticate
from utility.requestErrorFormate import requestErrorMessagesFormate
from utility.rbacService import RbacService
from users.models import UserCauses, UserSubCauses, User
from causes_subcauses.models import Cause, SubCause
from post.models import Post, PostCauses, PostSubCauses
from post.serializers import UserCauseSerializer
from causes_subcauses.serializers import CauseSerializer
from post.views import causes_engagement_count, sub_causes_engagement_count
from .requestSchema import PreferredCauseListValidator, ExplorePostListValidator, AddRemoveCauseValidator
from utility.loggerService import logerror

# Get user preferred cause list
@api_view(['POST'])
@isAuthenticate
@RbacService('post:read')
def explore_preferred_causes(request):
    """
    @api {POST} v1/user/explore/list/preferred-causes User preferred causes
    @apiName User preferred causes
    @apiGroup Explore
    @apiHeader {String} authorization Users unique access-token.
    @apiParam {float} var_latitude User latitude
    @apiParam {float} var_longitude User longitude
    @apiParam {integer} radius Radius
    @apiSuccessExample Success-Response:
    HTTP/1.1 201 OK
    {
        "data": [
            {
                "cause": {
                    "cause_id": 1,
                    "cause_name": "Environment",
                    "cause_image": null,
                    "cause_color": "#fafafa"
                },
                "engagement_count": 2
            },
            {
                "cause": {
                    "cause_id": 2,
                    "cause_name": "Child Welfare",
                    "cause_image": null,
                    "cause_color": "#fafafa"
                },
                "engagement_count": 3
            }
        ]
    }
    """
    try:
        validator = PreferredCauseListValidator(request.data)
        valid = validator.validate()  # validate the request
        if valid:
            var_latitude = float(request.data.get('var_latitude'))
            var_longitude = float(request.data.get('var_longitude'))
            radius = int(request.data.get('radius'))

            user_causes = []
            if UserCauses.objects.filter(user_id=request.user_id).exists():

                user_causes = UserCauses.objects.filter(user_id=request.user_id).all()  # fetch the from database
                causes_serializer = UserCauseSerializer(user_causes, many=True)  # serialize the data

                user_causes = []
                for cause in causes_serializer.data:
                    ordered_cause = dict(OrderedDict(cause))
                    user_causes.append({
                        "cause": ordered_cause['causes'],
                        "engagement_count": engagement_count(
                            ordered_cause['causes_id'],
                            var_latitude,
                            var_longitude,
                            radius
                        )
                    })

            return Response({'data': user_causes}, status=status.HTTP_200_OK)
        else:
            return Response({'error': requestErrorMessagesFormate(validator.get_message())}, status=status.HTTP_200_OK)
    except Exception as exception:
        logerror('post_explore/views.py/explore_preferred_causes', str(exception))
        return Response({'error': str(exception)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Get post list
@api_view(['POST'])
@isAuthenticate
@RbacService('post:read')
def explore_post_list(request):
    """
    @api {POST} v1/user/explore/list/post Post listing
    @apiName Post listing
    @apiGroup Explore
    @apiHeader {String} authorization Users unique access-token.
    @apiParam {float} var_latitude User latitude
    @apiParam {float} var_longitude User longitude
    @apiParam {integer} radius Radius
    @apiParam {integer} cause_id Cause id, 0 => In case of subcause
    @apiParam {integer} subcause_id Subcause id, 0 => In case of cause
    @apiParam {integer} page_limit Page limit
    @apiParam {integer} page_offset Page offset
    @apiSuccessExample {json} Success-Response:
    HTTP/1.1 200 OK
    {
        "data": [
            {
                "post_id": 23,
                "title": "new post",
                "latitude": 28.6863,
                "longitude": 77.2218,
                "is_campaign": 1
            },
            {
                "post_id": 22,
                "title": "hey",
                "latitude": 39.7392,
                "longitude": -104.99,
                "is_campaign": 1
            },
            {
                "post_id": 20,
                "title": "post 17",
                "latitude": 28.6236,
                "longitude": 77.3661,
                "is_campaign": 0
            },
            {
                "post_id": 18,
                "title": "post16",
                "latitude": 28.6236,
                "longitude": 77.3661,
                "is_campaign": 0
            }
        ]
    }
    """
    try:
        validator = ExplorePostListValidator(request.data)
        valid = validator.validate()  # Validate the request
        if valid:
            var_latitude = float(request.data.get('var_latitude'))
            var_longitude = float(request.data.get('var_longitude'))
            radius = int(request.data.get('radius'))
            cause_id = int(request.data.get('cause_id'))
            subcause_id = int(request.data.get('subcause_id'))
            page_limit = request.data.get('page_limit')
            page_offset = request.data.get('page_offset')
            current_user_id = request.user_id

            if subcause_id > 0:
                post_subcauses = PostSubCauses.objects.filter(
                    subcause_id=subcause_id
                ).values_list('post_id', flat=True).distinct()

                # Get post Ids
                post_ids = list(post_subcauses)
            else:
                post_causes = PostCauses.objects.filter(
                    cause_id=cause_id
                ).values_list('post_id', flat=True).distinct()

                # Get post Ids
                post_ids = list(post_causes)

            # Get post ids created by current user because we will remove them from final post listing
            user_posts = Post.objects.filter(created_by=current_user_id).values_list('post_id', flat=True).distinct()
            user_post_ids = list(user_posts)

            # Remove post ids created by current user from post listing
            """
            if len(user_post_ids) > 0:
                for i in user_post_ids:
                    if i in post_ids:
                        post_ids.remove(i)
            """

            if len(post_ids) > 0:

                # Get post listing by distance filter
                post_list = Post.objects.raw('''
                                            (
                                                SELECT post_id, title, latitude, longitude, is_campaign,
                                                (
                                                    6371 * ACOS(
                                                        COS(RADIANS(%s)) * COS(RADIANS(latitude)) * COS(
                                                            RADIANS(longitude) - RADIANS(%s)
                                                        ) + SIN(RADIANS(%s)) * SIN(RADIANS(latitude))
                                                    )
                                                ) AS DISTANCE
                                                FROM posts
                                                WHERE post_id IN %s AND is_active = 1 AND is_campaign = 1
                                                HAVING DISTANCE < %s
                                            )
                                            UNION ALL
                                            (
                                                SELECT
                                                post_id, title, latitude, longitude, is_campaign,
                                                (
                                                    6371 * ACOS(
                                                        COS(RADIANS(%s)) * COS(RADIANS(latitude)) * COS(
                                                            RADIANS(longitude) - RADIANS(%s)
                                                        ) + SIN(RADIANS(%s)) * SIN(RADIANS(latitude))
                                                    )
                                                ) AS DISTANCE
                                                FROM posts
                                                WHERE post_id IN %s AND is_active = 1 AND is_campaign = 0
                                                HAVING DISTANCE < %s
                                            )
                                            ORDER BY post_id DESC
                                            limit %s
                                            offset %s
                                            ''',
                                             [
                                                 var_latitude, var_longitude, var_latitude, post_ids, radius,
                                                 var_latitude, var_longitude, var_latitude, post_ids, radius,
                                                 page_limit, page_offset
                                             ]
                                             )

                post_list_data = []
                for i in post_list:
                    post_details = {
                        "post_id": i.post_id,
                        "title": i.title,
                        "latitude": i.latitude,
                        "longitude": i.longitude,
                        "is_campaign": i.is_campaign
                    }
                    post_list_data.append(post_details)

                return Response({'data': post_list_data}, status=status.HTTP_200_OK)

            return Response({'data': []}, status=status.HTTP_200_OK)
        else:
            return Response({'error': requestErrorMessagesFormate(validator.get_message())}, status=status.HTTP_200_OK)
    except Exception as exception:
        logerror('post_explore/views.py/explore_post_list', str(exception))
        return Response({'error': str(exception)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Get trending cause list
@api_view(['POST'])
@isAuthenticate
@RbacService('post:read')
def trending_cuase_subcause(request):
    """
    @api {POST} v1/user/explore/list/trending/cause-subcause Causes/Subcause trending list
    @apiName Causes/Subcause trending list
    @apiGroup Explore
    @apiHeader {String} authorization Users unique access-token.
    @apiParam {float} var_latitude User latitude
    @apiParam {float} var_longitude User longitude
    @apiParam {integer} radius Radius
    @apiSuccessExample {json} Success-Response:
    HTTP/1.1 200 OK
    {
        "data": [
            {
                "cause_id": 1,
                "cause_name": "Environment",
                "cause_image": null,
                "cause_color": "#fafafa",
                "cause_color_gradient" "#fafafa",
                "is_cause_selected": 0,
                "engagement_count": 10
            },
            {
                "cause_id": 3,
                "cause_name": "Women",
                "cause_image": null,
                "cause_color": "#fafafa",
                "cause_color_gradient" "#fafafa",
                "is_cause_selected": 1,
                "engagement_count": 7
            },
            {
                "cause_id": 2,
                "cause_name": "Child Welfare",
                "cause_image": null,
                "cause_color": "#fafafa",
                "cause_color_gradient" "#fafafa",
                "is_cause_selected": 1,
                "engagement_count": 6
            }
        ]
    }
    """
    try:
        validator = PreferredCauseListValidator(request.data)
        valid = validator.validate()  # Validate the request
        if valid:
            current_user_id = request.user_id
            var_latitude = float(request.data.get('var_latitude'))
            var_longitude = float(request.data.get('var_longitude'))
            radius = int(request.data.get('radius'))

            # Get post listing by distance filter
            post_ids = []
            post_list = Post.objects.raw('''
                                        SELECT post_id,
                                            (
                                                6371 * ACOS(
                                                    COS(RADIANS(%s)) * COS(RADIANS(latitude)) * COS(
                                                        RADIANS(longitude) - RADIANS(%s)
                                                    ) + SIN(RADIANS(%s)) * SIN(RADIANS(latitude))
                                                )
                                            ) AS DISTANCE
                                        FROM posts
                                        WHERE is_active = 1 AND is_campaign = 0
                                        HAVING DISTANCE < %s
                                        ORDER BY DISTANCE
                                        ''',
                                         [var_latitude, var_longitude, var_latitude, radius]
                                         )

            for p in post_list:
                post_ids.append(p.post_id)

            if len(post_ids) > 0:

                causes_list = PostCauses.objects.raw('''
                                                    SELECT pc.id, pc.cause_id, 
                                                    count(pc.post_id) as total_post_count, 
                                                    c.name
                                                    FROM post_causes pc
                                                    LEFT JOIN causes c ON c.id = pc.cause_id
                                                    WHERE c.is_deleted = 0
                                                    AND c.is_active = 1 
                                                    AND pc.post_id IN %s 
                                                    GROUP BY pc.cause_id ORDER BY total_post_count DESC
                                                    ''',
                                                     [post_ids]
                                                     )

                user_causes_ids = UserCauses.objects.filter(
                    user_id=current_user_id
                ).values_list('causes_id', flat=True).distinct()

                causes_list_data = []
                for c in causes_list:
                    case_serializer = CauseSerializer(c.cause_id, many=False)

                    is_cause_selected = 0
                    if case_serializer.data['cause_id'] in user_causes_ids:
                        is_cause_selected = 1

                    cause_details = {
                        "cause_id": case_serializer.data['cause_id'],
                        "cause_name": c.name,
                        "cause_image": case_serializer.data['cause_image'],
                        "cause_color": case_serializer.data['cause_color'],
                        "cause_color_gradient": case_serializer.data['cause_color_gradient'],
                        "is_cause_selected": is_cause_selected,
                        "engagement_count": c.total_post_count
                    }
                    causes_list_data.append(cause_details)

                return Response({'data': causes_list_data}, status=status.HTTP_200_OK)

            return Response({'data': []}, status=status.HTTP_200_OK)
        else:
            return Response({'error': requestErrorMessagesFormate(validator.get_message())}, status=status.HTTP_200_OK)
    except Exception as exception:
        logerror('post_explore/views.py/trending_cuase_subcause', str(exception))
        return Response({'error': str(exception)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Engagement count by cause id
def engagement_count(cause_id, var_latitude, var_longitude, radius):
    try:
        # Get post ids by cause_id
        post_causes = PostCauses.objects.filter(cause_id=cause_id).values_list('post_id', flat=True).distinct()
        post_ids_list = list(post_causes)

        if len(post_ids_list) == 0:
            return 0

        # Get post listing by distance filter
        post_list = Post.objects.raw('''
                                    SELECT
                                    post_id,
                                    (
                                        6371 * ACOS(
                                            COS(RADIANS(%s)) * COS(RADIANS(latitude)) * COS(
                                                RADIANS(longitude) - RADIANS(%s)
                                            ) + SIN(RADIANS(%s)) * SIN(RADIANS(latitude))
                                        )
                                    ) AS DISTANCE
                                    FROM posts
                                    WHERE post_id IN %s AND is_active = 1 AND is_campaign = 0
                                    HAVING  DISTANCE < %s
                                    ORDER BY
                                    DISTANCE        
                                    ''',
                                     [var_latitude, var_longitude, var_latitude, post_ids_list, radius]
                                     )

        # Get total count
        total_count = len(list(post_list))
        return total_count
    except Exception as exception:
        logerror('post_explore/views.py/engagement_count', str(exception))
        return 0


# Get user cause/subcauses list
@api_view(['GET'])
@isAuthenticate
@RbacService('user:read')
def user_cause_subcause(request):
    """
    @api {GET} v1/user/explore/list/user/cause-subcause User causes/subcauses list
    @apiName User cause/subcauses list
    @apiGroup Explore
    @apiHeader {String} authorization Users unique access-token.
    @apiSuccessExample {json} Success-Response:
    HTTP/1.1 200 OK
    {
        "data": [
            {
                "cause_id": 1,
                "cause_name": "Environment",
                "cause_image": null,
                "is_selected": 1,
                "engagement_count": 8,
                "sub_causes": [
                    {
                        "cause_id": 1,
                        "sub_cause_id": 1,
                        "cause_name": "Environment",
                        "sub_cause_name": "Forest",
                        "sub_cause_image": null,
                        "is_selected": 1,
                        "engagement_count": 1
                    },
                    {
                        "cause_id": 1,
                        "sub_cause_id": 2,
                        "cause_name": "Environment",
                        "sub_cause_name": "Activist",
                        "sub_cause_image": null,
                        "is_selected": 1,
                        "engagement_count": 1
                    }
                ]
            },
            {
                "cause_id": 2,
                "cause_name": "Child Welfare",
                "cause_image": null,
                "is_selected": 1,
                "engagement_count": 4,
                "sub_causes": [
                    {
                        "cause_id": 2,
                        "sub_cause_id": 5,
                        "cause_name": "Child Welfare",
                        "sub_cause_name": "Child Subcauses 1",
                        "sub_cause_image": null,
                        "is_selected": 0,
                        "engagement_count": 0
                    }
                ]
            }
        ]
    }
    """
    try:
        current_user_id = request.user_id

        # Get user preferred causes/subcauses
        user_causes_ids = UserCauses.objects.filter(user_id=current_user_id).values_list('causes_id', flat=True).distinct()
        user_subcauses_ids = UserSubCauses.objects.filter(user_id=current_user_id).values_list('sub_causes_id', flat=True).distinct()

        # Get all causes/subcauses exist in the system
        causes = Cause.objects.filter(is_deleted=0, is_active=1).all()  # fetch the from database
        serializer = CauseSerializer(causes, many=True)  # serialize the data

        new_data = []
        for data in serializer.data:

            ordered_data = dict(OrderedDict(data))
            subcauses = []

            for subcause in ordered_data['sub_causes']:

                ordered_subcause = dict(OrderedDict(subcause))

                is_selected = 0
                if ordered_subcause['sub_cause_id'] in user_subcauses_ids:
                    is_selected = 1

                if ordered_subcause['is_active'] == 1 and ordered_subcause['is_deleted'] == 0:
                    subcauses.append({
                        "cause_id": ordered_data['cause_id'],
                        "sub_cause_id": ordered_subcause['sub_cause_id'],
                        "cause_name": ordered_data['cause_name'],
                        "sub_cause_name": ordered_subcause['sub_cause_name'],
                        "sub_cause_image": ordered_subcause['sub_cause_image'],
                        "is_selected": is_selected,
                        "engagement_count": sub_causes_engagement_count(ordered_subcause['sub_cause_id'])
                    })

            is_cause_selected = 0
            if ordered_data['cause_id'] in user_causes_ids:
                is_cause_selected = 1

            new_data.append({
                "cause_id": ordered_data['cause_id'],
                "cause_name": ordered_data['cause_name'],
                "cause_image": ordered_data['cause_image'],
                "is_selected": is_cause_selected,
                "engagement_count": causes_engagement_count(ordered_data['cause_id']),
                "sub_causes": subcauses
            })

        return Response({'data': new_data}, status=status.HTTP_200_OK)
    except Exception as exception:
        logerror('post_explore/views.py/user_cause_subcause', str(exception))
        return Response({'error': str(exception)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT'])
@isAuthenticate
@RbacService('user:update')
def update_cause_subcause(request):
    """
    @api {PUT} v1/user/explore/update/user/cause-subcause Update user causes/subcauses
    @apiName Update user causes/subcauses
    @apiGroup Explore
    @apiHeader {String} authorization Users unique access-token.
    @apiParam {list} user_causes [1,2,3]
    @apiParam {list} user_sub_causes [1,2,3]
    @apiSuccessExample {json} Success-Response:
    HTTP/1.1 200 OK
    {
        "message": "Cause/Subcauses has been updated successfully"
    }
    """
    try:            
        current_user_id = request.user_id
        user_obj = User.objects.get(id=current_user_id)

        # Delete old causes and sub-causes
        UserCauses.objects.filter(user_id=current_user_id).delete()
        UserSubCauses.objects.filter(user_id=current_user_id).delete()

        # Insert causes
        user_causes = request.data.get('user_causes')
        if len(user_causes) > 0:
            for cause_id in user_causes:
                cause = Cause.objects.get(id=cause_id)
                user_causes = UserCauses.objects.create(
                    user_id=user_obj,
                    causes_id=cause,
                )

        # Insert sub-causes
        user_sub_causes = request.data.get('user_sub_causes')
        if len(user_sub_causes) > 0:
            for sub_cause_id in user_sub_causes:
                sub_cause = SubCause.objects.get(id=sub_cause_id)
                user_sub_causes = UserSubCauses.objects.create(
                    user_id=user_obj,
                    sub_causes_id=sub_cause
                )

        return Response({'message': Messages.USER_CAUSES_SUBCAUSES_UPDATED}, status=status.HTTP_200_OK)
    except Exception as exception:
        logerror('post_explore/views.py/update_cause_subcause', str(exception))
        return Response({'error': str(exception)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT'])
@isAuthenticate
@RbacService('user:update')
def add_remove_cause(request):
    """
    @api {PUT} v1/user/explore/add-remove/user/cause Add/Remove user cause
    @apiName Add/Remove user cause
    @apiGroup Explore
    @apiHeader {String} authorization Users unique access-token.
    @apiParam {integer} cause_id Cause id, Default => 0 in case of subcause
    @apiParam {integer} subcause_id Subcause id, Default => 0
    @apiParam {integer} type 1 => Cause, 2 => Subcause
    @apiSuccessExample {json} Success-Response:
    HTTP/1.1 200 OK
    {
        "message": "Cause has been added to your profile"
    }
    """
    try:
        validator = AddRemoveCauseValidator(request.data)
        valid = validator.validate()  # validate the request
        if valid:
            current_user_id = request.user_id
            cause_id = int(request.data.get('cause_id'))
            subcause_id = int(request.data.get('subcause_id'))
            type = int(request.data.get('type'))
            user_obj = User.objects.get(id=current_user_id)

            # Cause
            if type == 1:
                # If not exist then insert
                if not UserCauses.objects.filter(user_id=current_user_id, causes_id=cause_id).exists():

                    cause = Cause.objects.get(id=cause_id)
                    UserCauses.objects.create(
                        user_id=user_obj,
                        causes_id=cause,
                    )
                    response_msg = Messages.USER_CAUSES_ADDED
                else:
                    user_causes = UserCauses.objects.filter(
                        user_id=current_user_id
                    ).values_list('causes_id', flat=True).distinct()

                    # Use should have at least 1 cause in his profile
                    if len(user_causes) == 1:
                        return Response({'error': Messages.USER_CANNOT_REMOVE_CAUSE}, status=status.HTTP_200_OK)

                    UserCauses.objects.filter(user_id=current_user_id, causes_id=cause_id).delete()
                    response_msg = Messages.USER_CAUSES_REMOVED
                return Response({'message': response_msg}, status=status.HTTP_200_OK)

            # Cause
            if type == 2:
                # If not exist then insert
                if not UserSubCauses.objects.filter(user_id=current_user_id, sub_causes_id=subcause_id).exists():

                    subcause = SubCause.objects.get(id=subcause_id)
                    UserSubCauses.objects.create(
                        user_id=user_obj,
                        sub_causes_id=subcause,
                    )
                    response_msg = Messages.USER_SUB_CAUSES_ADDED
                else:
                    UserSubCauses.objects.filter(user_id=current_user_id, sub_causes_id=subcause_id).delete()
                    response_msg = Messages.USER_SUB_CAUSES_REMOVED

            return Response({'message': response_msg}, status=status.HTTP_200_OK)
        else:
            return Response({'error': requestErrorMessagesFormate(validator.get_message())}, status=status.HTTP_200_OK)
    except Exception as exception:
        logerror('post_explore/views.py/add_remove_cause', str(exception))
        return Response({'error': str(exception)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



# This method is used to get list of suggested users
from django.db.models import Count, Q, Sum
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from causes_subcauses.models import Cause, SubCause
from config.messages import Messages
from post.models import Post
from user_interest.models import UserInterest, UserInterestsRequest
from user_interest.v2.serializers import SuggestedUsersSerializer
from user_interest.v2.validators import InputUserSuggestValidator
from users.models import User
from utility.loggerService import logerror
from utility.requestErrorFormate import requestErrorMessagesFormate


def _receive_users(query):
    active_post = Q(post__is_active=True)
    return User.objects.filter(query, is_deleted=0, is_active=1) \
        .annotate(engagement_cnt=Count('post', filter=active_post),
                  upvote_sum=Sum('post__upvote_count', filter=active_post)) \
        .filter(engagement_cnt__gt=0) \
        .order_by('-is_admin_verified', '-engagement_cnt', '-upvote_sum') \
        .values('id', 'name', 'profile_pic', 'email')


def get_suggested_users(current_user_id, user_interest, cause_id, subacauses, page_limit, page_offset):
    print(user_interest)
    query = None
    #Filter по cause_id
    cause_query = Q(user_causes__causes_id=cause_id)
    #
    if subacauses:
        query = Q(user_sub_causes__sub_causes_id__in=subacauses)
    elif cause_id:
        query = cause_query
    
    #Получаем упорядоченный список 
    users = _receive_users(query)


    if users.count() < int(page_limit):
        users = _receive_users(cause_query)

    users = users[page_offset:page_limit + page_offset]

    users_id = (user['id'] for user in users)

    posts = Post.objects.filter(is_active=True, upvote_count__gt=0,
                                created_by__id__in=list(users_id)) \
        .values('created_by', 'post_id', 'title', 'description', 'upvote_count')

    posts = User.objects.annotate()
    
    #slow method

    data = []
    for user in users:
        if user['id'] in user_interest:
            is_interested = 1
        else:
            is_interested = 0

        

        is_request_sent = UserInterestsRequest.objects.filter(
            user_id=current_user_id, interested_user_id=user['id']
        )
        # posts.filter(created_by=user[id]).order_by('-upvote_count').first()
        user_posts = list(filter(lambda u: u['created_by'] == user['id'], posts))
        # post = max(user_posts, key=lambda k: k['upvote_count'])
        post = sorted(user_posts, key=lambda k: k['upvote_count'])[-1]

        data.append({
            'id': user['id'],
            'name': user['name'],
            'profile_pic': user['profile_pic'],
            'is_interested': is_interested,
            'is_request_sent': is_request_sent,
            'email': user['email'],
            'post_id': post['post_id'],
            'post_title': post['title'],
            'post_description': post['description'],
        })

    return SuggestedUsersSerializer(data, many=True).data


@api_view(['POST'])
def suggested_users(request):
    """
    @api {POST} v2/user/interest/suggested-users Get list of suggested users
    @apiName Get list of suggested users
    @apiGroup User Interest
    @apiParam {integer} user_id User Id
    @apiParam {integer} causes_subcauses as dict {cause_id: [subcauses_ids], cause_id: [subcauses_ids],}
    @apiParam {integer} page_limit Page limit
    @apiParam {integer} page_offset Page offset
    @apiSuccessExample {json} Success-Response:
    HTTP/1.1 200 OK
    {
        "data": [
            cause_id:
                [{
                    "name": "Test 30",
                    "id": 33,
                    "email": "test30@yopmail.com",
                    "profile_pic": "profilepic.png",
                    "is_interested": 1,
                    "is_request_sent": false,
                    "post_title": "post title",
                    "post_description": "post description",
                },
                {
                    "name": "Jitendra Singh",
                    "id": 32,
                    "email": "test25@yopmail.com",
                    "profile_pic": "profilepic.png",
                    "is_interested": 1,
                    "is_request_sent": false,
                    "post_title": "post title",
                    "post_description": "post description",
                },
                {
                    "name": "Test 24",
                    "id": 31,
                    "email": "test24@yopmail.com",
                    "profile_pic": "profilepic.png",
                    "is_interested": 0,
                    "is_request_sent": false,
                    "post_title": "post title",
                    "post_description": "post description",
                }],
            cause_id: [{
                    "name": "Test 24",
                    "id": 31,
                    "email": "test24@yopmail.com",
                    "profile_pic": "profilepic.png",
                    "is_interested": 0,
                    "is_request_sent": false,
                    "post_title": "post title",
                    "post_description": "post description",
                }],
        ]
    }
    @apiErrorExample Error-Response:
    HTTP/1.1 200 OK
    {
        "error": "User does not exist"
    }
    """
    try:
        validator = InputUserSuggestValidator(request.data)
        valid = validator.validate()  # validate the request

        if valid:
            """
           {'user_id': user_id,
            'causes_subcauses': {
            cause_id : [subcauses_ids]},  
            'page_limit': page_limit,
            'page_offset': page_offset}
            Пример
            {
                "user_id": 5,
                "causes_subcauses": {
                    5: [128],
                    6: [353, 230]
                },
                "page_limit": 20,
                "page_offset": 0.
            }
            """
            current_user_id = int(request.data['user_id'])
            causes_subcauses = dict(request.data['causes_subcauses'])
            page_limit = int(request.data['page_limit'])
            page_offset = int(request.data['page_offset'])

            # if user does not exists
            if not User.objects.filter(id=current_user_id).exists():
                return Response({'error': Messages.USER_NOT_EXIST}, status=status.HTTP_200_OK)

            cause_ids = list(causes_subcauses.keys())
            if not Cause.objects.filter(id__in=cause_ids).exists():
                return Response({'error': Messages.CAUSE_NOT_EXIST}, status=status.HTTP_200_OK)

            subcauses_ids = []
            for v in causes_subcauses.values():
                subcauses_ids.extend(v)

            if not SubCause.objects.filter(id__in=cause_ids).exists():
                return Response({'error': Messages.SUBCAUSE_NOT_EXIST}, status=status.HTTP_200_OK)

            user_interest = UserInterest.objects.filter(
                user_id=current_user_id
            ).values_list('interested_user_id', flat=True).distinct()

            response = []
            for cause, subacuses in causes_subcauses.items():
                data = get_suggested_users(current_user_id, user_interest, cause, subacuses, page_limit, page_offset)
                response.append({cause: data})

            return Response({'data': response}, status=status.HTTP_200_OK)
        else:
            return Response({'error': requestErrorMessagesFormate(validator.get_message())}, status=status.HTTP_200_OK)
    except Exception as exception:
        logerror('v2/user_interest/views.py/suggsted_users', str(exception))
        return Response({'error': str(exception)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

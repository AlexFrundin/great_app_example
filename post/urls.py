from django.urls import path
from rest_framework import routers
from . import views

router = routers.DefaultRouter()

urlpatterns = [
    path('create', views.create_post),
    path('detail', views.post_detail),
    path('list', views.list_post),
    path('comments', views.post_comments),
    path('list/upvote-users', views.upvote_users),
    path('comment/add', views.post_comment_add),
    path('post-comment/upvote', views.post_comment_upvote),
    path('causes/subcauses', views.user_causes_list),
    path('save', views.user_post_save),
    path('report', views.report_post),
    path('report/list', views.report_option_list),
    path('receive/notification', views.receive_post_notification)
]

urlpatterns += router.urls
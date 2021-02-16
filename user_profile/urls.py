from django.urls import path
from rest_framework import routers
from . import views
from utility.AppScheduler import AppScheduler

router = routers.DefaultRouter()

urlpatterns = [
    path('profile', views.user_own_profile),
    path('self/post/list', views.user_post_list),
    path('profile/edit', views.edit_profile),
    path('post/edit', views.edit_post),
    path('post/delete', views.delete_post),
    path('self/saved/post/list', views.user_saved_post_list),
    path('profile/delete', views.user_delete_profile)
]

urlpatterns += router.urls
from django.urls import path
from rest_framework import routers
from . import views


router = routers.DefaultRouter()

urlpatterns = [
    path('profile', views.user_own_profile),
    path('self/post/list', views.user_post_list),
    path('profile/edit', views.edit_profile),

    
]

urlpatterns += router.urls

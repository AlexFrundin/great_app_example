from django.urls import path
from rest_framework import routers
from . import views

router = routers.DefaultRouter()

urlpatterns = [
    path('basic/profile', views.other_user_profile),
    path('posts', views.other_user_posts),
    path('suggestion/list', views.suggessted_users_list),
    path('full/profile', views.other_user_full_profile),
    path('report', views.report_user),
    path('saved/posts', views.other_user_saved_posts)
]

urlpatterns += router.urls
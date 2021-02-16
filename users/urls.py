from django.urls import path
from rest_framework import routers
from . import views

router = routers.DefaultRouter()

urlpatterns = [
    path('create', views.create),
    path('verify-otp', views.verify_otp),
    path('resend-otp', views.resend_otp),
    path('login', views.login),
    path('forgot-password', views.forgot_password),
    path('reset-password', views.reset_password),
    path('logout', views.logout),
    path('change-password', views.change_password),
    path('refresh-token', views.refresh_token),
    path('block-unblock', views.user_block_unblock),
    path('change-setting', views.user_change_setting),
    path('get-setting', views.user_setting),
    path('blocked/list', views.user_blocked_list),
    path('unblocked/list', views.user_unblocked_list),
    path('interested/list', views.user_interested_list),
    path('version-check', views.version_check)
]

urlpatterns += router.urls
from django.urls import path
from rest_framework import routers
from . import views

router = routers.DefaultRouter()

urlpatterns = [
    path('list', views.notification_list),
    path('clear', views.clear_notifiactions),
    path('count', views.get_notification_count)
]

urlpatterns += router.urls
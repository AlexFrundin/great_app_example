from django.urls import path
from rest_framework import routers

from . import views

router = routers.DefaultRouter()

urlpatterns = [
    path('suggested-users', views.suggested_users),
]

urlpatterns += router.urls

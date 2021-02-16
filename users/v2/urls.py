from django.urls import path
from rest_framework import routers

from . import views

router = routers.DefaultRouter()

urlpatterns = [
    path('verify-email', views.verify_email),
    path('create', views.create),
]

urlpatterns += router.urls

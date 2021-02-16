from django.urls import path
from rest_framework import routers
from . import views

router = routers.DefaultRouter()

urlpatterns = [
    # first landing page url
    path(r'', views.index),
]

urlpatterns += router.urls

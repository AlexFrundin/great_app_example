from django.urls import path
from rest_framework import routers
from . import views

router = routers.DefaultRouter()

urlpatterns = [
    path('suggested-users', views.suggsted_users),
    path('add-remove', views.add_remove),
    path('approve-reject', views.approve_reject_request),
]

urlpatterns += router.urls
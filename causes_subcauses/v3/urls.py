from django.urls import path
from rest_framework import routers

from . import views

router = routers.DefaultRouter()

urlpatterns = [
    path('', views.add_causes),
    path('subcauses', views.add_subcauses),
    path('subcauses/list', views.user_cause_subcause_list),
    path('list', views.causes_list),
]

urlpatterns += router.urls

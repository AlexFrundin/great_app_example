from django.urls import path
from rest_framework import routers
from . import views

router = routers.DefaultRouter()

urlpatterns = [
    path('list', views.static_content),
    path('save-newsletter', views.save_newsletter),
    path('search', views.search_content),
]

urlpatterns += router.urls
from django.urls import path
from rest_framework import routers
from . import views

router = routers.DefaultRouter()

urlpatterns = [
    path('list/preferred-causes', views.explore_preferred_causes),
    path('list/post', views.explore_post_list),
    path('list/trending/cause-subcause', views.trending_cuase_subcause),
    path('list/user/cause-subcause', views.user_cause_subcause),
    path('update/user/cause-subcause', views.update_cause_subcause),
    path('add-remove/user/cause', views.add_remove_cause)
]

urlpatterns += router.urls

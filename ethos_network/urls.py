"""
ethos_network URL Configuration
The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))

Function get_include() provides work for api version 2
 returns resources  for api version 2, if any
"""
from django.conf.urls import include
from django.urls import path
from .unifications_route import get_include

urlpatterns = [
    # App URLs v1
    path('', include('content.defaultUrls')),
    path('v1/user/', include('users.urls')),
    path('v1/user/', include('user_profile.urls')),
    path('v1/user/content/', include('content.urls')),
    path('v1/user/causes/', include('causes_subcauses.urls')),
    path('v1/user/interest/', include('user_interest.urls')),
    path('v1/other/user/', include('other_user_profile.urls')),
    path('v1/user/notification/', include('notifications.urls')),
    path('v1/user/chat/', include('chat.urls')),


    # Admin URLs v1
    path('v1/admin/user/', include('admin_users.urls')),
    path('v1/user/post/', include('post.urls')),
    path('v1/user/explore/', include('post_explore.urls')),
    path('v1/admin/post/', include('admin_post.urls')),
    path('v1/admin/causes/', include('admin_causes.urls')),
    path('v1/admin/report/management/', include('admin_report_management.urls')),
    path('v1/admin/reports/', include('admin_post_reports.urls')),
    path('v1/admin/content/moderation/', include('admin_content_moderation.urls')),

    # App URLs v2
    *get_include('v2/user/', ('users.urls')),
    *get_include('v2/user/', ('user_profile.urls')),
    *get_include('v2/user/content/', ('content.urls')),
    *get_include('v2/user/causes/', ('causes_subcauses.urls')),
    *get_include('v2/user/interest/', ('user_interest.urls')),
    *get_include('v2/other/user/', ('other_user_profile.urls')),
    *get_include('v2/user/notification/', ('notifications.urls')),
    *get_include('v2/user/chat/', ('chat.urls')),

    # Admin URLs v2
    *get_include('v2/admin/user/', ('admin_users.urls')),
    *get_include('v2/user/post/', ('post.urls')),
    *get_include('v2/user/explore/', ('post_explore.urls')),
    *get_include('v2/admin/post/', ('admin_post.urls')),
    *get_include('v2/admin/causes/', ('admin_causes.urls')),
    *get_include('v2/admin/report/management/', ('admin_report_management.urls')),
    *get_include('v2/admin/reports/', ('admin_post_reports.urls')),
    *get_include('v2/admin/content/moderation/', ('admin_content_moderation.urls')),

    path('v3/user/', include('user_profile.v2.urls')),
    path('v3/user/causes/', include('causes_subcauses.v3.urls')),
    
]

# from django.conf import settings
# from django.conf.urls.static import static
#
# urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

from rest_framework.schemas import get_schema_view
from django.views.generic import TemplateView
# api documentation
urlpatterns += [
    path('openv2-schema', get_schema_view(
        title="Ethos app",
        description="Develop app",
        version="1.0.0",
        public=True,
    ), name='openv2-schema'),
    path('documentation/', TemplateView.as_view(
        template_name='documentation.html',
        extra_context={'schema_url': 'openv2-schema'}
    ), name='swagger-ui'),

]

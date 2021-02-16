from django.urls import path

from . import views

urlpatterns = [
    path('request', views.send_request),
    path('approve-reject', views.approve_reject),
    path('list', views.chat_list),
    path('group/create', views.create_group),
    path('group/edit', views.edit_group),
    path('group/member/add-remove', views.add_remove_member),
    path('group/detail', views.group_details),
    path('group/update/message', views.update_last_message),
    path('group/leave', views.leave_group)
]

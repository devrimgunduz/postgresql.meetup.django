from django.urls import path
from . import views_admin

urlpatterns = [
    path('',                            views_admin.admin_index,   name='admin_index'),
    path('login/',                      views_admin.admin_login,   name='admin_login'),
    path('logout/',                     views_admin.admin_logout,  name='admin_logout'),

    path('meetups/new/',                views_admin.meetup_edit,   name='meetup_new'),
    path('meetups/<int:pk>/edit/',      views_admin.meetup_edit,   name='meetup_edit'),
    path('meetups/<int:pk>/delete/',    views_admin.meetup_delete, name='meetup_delete'),

    path('meetups/<int:meetup_pk>/talks/',          views_admin.talks_list,  name='talks_list'),
    path('talks/<int:pk>/delete/',                  views_admin.talk_delete, name='talk_delete'),

    path('languages/',                  views_admin.languages_list, name='languages_list'),
    path('users/',                      views_admin.users_list,     name='users_list'),
]

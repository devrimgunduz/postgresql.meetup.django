from django.urls import path
from . import views_public

urlpatterns = [
    path('',             views_public.index,    name='index'),
    path('previous/',    views_public.previous,  name='previous'),
]

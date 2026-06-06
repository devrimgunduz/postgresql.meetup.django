from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('django-admin/', admin.site.urls),          # Django built-in admin
    path('admin-panel/', include('meetups.urls_admin')),  # Custom admin panel
    path('', include('meetups.urls_public')),         # Public site
]

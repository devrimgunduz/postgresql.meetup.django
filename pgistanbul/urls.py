from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('django-admin/', admin.site.urls),               # Django built-in admin
    path('admin-panel/', include('meetups.urls_admin')),  # Custom admin panel
    path('', include('meetups.urls_public')),             # Public site
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

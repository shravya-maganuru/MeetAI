from django.contrib import admin
from django.urls import path, include
from core.views import homepage 
from django.conf import settings
from django.conf.urls.static import static # <-- CRITICAL IMPORT 1

urlpatterns = [
    # Serves the homepage
    path('', homepage, name='homepage'), 
    
    # Includes all the API endpoints defined in core/urls.py
    path('api/', include('core.urls')),

    path('admin/', admin.site.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) 
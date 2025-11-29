from django.contrib import admin
from django.urls import path, include
from django.views.generic.base import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('reportes/', include('reportes.urls')),
    path('sistema/', include('core.urls')),
    path('auditoria/', include('auditoria.urls')),
    path('notifications/', include('notifications.urls')),
    
    # Redirect root to login
    path('', RedirectView.as_view(url='/accounts/login/', permanent=False)),
]
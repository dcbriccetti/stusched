from django.urls import path, include
from django.contrib import admin

urlpatterns = [
    path('apps/sis/', include('app.urls')),
    path('apps/admin/', admin.site.urls),
]

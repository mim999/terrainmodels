from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('', include('terrainmap.urls')),
    path('admin/', admin.site.urls),
]
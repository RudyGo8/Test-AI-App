"""
URL configuration for test_ai_demo project.
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('test_ai_app.urls')),
]

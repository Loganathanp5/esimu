from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/game/', include('game.urls_api')),
    path('', include('game.urls_web')),
]

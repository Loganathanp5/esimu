from django.urls import path

from . import views

urlpatterns = [
    path('start/', views.api_start, name='api-start'),
    path('choose/', views.api_choose, name='api-choose'),
    path('result/<uuid:session_id>/', views.api_result, name='api-result'),
]

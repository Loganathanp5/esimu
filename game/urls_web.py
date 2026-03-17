from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('game/', views.game_page, name='game-page'),
    path('result/<uuid:session_id>/', views.result_page, name='result-page'),
]

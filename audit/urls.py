from . import views
from django.urls import path


urlpatterns = [
    path('bitacora/', views.bitacora_list, name='bitacora-list'),
    path('bitacora/stats/', views.bitacora_stats, name='bitacora-stats'),
]

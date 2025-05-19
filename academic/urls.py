from . import views
from django.urls import path


urlpatterns = [
    # CRUD de Materias
    path('materias/', views.materia_list_create, name='materia-list-create'),
    path('materias/<int:pk>/', views.materia_detail, name='materia-detail'),

    # CRUD de Aulas
    path('aulas/', views.aula_list_create, name='aula-list-create'),
    path('aulas/<int:pk>/', views.aula_detail, name='aula-detail'),

    # CRUD de Niveles y Grupos
    path('niveles/', views.nivel_list_create, name='nivel-list-create'),
    path('grupos/', views.grupo_list_create, name='grupo-list-create'),

    # Estadísticas
    path('stats/', views.academic_stats, name='academic-stats'),
]

from . import views
from django.urls import path

urlpatterns = [
    # Gestión de exámenes
    path('mis-examenes/', views.mis_examenes, name='mis-examenes'),
    path('mis-examenes/<int:pk>/', views.examen_detail, name='examen-detail'),

    # Gestión de tareas
    path('mis-tareas/', views.mis_tareas, name='mis-tareas'),
    path('mis-tareas/<int:pk>/', views.tarea_detail, name='tarea-detail'),

    # Endpoints auxiliares
    path('opciones/profesor-materias/', views.opciones_profesor_materias, name='opciones-profesor-materias'),
    path('opciones/trimestres/', views.opciones_trimestres, name='opciones-trimestres'),
]

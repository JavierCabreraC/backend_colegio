from . import views
from django.urls import path

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('activity/', views.user_activity, name='user-activity'),

    path('profesores/', views.profesor_list_create, name='profesor-list-create'),
    path('profesores/<int:pk>/', views.profesor_detail, name='profesor-detail'),

    path('alumnos/', views.alumno_list_create, name='alumno-list-create'),
    path('alumnos/<int:pk>/', views.alumno_detail, name='alumno-detail'),

    path('dashboard/director/', views.dashboard_director, name='dashboard-director'),
]
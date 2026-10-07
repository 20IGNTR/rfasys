from django.urls import path
from . import views

urlpatterns = [
    path('', views.inicio, name='inicio'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('logout/', views.cerrar_sesion, name='cerrar_sesion'),
    path('ads/proveedores/', views.ads_proveedores, name='ads_proveedores'),
    path('ads/clientes/', views.ads_clientes, name='ads_clientes'),
    path('ads/empleados/', views.ads_empleados, name='ads_empleados'),
    path('notas/<int:nota_id>/eliminar/', views.nota_eliminar, name='home_nota_eliminar'),
]
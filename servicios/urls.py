from django.urls import path
from . import views

urlpatterns = [
    path('taller/', views.taller_lista, name='servicios_taller'),
    path('taller/nueva-orden/', views.orden_crear, name='servicios_orden_crear'),
    path('taller/<int:orden_id>/editar/', views.orden_editar, name='servicios_orden_editar'),
    path('taller/<int:orden_id>/eliminar/', views.orden_eliminar, name='servicios_orden_eliminar'),
    path('detailing/', views.detailing_lista, name='servicios_detailing'),
]
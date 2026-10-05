from django.urls import path
from . import views

urlpatterns = [
    path('ingresos/', views.ingresos_lista, name='compras_ingresos'),
    path('ingresos/nuevo/', views.ingreso_crear, name='compras_ingreso_crear'),
    path('ingresos/<int:ingreso_id>/editar/', views.ingreso_editar, name='compras_ingreso_editar'),
    path('ingresos/<int:ingreso_id>/eliminar/', views.ingreso_eliminar, name='compras_ingreso_eliminar'),
    path('inventario/', views.inventario_lista, name='compras_inventario'),
    
    # Consola unificada de Transferencias
    path('transferencias/', views.transferencias_lista, name='compras_transferencias'),
    path('transferencias/nueva/', views.transferencias_lista, name='compras_transferencia_crear'),
    path('transferencias/<int:transferencia_id>/', views.transferencia_detalle, name='compras_transferencia_detalle'),
    path('transferencias/<int:transferencia_id>/eliminar/', views.transferencia_eliminar, name='compras_transferencia_eliminar'),
    path('reembolsos/', views.reembolsos_lista, name='compras_reembolsos'),  # <-- NUEVA RUTA
    # Historial / Kardex
    path('historial/', views.historial_kardex, name='compras_historial'),
]
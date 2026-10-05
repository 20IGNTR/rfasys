from django.urls import path
from . import views

urlpatterns = [
    path('presupuestos/', views.presupuestos_lista, name='ventas_presupuestos'),
    path('facturas/', views.facturas_lista, name='ventas_facturas'),
    path('remisiones/', views.remisiones_lista, name='ventas_remisiones'),  # <-- NUEVA RUTA
]
from django.contrib import admin
from .models import OrdenTrabajo, DetalleOrden, ClienteRecurrente

class DetalleOrdenInline(admin.TabularInline):
    model = DetalleOrden
    extra = 0

@admin.register(OrdenTrabajo)
class OrdenTrabajoAdmin(admin.ModelAdmin):
    list_display = ('numero_orden', 'moto_modelo', 'cliente_nombre', 'mecanico', 'estado', 'total_presupuesto')
    list_filter = ('estado', 'mecanico')
    search_fields = ('numero_orden', 'cliente_nombre', 'moto_placa', 'moto_modelo')
    inlines = [DetalleOrdenInline]

@admin.register(ClienteRecurrente)
class ClienteRecurrenteAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'telefono', 'moto_modelo', 'moto_placa', 'activo')
    search_fields = ('nombre', 'telefono', 'moto_placa')
    list_filter = ('activo',)
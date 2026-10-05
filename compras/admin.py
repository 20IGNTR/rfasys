from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from .models import Proveedor, Deposito, Articulo, Ingreso, DetalleIngreso, Stock

# 1. Recurso y Administración para Proveedores (Manual + Importación Masiva)
class ProveedorResource(resources.ModelResource):
    class Meta:
        model = Proveedor
        import_id_fields = ('ruc',)  # El RUC actúa como identificador único para evitar duplicados
        fields = ('razon_social', 'ruc', 'timbrado', 'telefono', 'correo', 'direccion', 'activo')
        export_order = ('razon_social', 'ruc', 'timbrado', 'telefono', 'correo', 'direccion', 'activo')

@admin.register(Proveedor)
class ProveedorAdmin(ImportExportModelAdmin):
    resource_class = ProveedorResource
    list_display = ('razon_social', 'ruc', 'timbrado', 'telefono', 'correo', 'activo')
    search_fields = ('razon_social', 'ruc', 'timbrado')
    list_filter = ('activo',)

# 2. Catálogo de Depósitos (Manual)
@admin.register(Deposito)
class DepositoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'ubicacion', 'activo')
    search_fields = ('nombre',)
    list_filter = ('activo',)

# 3. Recurso y Administración para Artículos (Manual + Importación Masiva)
class ArticuloResource(resources.ModelResource):
    class Meta:
        model = Articulo
        import_id_fields = ('codigo',)
        fields = ('codigo', 'nombre', 'presentacion', 'costo_referencia', 'activo')
        export_order = ('codigo', 'nombre', 'presentacion', 'costo_referencia', 'activo')

@admin.register(Articulo)
class ArticuloAdmin(ImportExportModelAdmin):
    resource_class = ArticuloResource
    list_display = ('codigo', 'nombre', 'presentacion', 'costo_referencia', 'activo')
    search_fields = ('codigo', 'nombre')
    list_filter = ('activo',)

# 4. Cabecera y Detalle de Ingresos (Manual / Auditoría)
class DetalleIngresoInline(admin.TabularInline):
    model = DetalleIngreso
    extra = 0
    readonly_fields = ('subtotal',)

@admin.register(Ingreso)
class IngresoAdmin(admin.ModelAdmin):
    list_display = ('numero_registro', 'proveedor', 'numero_comprobante', 'fecha_comprobante', 'total_general', 'creado_por', 'anulado')
    list_filter = ('tipo_documento', 'condicion', 'moneda', 'anulado', 'fecha_comprobante')
    search_fields = ('numero_registro', 'numero_comprobante', 'proveedor__razon_social')
    readonly_fields = ('numero_registro', 'fecha_insercion', 'fecha_modificacion')
    inlines = [DetalleIngresoInline]

# 5. Control de Existencias de Inventario (Manual / Vista)
@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ('articulo', 'deposito', 'cantidad', 'ultima_actualizacion')
    list_filter = ('deposito',)
    search_fields = ('articulo__codigo', 'articulo__nombre', 'deposito__nombre')
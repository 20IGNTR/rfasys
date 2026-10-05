from decimal import Decimal
from django.db import models
from django.contrib.auth.models import User
from compras.models import Articulo, Deposito


class OrdenTrabajo(models.Model):
    ESTADO_CHOICES = [
        ('banco', 'En Banco'),
        ('repuesto', 'Espera Repuesto'),
        ('listo', 'Listo Retiro'),
        ('entregado', 'Entregado'),
        ('cancelado', 'Cancelado'),
    ]

    numero_orden = models.CharField(max_length=20, unique=True, verbose_name="N° Orden")
    cliente_nombre = models.CharField(max_length=150, verbose_name="Cliente")
    cliente_telefono = models.CharField(max_length=50, verbose_name="Teléfono / WhatsApp")
    moto_modelo = models.CharField(max_length=120, verbose_name="Vehículo / Modelo")
    moto_placa = models.CharField(max_length=30, verbose_name="Chapa / Placa")
    moto_kilometraje = models.IntegerField(null=True, blank=True, verbose_name="Kilometraje")

    mecanico = models.ForeignKey(User, on_delete=models.PROTECT, related_name='ordenes_asignadas', verbose_name="Mecánico")
    deposito_origen = models.ForeignKey(Deposito, on_delete=models.PROTECT, related_name='ordenes_trabajo', null=True, blank=True, verbose_name="Depósito Salida")
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='banco')
    fecha_promesa = models.DateField(null=True, blank=True, verbose_name="Promesa de Entrega")

    motivo_ingreso = models.TextField(verbose_name="Motivo de Ingreso")
    observaciones_vehiculo = models.TextField(blank=True, null=True, verbose_name="Detalle / Observaciones")

    total_presupuesto = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))

    creado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='ordenes_creadas')
    modificado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='ordenes_modificadas')
    fecha_ingreso = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"#{self.numero_orden} - {self.moto_modelo} ({self.cliente_nombre})"

    class Meta:
        verbose_name = "Orden de Trabajo"
        verbose_name_plural = "Órdenes de Trabajo"
        ordering = ['-fecha_ingreso']


class DetalleOrden(models.Model):
    TIPO_CHOICES = [
        ('repuesto', 'Repuesto / Insumo'),
        ('producto', 'Producto'),
        ('servicio', 'Mano de Obra'),
    ]

    orden = models.ForeignKey(OrdenTrabajo, on_delete=models.CASCADE, related_name='detalles')
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='repuesto')
    articulo = models.ForeignKey(Articulo, on_delete=models.SET_NULL, null=True, blank=True)
    deposito = models.ForeignKey('compras.Deposito', on_delete=models.SET_NULL, null=True, blank=True)
    concepto_manual = models.CharField(max_length=200, blank=True, null=True)
    cantidad = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('1.00'))
    precio_unitario = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    subtotal = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))

    def __str__(self):
        desc = self.articulo.nombre if self.articulo else self.concepto_manual
        return f"{self.orden.numero_orden} - {desc}"

class ClienteRecurrente(models.Model):
    nombre = models.CharField(max_length=150, verbose_name="Nombre & Apellido")
    telefono = models.CharField(max_length=50, blank=True, null=True, verbose_name="Teléfono / WhatsApp")
    moto_modelo = models.CharField(max_length=120, blank=True, null=True, verbose_name="Vehículo / Modelo habitual")
    moto_placa = models.CharField(max_length=30, blank=True, null=True, verbose_name="Chapa / Matrícula")
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Cliente Recurrente"
        verbose_name_plural = "Clientes Recurrentes"
        ordering = ['nombre']

    def __str__(self):
        return f"{self.nombre} ({self.moto_modelo or 'Sin moto'})"
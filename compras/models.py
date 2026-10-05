from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from decimal import Decimal
from decimal import Decimal
from django.core.validators import MinValueValidator
from django.contrib.auth.models import User

# ==============================================================================
# 1. MODELOS BASE DEL CATÁLOGO
# ==============================================================================

class Proveedor(models.Model):
    razon_social = models.CharField(max_length=150)
    ruc = models.CharField(max_length=30, unique=True)
    timbrado = models.CharField(max_length=8, blank=True, null=True)
    telefono = models.CharField(max_length=50, blank=True, null=True)
    correo = models.EmailField(blank=True, null=True)
    direccion = models.CharField(max_length=255, blank=True, null=True)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.razon_social} ({self.ruc})"

class Deposito(models.Model):
    nombre = models.CharField(max_length=100)
    ubicacion = models.CharField(max_length=200, blank=True, null=True)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre

class Articulo(models.Model):
    codigo = models.CharField(max_length=50, unique=True)
    nombre = models.CharField(max_length=150)
    presentacion = models.CharField(max_length=80, blank=True, null=True)
    costo_referencia = models.DecimalField(max_digits=14, decimal_places=2, default=0.00)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.nombre} ({self.codigo})"

# ==============================================================================
# 2. MODELO PRINCIPAL: INGRESO DE COMPRAS (CABECERA Y AUDITORÍA)
# ==============================================================================

class Ingreso(models.Model):
    TIPO_DOC_CHOICES = [
        ('factura', 'Factura'),
        ('recibo', 'Recibo / Boleta Interna'),
        ('remision', 'Nota de Remisión'),
        ('importacion', 'Despacho / Importación'),
        ('credito', 'Nota de Crédito'),
    ]
    tipo_documento = models.CharField(max_length=20, choices=TIPO_DOC_CHOICES, default='factura')
    timbrado = models.CharField(max_length=8, blank=True, null=True, verbose_name="Timbrado")

    CONDICION_CHOICES = [
        ('contado', 'Contado'),
        ('credito', 'Crédito'),
    ]

    METODO_CHOICES = [
        ('efectivo', 'Efectivo'),
        ('transferencia', 'Transferencia'),
        ('tarjeta', 'Tarjeta'),
    ]

    MONEDA_CHOICES = [
        ('PYG', 'PYG (Gs.)'),
        ('USD', 'USD ($)'),
        ('BRL', 'BRL (R$)'),
        ('ARS', 'ARS ($)'),
        ('EUR', 'EUR (€)'),
    ]

    # Datos Generales del Comprobante
    numero_registro = models.CharField(max_length=20, unique=True, editable=False)
    proveedor = models.ForeignKey(Proveedor, on_delete=models.PROTECT, related_name='ingresos')
    timbrado = models.CharField(max_length=8)
    tipo_documento = models.CharField(max_length=20, choices=TIPO_DOC_CHOICES, default='factura')
    numero_comprobante = models.CharField(max_length=50)
    fecha_comprobante = models.DateField()
    deposito_destino = models.ForeignKey(Deposito, on_delete=models.PROTECT, related_name='ingresos')
    recibido_por = models.ForeignKey(User, on_delete=models.PROTECT, related_name='compras_recibidas')

    # Condiciones Comerciales y Divisas
    condicion = models.CharField(max_length=15, choices=CONDICION_CHOICES, default='contado')
    metodo_pago = models.CharField(max_length=20, choices=METODO_CHOICES, default='efectivo')
    moneda = models.CharField(max_length=5, choices=MONEDA_CHOICES, default='PYG')
    cotizacion = models.DecimalField(max_digits=10, decimal_places=4, default=1.0000)
    comprobante_adjunto = models.FileField(upload_to='comprobantes_compras/%Y/%m/', blank=True, null=True)
    observaciones = models.TextField(blank=True, null=True)

    # Totales y Liquidaciones (en moneda base)
    total_exentas = models.DecimalField(max_digits=16, decimal_places=2, default=0.00)
    total_iva5 = models.DecimalField(max_digits=16, decimal_places=2, default=0.00)
    total_iva10 = models.DecimalField(max_digits=16, decimal_places=2, default=0.00)
    liquidacion_iva = models.DecimalField(max_digits=16, decimal_places=2, default=0.00)
    total_general = models.DecimalField(max_digits=16, decimal_places=2, default=0.00)

    # Auditoría Interna / Trazabilidad
    creado_por = models.ForeignKey(User, on_delete=models.PROTECT, related_name='ingresos_creados')
    modificado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='ingresos_modificados')
    fecha_insercion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    anulado = models.BooleanField(default=False)

    class Meta:
        ordering = ['-id']

    def __str__(self):
        return f"Ingreso #{self.numero_registro} — {self.proveedor.razon_social}"

    def save(self, *args, **kwargs):
        if not self.numero_registro:
            ultimo = Ingreso.objects.order_by('-id').first()
            nuevo_num = 1 if not ultimo else ultimo.id + 1
            self.numero_registro = f"{nuevo_num:05d}"
        super().save(*args, **kwargs)

# ==============================================================================
# 3. DETALLE DE ARTÍCULOS POR COMPROBANTE
# ==============================================================================

class DetalleIngreso(models.Model):
    IVA_CHOICES = [
        (0, 'Exenta'),
        (5, 'IVA 5%'),
        (10, 'IVA 10%'),
    ]

    ingreso = models.ForeignKey(Ingreso, on_delete=models.CASCADE, related_name='detalles')
    articulo = models.ForeignKey(Articulo, on_delete=models.PROTECT, related_name='detalles_compra')
    lote_proveedor = models.CharField(max_length=60, blank=True, null=True)
    cantidad = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    costo_unitario = models.DecimalField(max_digits=14, decimal_places=2, default=0.00)
    iva_porcentaje = models.IntegerField(choices=IVA_CHOICES, default=10)
    subtotal = models.DecimalField(max_digits=16, decimal_places=2, default=0.00)

    def __str__(self):
        return f"{self.articulo.nombre} x {self.cantidad}"

# ==============================================================================
# 4. CONTROL DE STOCK POR ARTÍCULO Y DEPÓSITO
# ==============================================================================

class Stock(models.Model):
    articulo = models.ForeignKey(Articulo, on_delete=models.PROTECT, related_name='existencias')
    deposito = models.ForeignKey(Deposito, on_delete=models.PROTECT, related_name='existencias')
    cantidad = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    ultima_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('articulo', 'deposito')

    def __str__(self):
        return f"{self.articulo.codigo} en {self.deposito.nombre}: {self.cantidad}"

# ==============================================================================
# TRANSFERENCIAS ENTRE DEPÓSITOS
# ==============================================================================

class Transferencia(models.Model):
    numero_transferencia = models.CharField(max_length=30, unique=True, verbose_name="N° Transferencia")
    deposito_origen = models.ForeignKey(Deposito, on_delete=models.PROTECT, related_name='transferencias_salida')
    deposito_destino = models.ForeignKey(Deposito, on_delete=models.PROTECT, related_name='transferencias_entrada')
    fecha = models.DateField(verbose_name="Fecha Transferencia")
    observaciones = models.TextField(blank=True, null=True, verbose_name="Motivo / Observaciones")
    creado_por = models.ForeignKey(User, on_delete=models.PROTECT, related_name='transferencias_creadas')
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Transferencia"
        verbose_name_plural = "Transferencias"
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f"{self.numero_transferencia} ({self.deposito_origen} -> {self.deposito_destino})"


class DetalleTransferencia(models.Model):
    transferencia = models.ForeignKey(Transferencia, on_delete=models.CASCADE, related_name='detalles')
    articulo = models.ForeignKey(Articulo, on_delete=models.PROTECT, related_name='detalles_transferencia')
    cantidad = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])

    def __str__(self):
        return f"{self.articulo.nombre} x {self.cantidad}"


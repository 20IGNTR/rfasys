from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db import transaction
from django.db.models import Sum
from compras.models import Articulo, Deposito, Stock
from .models import OrdenTrabajo, DetalleOrden, ClienteRecurrente
from datetime import date

@login_required
def taller_lista(request):
    """Bandeja técnica con filtro mensual automático y navegación histórica."""
    hoy = date.today()

    # 1. Obtener mes y año solicitados (por defecto toma el mes actual)
    try:
        mes_seleccionado = int(request.GET.get('mes', hoy.month))
        anio_seleccionado = int(request.GET.get('anio', hoy.year))
    except (ValueError, TypeError):
        mes_seleccionado = hoy.month
        anio_seleccionado = hoy.year

    # 2. Calcular mes anterior y mes siguiente
    if mes_seleccionado == 1:
        mes_anterior = 12
        anio_anterior = anio_seleccionado - 1
    else:
        mes_anterior = mes_seleccionado - 1
        anio_anterior = anio_seleccionado

    if mes_seleccionado == 12:
        mes_siguiente = 1
        anio_siguiente = anio_seleccionado + 1
    else:
        mes_siguiente = mes_seleccionado + 1
        anio_siguiente = anio_seleccionado

    meses_nombres = [
        "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
        "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
    ]
    nombre_mes = f"{meses_nombres[mes_seleccionado - 1]} {anio_seleccionado}"

    # 3. Filtrar órdenes registradas en ese mes/año
    ordenes_mes = OrdenTrabajo.objects.filter(
        fecha_ingreso__year=anio_seleccionado,
        fecha_ingreso__month=mes_seleccionado
    ).select_related('mecanico', 'creado_por').order_by('-fecha_ingreso')

    # 4. Métricas computadas sobre el mes seleccionado
    total_en_banco = ordenes_mes.filter(estado='banco').count()
    total_espera_repuesto = ordenes_mes.filter(estado='repuesto').count()
    total_listo_retiro = ordenes_mes.filter(estado__in=['listo', 'entregado']).count()
    total_servicios = ordenes_mes.count()

    context = {
        'ordenes': ordenes_mes,
        'total_en_banco': total_en_banco,
        'total_espera_repuesto': total_espera_repuesto,
        'total_listo_retiro': total_listo_retiro,
        'total_servicios': total_servicios,
        'nombre_mes': nombre_mes,
        'mes_anterior': mes_anterior,
        'anio_anterior': anio_anterior,
        'mes_siguiente': mes_siguiente,
        'anio_siguiente': anio_siguiente,
        'es_mes_actual': (mes_seleccionado == hoy.month and anio_seleccionado == hoy.year),
    }
    return render(request, 'servicios/taller_lista.html', context)

@login_required
def detailing_lista(request):
    return render(request, 'servicios/detailing_lista.html')

@login_required
def orden_crear(request):
    """Creación y guardado de Orden de Trabajo con redirección garantizada a la lista."""
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # 1. Lectura limpia de campos de cabecera
                cliente_nombre = request.POST.get('cliente_nombre', '').strip()
                cliente_tel = request.POST.get('cliente_telefono', '').strip()
                moto_mod = request.POST.get('moto_modelo', '').strip()
                moto_plc = request.POST.get('moto_placa', '').strip().upper()

                # ==============================================================
                # REGISTRO TRANSPARENTE EN SEGUNDO PLANO (CLIENTES RECURRENTES)
                # ==============================================================
                if cliente_nombre:
                    ClienteRecurrente.objects.update_or_create(
                        nombre=cliente_nombre,
                        defaults={
                            'telefono': cliente_tel,
                            'moto_modelo': moto_mod,
                            'moto_placa': moto_plc,
                            'activo': True,
                        }
                    )

                # ==============================================================
                # 2. GENERACIÓN DE CORRELATIVO SEGURO (#OT-00001)
                # ==============================================================
                ultima_orden = OrdenTrabajo.objects.order_by('-id').first()
                if ultima_orden and ultima_orden.numero_orden.startswith("OT-"):
                    try:
                        ultimo_num = int(ultima_orden.numero_orden.replace("OT-", ""))
                        siguiente_num = ultimo_num + 1
                    except ValueError:
                        siguiente_num = (OrdenTrabajo.objects.count() + 1)
                else:
                    siguiente_num = 1
                
                # Evitar cualquier duplicado en la base de datos
                numero_orden = f"OT-{siguiente_num:05d}"
                while OrdenTrabajo.objects.filter(numero_orden=numero_orden).exists():
                    siguiente_num += 1
                    numero_orden = f"OT-{siguiente_num:05d}"
                # Continúa con la creación de la cabecera OrdenTrabajo.objects.create(...)
                
                # Garantizar que el número generado no exista en la BD
                numero_orden = f"OT-{siguiente_num:05d}"
                while OrdenTrabajo.objects.filter(numero_orden=numero_orden).exists():
                    siguiente_num += 1
                    numero_orden = f"OT-{siguiente_num:05d}"

                # 2. Mecánico asignado
                mecanico_id = request.POST.get('mecanico')
                mecanico_obj = User.objects.filter(id=mecanico_id).first() if mecanico_id else request.user

                # 3. Lectura de cabecera
                cliente_nombre = request.POST.get('cliente_nombre', '').strip() or 'Cliente Mostrador'
                cliente_tel = request.POST.get('cliente_telefono', '').strip() or 'S/N'
                moto_mod = request.POST.get('moto_modelo', '').strip() or 'Motocicleta General'[cite: 4]
                moto_plc = request.POST.get('moto_placa', '').strip().upper() or 'S/CHAPA'
                
                km_raw = request.POST.get('moto_kilometraje')
                moto_km = int(km_raw) if km_raw and km_raw.isdigit() else None

                estado_val = request.POST.get('estado', 'banco')
                fecha_prom = request.POST.get('fecha_promesa') or None
                motivo = request.POST.get('motivo_ingreso', '').strip() or 'Mantenimiento / Servicio'
                obs = request.POST.get('observaciones_vehiculo', '').strip()

                # 4. Crear cabecera de la Orden
                orden = OrdenTrabajo.objects.create(
                    numero_orden=numero_orden,
                    cliente_nombre=cliente_nombre,
                    cliente_telefono=cliente_tel,
                    moto_modelo=moto_mod,
                    moto_placa=moto_plc,
                    moto_kilometraje=moto_km,
                    mecanico=mecanico_obj,
                    estado=estado_val,
                    fecha_promesa=fecha_prom,
                    motivo_ingreso=motivo,
                    observaciones_vehiculo=obs,
                    creado_por=request.user,
                    modificado_por=request.user,
                    total_presupuesto=Decimal('0')
                )

                # 5. Guardar renglones de detalles y descontar stock
                tipos = request.POST.getlist('tipos[]')
                articulos_codigos = request.POST.getlist('articulos[]')
                conceptos = request.POST.getlist('conceptos[]')
                cantidades = request.POST.getlist('cantidades[]')
                precios = request.POST.getlist('precios[]')
                depositos_ids = request.POST.getlist('depositos_item[]')

                total_orden = Decimal('0')
                idx_art = 0
                idx_con = 0

                for i in range(len(tipos)):
                    tipo = tipos[i]
                    cant = Decimal(cantidades[i]) if i < len(cantidades) and cantidades[i] else Decimal('1')
                    precio = Decimal(precios[i]) if i < len(precios) and precios[i] else Decimal('0')
                    subtotal = cant * precio

                    # Depósito del renglón (definido siempre de forma segura)
                    dep_id = depositos_ids[i] if i < len(depositos_ids) and depositos_ids[i] else None
                    deposito_item_obj = Deposito.objects.filter(id=dep_id).first() if dep_id else Deposito.objects.filter(nombre__icontains='taller').first()

                    articulo_obj = None
                    concepto_manual = ''

                    if tipo in ['repuesto', 'producto']:
                        if idx_art < len(articulos_codigos):
                            cod = articulos_codigos[idx_art]
                            articulo_obj = Articulo.objects.filter(codigo=cod).first()
                            idx_art += 1

                        # Descuento en la tabla de Stock
                        if articulo_obj and deposito_item_obj:
                            stk = Stock.objects.filter(articulo=articulo_obj, deposito=deposito_item_obj).first()
                            if stk:
                                stk.cantidad -= cant
                                stk.save()
                    else:
                        if idx_con < len(conceptos):
                            concepto_manual = conceptos[idx_con].strip()
                            idx_con += 1

                    # Creación del detalle con su depósito asignado
                    DetalleOrden.objects.create(
                        orden=orden,
                        tipo=tipo,
                        articulo=articulo_obj,
                        deposito=deposito_item_obj,
                        concepto_manual=concepto_manual,
                        cantidad=cant,
                        precio_unitario=precio,
                        subtotal=subtotal
                    )
                    total_orden += subtotal

                orden.total_presupuesto = total_orden
                orden.save()

                messages.success(request, f"Orden #{orden.numero_orden} registrada con éxito.")
                return redirect('servicios_taller')

        except Exception as e:
            print(f"--> FALLÓ GUARDADO EN TERMINAL: {repr(e)}")
            messages.error(request, f"Error: {e}")

    # ==============================================================
    # PETICIÓN GET (Carga inicial del formulario)
    # ==============================================================
    mecanicos = User.objects.filter(is_active=True).order_by('first_name', 'username')
    articulos_qs = Articulo.objects.filter(activo=True).order_by('nombre')
    depositos = Deposito.objects.filter(activo=True).order_by('nombre')
    clientes_recurrentes = ClienteRecurrente.objects.filter(activo=True).order_by('nombre')

    # Datos serializados para que JavaScript autocomplete teléfono, moto y chapa
    clientes_data = [
        {
            'nombre': c.nombre,
            'telefono': c.telefono or '',
            'moto': c.moto_modelo or '',
            'placa': c.moto_placa or '',
        }
        for c in clientes_recurrentes
    ]

    articulos_data = [
        {
            'codigo': a.codigo,
            'nombre': f"{a.nombre} ({a.presentacion})" if a.presentacion else a.nombre,
            'costo': float(a.costo_referencia or 0)
        }
        for a in articulos_qs
    ]

    context = {
        'es_edicion': False,
        'orden': None,
        'detalles': [],
        'mecanicos': mecanicos,
        'articulos': articulos_qs,
        'articulos_json': articulos_data,
        'depositos': depositos,
        'clientes_recurrentes': clientes_recurrentes,
        'clientes_json': clientes_data,  # <-- Ahora sí llega a la pantalla
    }
    return render(request, 'servicios/orden_crear.html', context)

    # GET
    clientes_recurrentes = ClienteRecurrente.objects.filter(activo=True).order_by('nombre')
    
    clientes_data = [
        {
            'nombre': c.nombre,
            'telefono': c.telefono or '',
            'moto': c.moto_modelo or '',
            'placa': c.moto_placa or '',
        }
        for c in clientes_recurrentes
    ]

    context = {
        'clientes_recurrentes': clientes_recurrentes,
        'clientes_json': clientes_data,
        'mecanicos': mecanicos,
        'articulos': articulos_qs,
        'depositos': depositos,
        'es_edicion': False,
    }
    return render(request, 'servicios/orden_crear.html', context)


@login_required
def orden_editar(request, orden_id):
    """Edición y actualización de Orden de Trabajo."""
    orden = get_object_or_404(
        OrdenTrabajo.objects.select_related('mecanico', 'deposito_origen').prefetch_related('detalles__articulo'),
        id=orden_id
    )

    if request.method == 'POST':
        try:
            with transaction.atomic():
                # 1. Actualizar Depósito Origen
                deposito_id = request.POST.get('deposito_origen')
                orden.deposito_origen = Deposito.objects.filter(id=deposito_id).first() if deposito_id else None

                # 2. Actualizar datos de cabecera
                orden.cliente_nombre = request.POST.get('cliente_nombre', '').strip()
                orden.cliente_telefono = request.POST.get('cliente_telefono', '').strip()
                orden.moto_modelo = request.POST.get('moto_modelo', '').strip()
                orden.moto_placa = request.POST.get('moto_placa', '').strip().upper()
                orden.moto_kilometraje = request.POST.get('moto_kilometraje') or None
                
                mecanico_id = request.POST.get('mecanico')
                if mecanico_id:
                    orden.mecanico = get_object_or_404(User, id=mecanico_id)

                orden.estado = request.POST.get('estado', orden.estado)
                orden.fecha_promesa = request.POST.get('fecha_promesa') or None
                orden.motivo_ingreso = request.POST.get('motivo_ingreso', '').strip()
                orden.observaciones_vehiculo = request.POST.get('observaciones_vehiculo', '').strip()
                orden.modificado_por = request.user

                # 3. Reemplazar renglones de detalles
                orden.detalles.all().delete()

                tipos = request.POST.getlist('tipos[]')
                articulos_codigos = request.POST.getlist('articulos[]')
                conceptos = request.POST.getlist('conceptos[]')
                cantidades = request.POST.getlist('cantidades[]')
                precios = request.POST.getlist('precios[]')
                ivas = request.POST.getlist('ivas[]')

                total_orden = Decimal('0')
                idx_art = 0
                idx_con = 0

                for i in range(len(tipos)):
                    tipo = tipos[i]
                    cant = Decimal(cantidades[i]) if i < len(cantidades) and cantidades[i] else Decimal('1')
                    precio = Decimal(precios[i]) if i < len(precios) and precios[i] else Decimal('0')
                    iva = int(ivas[i]) if i < len(ivas) and ivas[i] else 10
                    subtotal = cant * precio

                    articulo_obj = None
                    concepto_manual = ''

                    if tipo in ['repuesto', 'producto']:
                        if idx_art < len(articulos_codigos):
                            cod = articulos_codigos[idx_art]
                            articulo_obj = Articulo.objects.filter(codigo=cod).first()
                            idx_art += 1
                    else:
                        if idx_con < len(conceptos):
                            concepto_manual = conceptos[idx_con]
                            idx_con += 1

                    DetalleOrden.objects.create(
                        orden=orden,
                        tipo=tipo,
                        articulo=articulo_obj,
                        deposito=deposito_item_obj,
                        concepto_manual=concepto_manual,
                        cantidad=cant,
                        precio_unitario=precio,
                        tipo_iva=iva,
                        subtotal=subtotal
                    )
                    total_orden += subtotal

                orden.total_presupuesto = total_orden
                orden.save()

                messages.success(request, f"Orden #{orden.numero_orden} actualizada correctamente.")
                return redirect('servicios_taller')

        except Exception as e:
            messages.error(request, f"Error al actualizar la orden: {str(e)}")

    # Al final de orden_editar:
    mecanicos = User.objects.filter(is_active=True).order_by('first_name', 'username')
    articulos_qs = Articulo.objects.filter(activo=True).order_by('nombre')
    depositos = Deposito.objects.filter(activo=True).order_by('nombre')

    context = {
        'es_edicion': True,
        'orden': orden,
        'detalles': orden.detalles.all(),
        'mecanicos': mecanicos,
        'articulos': articulos_qs,
        'depositos': depositos,
    }
    return render(request, 'servicios/orden_crear.html', context)

@login_required
def orden_eliminar(request, orden_id):
    """Eliminación de la orden con reposición garantizada de stock a su depósito."""
    orden = get_object_or_404(OrdenTrabajo, id=orden_id)
    deposito_taller = Deposito.objects.filter(nombre__icontains='taller').first()
    
    try:
        with transaction.atomic():
            # 1. Recorrer los ítems y devolver el stock real
            for det in orden.detalles.select_related('articulo', 'deposito').all():
                if det.tipo in ['repuesto', 'producto'] and det.articulo:
                    # Depósito de donde salió ese renglón (o Taller por defecto)
                    dep_destino = det.deposito or deposito_taller
                    
                    if dep_destino:
                        stock_reg, _ = Stock.objects.get_or_create(
                            articulo=det.articulo,
                            deposito=dep_destino,
                            defaults={'cantidad': Decimal('0.00')}
                        )
                        stock_reg.cantidad += det.cantidad
                        stock_reg.save()

            # 2. Eliminar la orden física
            numero = orden.numero_orden
            orden.delete()
            messages.success(request, f"Orden #{numero} eliminada y stock devuelto a inventario.")
            
    except Exception as e:
        messages.error(request, f"Error al eliminar la orden: {str(e)}")

    return redirect('servicios_taller')

@login_required
def detailing_lista(request):
    """Bandeja técnica visual del módulo de Detailing & Estética Vehicular."""
    # Datos estáticos de maqueta para validar la distribución visual
    servicios_mock = [
        {
            'id': 1,
            'numero_ficha': '00001',
            'moto_modelo': 'Ducati Panigale V4',
            'moto_placa': '741-ABC',
            'cliente_nombre': 'Carlos Benítez',
            'tratamiento': 'Cerámico 9H + Corrección de Barniz',
            'etapa': 'ceramico',  # lavado, correccion, ceramico, listo
            'operador': request.user.username,
            'monto': '1.850.000',
            'modificado': False,
        },
        {
            'id': 2,
            'numero_ficha': '00002',
            'moto_modelo': 'BMW R1250 GS',
            'moto_placa': '852-XYZ',
            'cliente_nombre': 'Marcos Vera',
            'tratamiento': 'Lavado Técnico + Descontaminado Férrico',
            'etapa': 'lavado',
            'operador': request.user.username,
            'monto': '350.000',
            'modificado': True,
        },
        {
            'id': 3,
            'numero_ficha': '00003',
            'moto_modelo': 'Yamaha MT-09',
            'moto_placa': '963-DFG',
            'cliente_nombre': 'Rodrigo Duarte',
            'tratamiento': 'Pulido 2 Pasos + Sellado Acrílico',
            'etapa': 'listo',
            'operador': request.user.username,
            'monto': '750.000',
            'modificado': False,
        },
    ]

    context = {
        'servicios': servicios_mock,
        'cant_lavado': 1,
        'cant_correccion': 0,
        'cant_ceramico': 1,
        'cant_listo': 1,
        'cant_total': len(servicios_mock),
    }
    return render(request, 'servicios/detailing_lista.html', context)
from decimal import Decimal
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.db.models import Sum
from django.contrib.auth.models import User
from .models import Proveedor, Deposito, Articulo, Ingreso, DetalleIngreso, Stock, Transferencia, DetalleTransferencia

@login_required
def ingresos_lista(request):
    ingresos = Ingreso.objects.select_related('proveedor', 'deposito_destino', 'creado_por', 'modificado_por').order_by('-id')
    total_mes = ingresos.filter(anulado=False).aggregate(total=Sum('total_general'))['total'] or 0
    total_comprobantes = ingresos.count()

    context = {
        'ingresos': ingresos,
        'total_mes': total_mes,
        'total_comprobantes': total_comprobantes,
    }
    return render(request, 'compras/ingresos_lista.html', context)

@login_required
def ingreso_crear(request):
    if request.method == 'POST':
        with transaction.atomic():
            proveedor_id = request.POST.get('proveedor')
            deposito_id = request.POST.get('deposito')
            tipo_doc = request.POST.get('tipo_documento')
            nro_comp = request.POST.get('numero_comprobante')
            timbrado = request.POST.get('timbrado')
            fecha = request.POST.get('fecha_comprobante')
            recibido_por_id = request.POST.get('recibido_por') or request.user.id
            condicion = request.POST.get('condicion', 'contado')
            metodo_pago = request.POST.get('metodo_pago', 'efectivo')
            moneda = request.POST.get('moneda', 'PYG')
            cotizacion = float(request.POST.get('cotizacion', 1) or 1)
            observaciones = request.POST.get('observaciones', '')
            adjunto = request.FILES.get('comprobante_adjunto')

            deposito = get_object_or_404(Deposito, id=deposito_id)

            ingreso = Ingreso(
                proveedor_id=proveedor_id,
                deposito_destino=deposito,
                tipo_documento=tipo_doc,
                numero_comprobante=nro_comp,
                timbrado=timbrado,
                fecha_comprobante=fecha,
                recibido_por_id=recibido_por_id,
                condicion=condicion,
                metodo_pago=metodo_pago,
                moneda=moneda,
                cotizacion=cotizacion,
                observaciones=observaciones,
                creado_por=request.user,
                total_general=0
            )

            if adjunto:
                ingreso.comprobante_adjunto = adjunto

            ingreso.save()

            articulos_codigos = request.POST.getlist('articulos[]')
            lotes = request.POST.getlist('lotes[]')
            cantidades = request.POST.getlist('cantidades[]')
            costos = request.POST.getlist('costos[]')
            ivas = request.POST.getlist('ivas[]')

            total_acumulado = Decimal('0.00')
            sum_exenta = Decimal('0.00')
            sum_iva5 = Decimal('0.00')
            sum_iva10 = Decimal('0.00')

            for i in range(len(articulos_codigos)):
                codigo = articulos_codigos[i]
                if not codigo:
                    continue

                articulo = Articulo.objects.filter(codigo=codigo).first()
                if not articulo:
                    continue

                cant = Decimal(str(cantidades[i] or 1))
                costo = Decimal(str(costos[i] or 0))
                iva = int(ivas[i] or 10)
                lote = lotes[i] if i < len(lotes) else ''
                subtotal = cant * costo

                total_acumulado += subtotal
                if iva == 0:
                    sum_exenta += subtotal
                elif iva == 5:
                    sum_iva5 += subtotal
                elif iva == 10:
                    sum_iva10 += subtotal

                DetalleIngreso.objects.create(
                    ingreso=ingreso,
                    articulo=articulo,
                    cantidad=cant,
                    costo_unitario=costo,
                    iva_porcentaje=iva,
                    subtotal=subtotal,
                    lote_proveedor=lote
                )

                # IMPACTO REAL EN STOCK DEL DEPÓSITO
                stock_item, _ = Stock.objects.get_or_create(
                    articulo=articulo,
                    deposito=deposito,
                    defaults={'cantidad': Decimal('0.00')}
                )
                stock_item.cantidad += cant
                stock_item.save()

            ingreso.total_exentas = sum_exenta
            ingreso.total_iva5 = sum_iva5
            ingreso.total_iva10 = sum_iva10
            ingreso.liquidacion_iva = round(sum_iva5 / Decimal('21'), 2) + round(sum_iva10 / Decimal('11'), 2)
            ingreso.total_general = total_acumulado
            ingreso.save()

            messages.success(request, f"Ingreso #{ingreso.numero_registro} registrado exitosamente.")
            return redirect('compras_ingresos')

    proveedores = Proveedor.objects.filter(activo=True)
    depositos = Deposito.objects.filter(activo=True)
    articulos_qs = Articulo.objects.filter(activo=True)
    empleados = User.objects.filter(is_active=True).order_by('username')

    articulos_data = [
        {
            'codigo': a.codigo,
            'nombre': f"{a.nombre} ({a.presentacion})" if a.presentacion else a.nombre,
            'costo': float(a.costo_referencia or 0)
        }
        for a in articulos_qs
    ]

    context = {
        'ingreso': None,
        'proveedores': proveedores,
        'depositos': depositos,
        'articulos': articulos_qs,
        'empleados': empleados,
        'articulos_json': articulos_data,
        'es_edicion': False,
    }
    return render(request, 'compras/ingreso_crear.html', context)

@login_required
def ingreso_editar(request, ingreso_id):
    ingreso = get_object_or_404(
        Ingreso.objects.select_related('proveedor', 'deposito_destino').prefetch_related('detalles__articulo'),
        id=ingreso_id
    )

    if request.method == 'POST':
        with transaction.atomic():
            # 1. Restar el stock previo antes de actualizar
            for det in ingreso.detalles.all():
                stock_prev = Stock.objects.filter(articulo=det.articulo, deposito=ingreso.deposito_destino).first()
                if stock_prev:
                    stock_prev.cantidad = max(Decimal('0.00'), stock_prev.cantidad - det.cantidad)
                    stock_prev.save()

            nuevo_deposito_id = request.POST.get('deposito')
            nuevo_deposito = get_object_or_404(Deposito, id=nuevo_deposito_id)

            ingreso.proveedor_id = request.POST.get('proveedor')
            ingreso.deposito_destino = nuevo_deposito
            ingreso.tipo_documento = request.POST.get('tipo_documento')
            ingreso.numero_comprobante = request.POST.get('numero_comprobante')
            ingreso.timbrado = request.POST.get('timbrado')
            ingreso.fecha_comprobante = request.POST.get('fecha_comprobante')
            ingreso.recibido_por_id = request.POST.get('recibido_por') or ingreso.recibido_por_id
            ingreso.condicion = request.POST.get('condicion', 'contado')
            ingreso.metodo_pago = request.POST.get('metodo_pago', 'efectivo')
            ingreso.moneda = request.POST.get('moneda', 'PYG')
            ingreso.cotizacion = float(request.POST.get('cotizacion', 1) or 1)
            ingreso.observaciones = request.POST.get('observaciones', '')
            ingreso.modificado_por = request.user

            if request.FILES.get('comprobante_adjunto'):
                ingreso.comprobante_adjunto = request.FILES.get('comprobante_adjunto')

            ingreso.detalles.all().delete()

            articulos_codigos = request.POST.getlist('articulos[]')
            lotes = request.POST.getlist('lotes[]')
            cantidades = request.POST.getlist('cantidades[]')
            costos = request.POST.getlist('costos[]')
            ivas = request.POST.getlist('ivas[]')

            total_acumulado = Decimal('0.00')
            sum_exenta = Decimal('0.00')
            sum_iva5 = Decimal('0.00')
            sum_iva10 = Decimal('0.00')

            for i in range(len(articulos_codigos)):
                codigo = articulos_codigos[i]
                if not codigo:
                    continue

                articulo = Articulo.objects.filter(codigo=codigo).first()
                if not articulo:
                    continue

                cant = Decimal(str(cantidades[i] or 1))
                costo = Decimal(str(costos[i] or 0))
                iva = int(ivas[i] or 10)
                lote = lotes[i] if i < len(lotes) else ''
                subtotal = cant * costo

                total_acumulado += subtotal
                if iva == 0:
                    sum_exenta += subtotal
                elif iva == 5:
                    sum_iva5 += subtotal
                elif iva == 10:
                    sum_iva10 += subtotal

                DetalleIngreso.objects.create(
                    ingreso=ingreso,
                    articulo=articulo,
                    cantidad=cant,
                    costo_unitario=costo,
                    iva_porcentaje=iva,
                    subtotal=subtotal,
                    lote_proveedor=lote
                )

                # SUMAR STOCK ACTUALIZADO
                stock_item, _ = Stock.objects.get_or_create(
                    articulo=articulo,
                    deposito=nuevo_deposito,
                    defaults={'cantidad': Decimal('0.00')}
                )
                stock_item.cantidad += cant
                stock_item.save()

            ingreso.total_exentas = sum_exenta
            ingreso.total_iva5 = sum_iva5
            ingreso.total_iva10 = sum_iva10
            ingreso.liquidacion_iva = round(sum_iva5 / Decimal('21'), 2) + round(sum_iva10 / Decimal('11'), 2)
            ingreso.total_general = total_acumulado
            ingreso.save()

            messages.success(request, f"Ingreso #{ingreso.numero_registro} actualizado exitosamente.")
            return redirect('compras_ingresos')

    proveedores = Proveedor.objects.filter(activo=True)
    depositos = Deposito.objects.filter(activo=True)
    articulos_qs = Articulo.objects.filter(activo=True)
    empleados = User.objects.filter(is_active=True).order_by('username')

    articulos_data = [
        {
            'codigo': a.codigo,
            'nombre': f"{a.nombre} ({a.presentacion})" if a.presentacion else a.nombre,
            'costo': float(a.costo_referencia or 0)
        }
        for a in articulos_qs
    ]

    context = {
        'ingreso': ingreso,
        'detalles': ingreso.detalles.all(),
        'proveedores': proveedores,
        'depositos': depositos,
        'articulos': articulos_qs,
        'empleados': empleados,
        'articulos_json': articulos_data,
        'es_edicion': True,
    }
    return render(request, 'compras/ingreso_crear.html', context)

@login_required
def ingreso_eliminar(request, ingreso_id):
    ingreso = get_object_or_404(Ingreso, id=ingreso_id)
    nro = ingreso.numero_registro

    with transaction.atomic():
        # Restar el stock antes de eliminar la compra
        for det in ingreso.detalles.all():
            stock = Stock.objects.filter(articulo=det.articulo, deposito=ingreso.deposito_destino).first()
            if stock:
                stock.cantidad = max(Decimal('0.00'), stock.cantidad - det.cantidad)
                stock.save()
        ingreso.delete()

    messages.success(request, f"Ingreso #{nro} eliminado exitosamente.")
    return redirect('compras_ingresos')

@login_required
def inventario_lista(request):
    depositos = Deposito.objects.filter(activo=True).order_by('nombre')
    
    depositos_data = []
    for dep in depositos:
        # Trae solo los artículos que tienen stock registrado (> 0) en este depósito
        stock_qs = Stock.objects.filter(deposito=dep, cantidad__gt=0).select_related('articulo').order_by('articulo__nombre')
        
        items_deposito = []
        for s in stock_qs:
            items_deposito.append({
                'codigo': s.articulo.codigo,
                'nombre': s.articulo.nombre,
                'presentacion': s.articulo.presentacion,
                'costo_referencia': s.articulo.costo_referencia,
                'cantidad': s.cantidad,
            })
            
        depositos_data.append({
            'deposito': dep,
            'items': items_deposito,
            'total_items': len(items_deposito),
        })

    total_articulos = Articulo.objects.filter(activo=True).count()
    unidades_totales = Stock.objects.aggregate(total=Sum('cantidad'))['total'] or 0

    context = {
        'depositos_data': depositos_data,
        'total_items': total_articulos,
        'unidades_totales': unidades_totales,
    }
    return render(request, 'compras/inventario_lista.html', context)

@login_required
def transferencias_lista(request):
    """Consola unificada: Formulario de traslado arriba + Historial auditable abajo."""
    if request.method == 'POST':
        try:
            with transaction.atomic():
                origen_id = request.POST.get('deposito_origen')
                destino_id = request.POST.get('deposito_destino')
                fecha_op = request.POST.get('fecha')
                observaciones = request.POST.get('observaciones', '').strip()

                if not origen_id or not destino_id:
                    messages.error(request, "Debe seleccionar un depósito de origen y uno de destino.")
                    return redirect('compras_transferencias')

                if origen_id == destino_id:
                    messages.error(request, "El depósito de origen y destino no pueden ser iguales.")
                    return redirect('compras_transferencias')

                origen = get_object_or_404(Deposito, id=origen_id)
                destino = get_object_or_404(Deposito, id=destino_id)

                articulos_ids = request.POST.getlist('articulos[]')
                cantidades = request.POST.getlist('cantidades[]')

                # Correlativo automático (#TR-00001)
                total_trf = Transferencia.objects.count() + 1
                numero_trf = f"TR-{total_trf:05d}"
                while Transferencia.objects.filter(numero_transferencia=numero_trf).exists():
                    total_trf += 1
                    numero_trf = f"TR-{total_trf:05d}"

                transferencia = Transferencia.objects.create(
                    numero_transferencia=numero_trf,
                    deposito_origen=origen,
                    deposito_destino=destino,
                    fecha=fecha_op,
                    observaciones=observaciones,
                    creado_por=request.user
                )

                items_procesados = 0
                for art_ref, cant_str in zip(articulos_ids, cantidades):
                    if not art_ref or not str(art_ref).strip():
                        continue
                    if not cant_str or not str(cant_str).strip():
                        continue

                    try:
                        cant = Decimal(str(cant_str).strip())
                    except Exception:
                        continue

                    if cant <= 0:
                        continue

                    # Búsqueda segura sin romper con DoesNotExist
                    art_ref_clean = str(art_ref).strip()
                    articulo = None
                    if art_ref_clean.isdigit():
                        articulo = Articulo.objects.filter(id=int(art_ref_clean)).first()
                    if not articulo:
                        articulo = Articulo.objects.filter(codigo=art_ref_clean).first()
                    if not articulo:
                        articulo = Articulo.objects.filter(codigo__iexact=art_ref_clean).first()

                    if not articulo:
                        continue

                    # Control estricto de existencia en depósito origen
                    stock_origen, _ = Stock.objects.get_or_create(
                        articulo=articulo,
                        deposito=origen,
                        defaults={'cantidad': Decimal('0.00')}
                    )

                    if stock_origen.cantidad < cant:
                        raise ValueError(
                            f"Stock insuficiente: '{articulo.nombre}' solo dispone de {stock_origen.cantidad:.0f} un. "
                            f"en '{origen.nombre}' (intentaste transferir {cant:.0f})."
                        )

                    # Descontar de origen y sumar a destino
                    stock_origen.cantidad -= cant
                    stock_origen.save()

                    stock_destino, _ = Stock.objects.get_or_create(
                        articulo=articulo,
                        deposito=destino,
                        defaults={'cantidad': Decimal('0.00')}
                    )
                    stock_destino.cantidad += cant
                    stock_destino.save()

                    DetalleTransferencia.objects.create(
                        transferencia=transferencia,
                        articulo=articulo,
                        cantidad=cant
                    )
                    items_procesados += 1

                if items_procesados == 0:
                    raise ValueError("No se seleccionó ningún artículo válido con cantidad mayor a 0.")

                messages.success(request, f"Transferencia #{numero_trf} confirmada con éxito.")
                return redirect('compras_transferencias')

        except Exception as e:
            messages.error(request, str(e))
            return redirect('compras_transferencias')

    # GET: Manejo de navegación entre transferencias
    transferencias = Transferencia.objects.select_related(
        'deposito_origen', 'deposito_destino', 'creado_por'
    ).prefetch_related('detalles__articulo').order_by('-fecha', '-id')

    ver_id = request.GET.get('id')
    transferencia_actual = None
    tr_anterior_id = None
    tr_siguiente_id = None

    lista_ids = list(transferencias.values_list('id', flat=True))

    if ver_id and ver_id.isdigit():
        ver_id_int = int(ver_id)
        transferencia_actual = transferencias.filter(id=ver_id_int).first()
        if transferencia_actual and ver_id_int in lista_ids:
            idx = lista_ids.index(ver_id_int)
            # Anterior en el tiempo (hacia atrás en la lista)
            if idx + 1 < len(lista_ids):
                tr_anterior_id = lista_ids[idx + 1]
            # Siguiente en el tiempo (hacia lo más nuevo)
            if idx > 0:
                tr_siguiente_id = lista_ids[idx - 1]
    else:
        # Si estamos en modo "Nuevo", la flecha izquierda lleva a la última creada
        if lista_ids:
            tr_anterior_id = lista_ids[0]

    depositos = Deposito.objects.filter(activo=True).order_by('nombre')
    articulos = Articulo.objects.filter(activo=True).order_by('nombre')

    context = {
        'transferencias': transferencias,
        'depositos': depositos,
        'articulos': articulos,
        'tr_actual': transferencia_actual,
        'tr_anterior_id': tr_anterior_id,
        'tr_siguiente_id': tr_siguiente_id,
    }
    return render(request, 'compras/transferencias_lista.html', context)

@login_required
def transferencia_detalle(request, transferencia_id):
    """Comprobante y nota de remisión imprimible de un traslado."""
    transferencia = get_object_or_404(
        Transferencia.objects.select_related('deposito_origen', 'deposito_destino', 'creado_por')
                             .prefetch_related('detalles__articulo'),
        id=transferencia_id
    )
    return render(request, 'compras/transferencia_detalle.html', {'transferencia': transferencia})

@login_required
def transferencia_eliminar(request, transferencia_id):
    """Elimina un traslado y revierte el stock: devuelve a origen y resta de destino."""
    transferencia = get_object_or_404(Transferencia, id=transferencia_id)
    nro = transferencia.numero_transferencia
    origen = transferencia.deposito_origen
    destino = transferencia.deposito_destino

    try:
        with transaction.atomic():
            for det in transferencia.detalles.select_related('articulo').all():
                art = det.articulo
                cant = det.cantidad

                # 1. Verificar si destino tiene suficiente stock para revertir
                stock_destino = Stock.objects.filter(articulo=art, deposito=destino).first()
                if not stock_destino or stock_destino.cantidad < cant:
                    disponible = stock_destino.cantidad if stock_destino else 0
                    raise ValueError(
                        f"No se puede revertir: '{art.nombre}' ya no tiene {cant:.0f} un. "
                        f"en {destino.nombre} (disponible: {disponible:.0f})."
                    )

                # 2. Restar del destino
                stock_destino.cantidad -= cant
                stock_destino.save()

                # 3. Sumar de vuelta al origen
                stock_origen, _ = Stock.objects.get_or_create(
                    articulo=art, 
                    deposito=origen, 
                    defaults={'cantidad': Decimal('0.00')}
                )
                stock_origen.cantidad += cant
                stock_origen.save()

            # 4. Borrar la transferencia física (sus detalles se eliminan en cascada)
            transferencia.delete()
            messages.success(request, f"Transferencia #{nro} eliminada y stock restituido a {origen.nombre}.")

    except Exception as e:
        messages.error(request, f"Error al revertir traslado: {str(e)}")

    return redirect('compras_transferencias')

@login_required
def reembolsos_lista(request):
    """Bandeja técnica y registro de reposiciones por garantía o cambios."""
    depositos = Deposito.objects.filter(activo=True).order_by('nombre')
    articulos = Articulo.objects.filter(activo=True).order_by('nombre')
    
    context = {
        'depositos': depositos,
        'articulos': articulos,
    }
    return render(request, 'compras/reembolsos_lista.html', context)

@login_required
def historial_kardex(request):
    """Vista inicial para el botón Historial."""
    return render(request, 'compras/historial_kardex.html')

from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def presupuestos_lista(request):
    """Bandeja técnica y registro de presupuestos / cotizaciones a clientes."""
    presupuestos_mock = [
        {
            'id': 1,
            'numero': '00001',
            'cliente': 'Esteban González',
            'documento': '4.120.350-1',
            'fecha': '01 Oct 2026',
            'validez': '15 Oct 2026',
            'items_resumen': '2x Aceite Motul 7100 + Filtro Yamaha MT09',
            'total': '320.000',
            'estado': 'pendiente',  # pendiente, aprobado, vencido
            'operador': request.user.username,
        },
        {
            'id': 2,
            'numero': '00002',
            'cliente': 'Moto Club Asunción (Guillermo)',
            'documento': '80054210-9',
            'fecha': '28 Sep 2026',
            'validez': '05 Oct 2026',
            'items_resumen': 'Kit Transmisión D.I.D + Pastillas Traseras Brembo',
            'total': '890.000',
            'estado': 'aprobado',
            'operador': request.user.username,
        },
        {
            'id': 3,
            'numero': '00003',
            'cliente': 'Fernando Silva',
            'documento': '3.890.112',
            'fecha': '20 Sep 2026',
            'validez': '27 Sep 2026',
            'items_resumen': 'Cubierta Michelin Road 5 + Válvulas aluminio',
            'total': '1.450.000',
            'estado': 'vencido',
            'operador': request.user.username,
        },
    ]

    context = {
        'presupuestos': presupuestos_mock,
        'cant_pendientes': 1,
        'cant_aprobados': 1,
        'cant_vencidos': 1,
        'cant_total': len(presupuestos_mock),
    }
    return render(request, 'ventas/presupuestos_lista.html', context)

@login_required
def facturas_lista(request):
    """Bandeja técnica visual del módulo de Ventas y Facturación Fiscal / Mostrador."""
    facturas_mock = [
        {
            'id': 1,
            'numero_factura': '001-002-0000104',
            'timbrado': '16482930',
            'cliente_nombre': 'Carlos Benítez',
            'cliente_ruc': '4.120.350-1',
            'fecha': '01 Oct 2026',
            'condicion': 'contado',  # contado, credito
            'metodo_pago': 'Efectivo',
            'origen': 'Mostrador',  # Mostrador, Taller, Presupuesto
            'total_general': '1.850.000',
            'estado': 'cobrado',  # cobrado, pendiente, anulado
            'operador': request.user.username,
        },
        {
            'id': 2,
            'numero_factura': '001-002-0000105',
            'timbrado': '16482930',
            'cliente_nombre': 'Transportes del Sur S.A.',
            'cliente_ruc': '80054210-9',
            'fecha': '01 Oct 2026',
            'condicion': 'credito',
            'metodo_pago': 'Transferencia (30d)',
            'origen': 'Presupuesto #PR-00002',
            'total_general': '890.000',
            'estado': 'pendiente',
            'operador': request.user.username,
        },
        {
            'id': 3,
            'numero_factura': '001-002-0000106',
            'timbrado': '16482930',
            'cliente_nombre': 'Fernando Silva',
            'cliente_ruc': '3.890.112',
            'fecha': '02 Oct 2026',
            'condicion': 'contado',
            'metodo_pago': 'Tarjeta',
            'origen': 'Orden de Taller #OT-00003',
            'total_general': '350.000',
            'estado': 'cobrado',
            'operador': request.user.username,
        },
    ]

    context = {
        'facturas': facturas_mock,
        'total_facturado_mes': '3.090.000',
        'cant_cobradas': 2,
        'cant_pendientes_cobro': 1,
        'cant_total': len(facturas_mock),
    }
    return render(request, 'ventas/facturas_lista.html', context)

@login_required
def remisiones_lista(request):
    """Bandeja técnica visual del módulo de Remisiones de Salida / Entrega a Clientes."""
    remisiones_mock = [
        {
            'id': 1,
            'numero_remision': '001-001-000042',
            'timbrado': '16482930',
            'cliente': 'Moto Club Asunción (Guillermo)',
            'documento': '80054210-9',
            'factura_asociada': '001-002-0000105',
            'fecha_traslado': '02 Oct 2026',
            'chofer_transporte': 'Juan Rojas (Furgón RFA-1)',
            'destino_entrega': 'Sede Club - Av. Mariscal López',
            'cant_bultos': 3,
            'estado': 'en_transito',  # en_transito, entregado, anulado
            'operador': request.user.username,
        },
        {
            'id': 2,
            'numero_remision': '001-001-000041',
            'timbrado': '16482930',
            'cliente': 'Carlos Benítez',
            'documento': '4.120.350-1',
            'factura_asociada': '001-002-0000104',
            'fecha_traslado': '01 Oct 2026',
            'chofer_transporte': 'Retiro en Local / Cliente',
            'destino_entrega': 'Entrega en mostrador central',
            'cant_bultos': 1,
            'estado': 'entregado',
            'operador': request.user.username,
        },
    ]

    context = {
        'remisiones': remisiones_mock,
        'cant_en_transito': 1,
        'cant_entregadas': 1,
        'cant_total': len(remisiones_mock),
    }
    return render(request, 'ventas/remisiones_lista.html', context)
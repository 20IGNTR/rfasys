from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from .models import NotaTurno

def inicio(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        action = request.POST.get('action', 'login')

        if action == 'login':
            usuario = request.POST.get('usuario')
            password = request.POST.get('password')
            user = authenticate(request, username=usuario, password=password)

            if user is not None:
                login(request, user)
                return redirect('dashboard')
            else:
                messages.error(request, 'Usuario o contraseña incorrectos')
                return redirect('inicio')

        elif action == 'change_password':
            usuario = request.POST.get('usuario')
            current_pass = request.POST.get('current_password')
            new_pass = request.POST.get('new_password')
            confirm_pass = request.POST.get('confirm_password')

            # 1. Validar coincidencia de nueva clave
            if new_pass != confirm_pass:
                messages.error(request, 'Las nuevas contraseñas no coinciden')
                return redirect('inicio')

            # 2. Validar que la contraseña actual sea verídica
            user = authenticate(request, username=usuario, password=current_pass)
            if user is not None:
                user.set_password(new_pass)
                user.save()
                messages.success(request, 'Contraseña actualizada. Inicia sesión.')
                return redirect('inicio')
            else:
                messages.error(request, 'Usuario o contraseña actual incorrectos')
                return redirect('inicio')

    return render(request, 'home/inicio.html')

@login_required(login_url='inicio')
def dashboard(request):
    if request.method == 'POST':
        # 1. Crear nueva nota
        if 'crear_nota' in request.POST:
            mensaje = request.POST.get('mensaje', '').strip()
            prioridad = request.POST.get('prioridad', 'normal')
            if mensaje:
                NotaTurno.objects.create(
                    autor=request.user,
                    mensaje=mensaje,
                    prioridad=prioridad
                )
            return redirect('dashboard')

        # 2. Editar nota existente
        elif 'editar_nota' in request.POST:
            nota_id = request.POST.get('nota_id')
            nota = get_object_or_404(NotaTurno, id=nota_id)
            nuevo_mensaje = request.POST.get('mensaje', '').strip()
            nueva_prioridad = request.POST.get('prioridad', 'normal')
            if nuevo_mensaje:
                nota.mensaje = nuevo_mensaje
                nota.prioridad = nueva_prioridad
                nota.save()
            return redirect('dashboard')

    # Solo las notas activas se muestran en el dashboard
    notas_turno = NotaTurno.objects.filter(activa=True)[:3]
    todas_las_notas = NotaTurno.objects.all()[:50]  # Para el modal de historial

    context = {
        'notas_turno': notas_turno,
        'todas_las_notas': todas_las_notas,
    }
    return render(request, 'home/dashboard.html', context)


@login_required(login_url='inicio')
def nota_eliminar(request, nota_id):
    """Borrado lógico: se desactiva del dashboard pero se conserva en Django Admin."""
    nota = get_object_or_404(NotaTurno, id=nota_id)
    nota.activa = False  # Permanece guardada en la base de datos
    nota.save()
    return redirect('dashboard')

def cerrar_sesion(request):
    logout(request)
    return redirect('inicio')
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def ads_proveedores(request):
    """Directorio y gestión de proveedores comerciales."""
    proveedores_mock = [
        {
            'id': 1,
            'razon_social': 'Motul Paraguay S.A.',
            'ruc': '80023456-1',
            'contacto': 'Rodrigo Morales',
            'telefono': '0981 123 456',
            'rubro': 'Lubricantes & Químicos',
            'estado': 'activo',
            'credito_dias': 30,
        },
        {
            'id': 2,
            'razon_social': 'Chacomer Automotores S.A.',
            'ruc': '80001290-4',
            'contacto': 'Laura Gómez',
            'telefono': '021 518 000',
            'rubro': 'Repuestos & Transmisión',
            'estado': 'activo',
            'credito_dias': 45,
        },
        {
            'id': 3,
            'razon_social': 'Brembo Racing Importadora',
            'ruc': '80112345-8',
            'contacto': 'Esteban Galeano',
            'telefono': '0971 998 877',
            'rubro': 'Frenos & Competición',
            'estado': 'inactivo',
            'credito_dias': 0,
        },
    ]
    context = {
        'proveedores': proveedores_mock,
        'cant_activos': 2,
        'cant_inactivos': 1,
        'cant_total': len(proveedores_mock),
    }
    return render(request, 'home/ads_proveedores.html', context)


@login_required
def ads_clientes(request):
    """Directorio general de clientes y fichas de vehículos."""
    clientes_mock = [
        {
            'id': 1,
            'nombre_completo': 'Carlos Benítez',
            'documento': '4.120.350-1',
            'telefono': '0982 555 111',
            'moto_principal': 'Ducati Panigale V4 (741-ABC)',
            'tipo_cliente': 'Particular / Taller',
            'saldo_cuenta': '0',
            'estado': 'al_dia',
        },
        {
            'id': 2,
            'nombre_completo': 'Moto Club Asunción (Guillermo)',
            'documento': '80054210-9',
            'telefono': '0981 888 222',
            'moto_principal': 'Flota (8 Unidades)',
            'tipo_cliente': 'Corporativo / Club',
            'saldo_cuenta': '890.000',
            'estado': 'credito_pendiente',
        },
        {
            'id': 3,
            'nombre_completo': 'Fernando Silva',
            'documento': '3.890.112',
            'telefono': '0971 333 444',
            'moto_principal': 'Yamaha MT-09 (963-DFG)',
            'tipo_cliente': 'Particular / Detailing',
            'saldo_cuenta': '0',
            'estado': 'al_dia',
        },
    ]
    context = {
        'clientes': clientes_mock,
        'cant_al_dia': 2,
        'cant_con_saldo': 1,
        'cant_total': len(clientes_mock),
    }
    return render(request, 'home/ads_clientes.html', context)
@login_required
def ads_empleados(request):
    """Directorio maestro de empleados, cargos y liquidación de salarios."""
    empleados_mock = [
        {
            'id': 1,
            'nombre_completo': 'Juan Ignacio Torres',
            'documento': '4.850.120',
            'cargo': 'Encargado de Taller / Mecánico',
            'departamento': 'Servicios',
            'telefono': '0981 123 456',
            'fecha_ingreso': '15 Ene 2024',
            'salario_base': '3.800.000',
            'ips_inscripto': True,
            'estado': 'activo',
            'usuario_sistema': request.user.username,
        },
        {
            'id': 2,
            'nombre_completo': 'Carlos Benítez',
            'documento': '3.940.852',
            'cargo': 'Mecánico Especialista',
            'departamento': 'Servicios',
            'telefono': '0971 654 321',
            'fecha_ingreso': '01 Mar 2025',
            'salario_base': '3.200.000',
            'ips_inscripto': True,
            'estado': 'activo',
            'usuario_sistema': 'cbenitez',
        },
        {
            'id': 3,
            'nombre_completo': 'María Sol Galeano',
            'documento': '5.120.330',
            'cargo': 'Atención al Cliente & Facturación',
            'departamento': 'Ventas / Mostrador',
            'telefono': '0982 999 888',
            'fecha_ingreso': '10 Jun 2025',
            'salario_base': '2.900.000',
            'ips_inscripto': True,
            'estado': 'activo',
            'usuario_sistema': 'mgaleano',
        },
    ]

    context = {
        'empleados': empleados_mock,
        'cant_activos': 3,
        'total_planilla_mensual': '9.900.000',
        'cant_total': len(empleados_mock),
    }
    return render(request, 'home/ads_empleados.html', context)
from django.contrib import admin
from django.urls import path, include
from django.conf import settings  # <--- ESTA ES LA LÍNEA QUE FALTA

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('home.urls')),
    path('compras/', include('compras.urls')),
    path('servicios/', include('servicios.urls')),
    path('ventas/', include('ventas.urls')),
]
# Si está corriendo en PythonAnywhere, inyecta la ruta de Baton al inicio
if getattr(settings, 'EN_PRODUCCION', False):
    urlpatterns.insert(0, path('baton/', include('baton.urls')))
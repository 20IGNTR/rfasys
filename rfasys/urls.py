from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('home.urls')),
    path('compras/', include('compras.urls')),
    path('servicios/', include('servicios.urls')),
    path('ventas/', include('ventas.urls')),
]
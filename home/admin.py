from django.contrib import admin
from .models import NotaTurno

@admin.register(NotaTurno)
class NotaTurnoAdmin(admin.ModelAdmin):
    list_display = ('id', 'autor', 'mensaje', 'prioridad', 'activa', 'fecha_creacion')
    list_filter = ('activa', 'prioridad', 'fecha_creacion')  # Filtra activas vs descartadas
    search_fields = ('mensaje', 'autor__username')
    ordering = ('-fecha_creacion',)
    list_editable = ('activa',)  # Puedes reactivarlas con un clic desde el Admin
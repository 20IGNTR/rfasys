from django.db import models
from django.contrib.auth.models import User

class NotaTurno(models.Model):
    PRIORIDAD_CHOICES = [
        ('normal', 'Normal'),
        ('urgente', 'Urgente'),
        ('info', 'Informativo'),
    ]

    autor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notas_turno')
    mensaje = models.CharField(max_length=250)
    prioridad = models.CharField(max_length=15, choices=PRIORIDAD_CHOICES, default='normal')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    activa = models.BooleanField(default=True)

    class Meta:
        ordering = ['-fecha_creacion']
        verbose_name = 'Nota de Turno'
        verbose_name_plural = 'Notas de Turno'

    def __str__(self):
        return f"@{self.autor.username}: {self.mensaje[:30]}"
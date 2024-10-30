# Generated by Django 5.0.7 on 2024-10-26 14:46

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Foto',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('titulo', models.CharField(max_length=255, verbose_name='Título')),
                ('imagen', models.ImageField(upload_to='fotos/', verbose_name='Imagen')),
                ('descripcion', models.TextField(blank=True, verbose_name='Descripción')),
                ('fecha_subida', models.DateTimeField(default=django.utils.timezone.now, verbose_name='Fecha de subida')),
                ('camara', models.CharField(blank=True, max_length=100, verbose_name='Cámara')),
                ('lente', models.CharField(blank=True, max_length=100, verbose_name='Lente')),
                ('configuracion', models.CharField(blank=True, max_length=255, verbose_name='Configuración')),
                ('usuario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='fotos', to=settings.AUTH_USER_MODEL, verbose_name='Usuario')),
            ],
        ),
    ]
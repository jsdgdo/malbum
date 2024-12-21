# Generated by Django 5.0.7 on 2024-12-21 19:33

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('malbum', '0004_alter_foto_licencia'),
    ]

    operations = [
        migrations.CreateModel(
            name='SolicitudImagen',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email_solicitante', models.EmailField(max_length=254, verbose_name='Email del solicitante')),
                ('mensaje', models.TextField(verbose_name='Mensaje')),
                ('fecha_solicitud', models.DateTimeField(auto_now_add=True)),
                ('estado', models.CharField(choices=[('pendiente', 'Pendiente'), ('aprobada', 'Aprobada'), ('rechazada', 'Rechazada')], default='pendiente', max_length=20)),
                ('url_descarga', models.CharField(blank=True, max_length=255, null=True)),
                ('fecha_respuesta', models.DateTimeField(blank=True, null=True)),
                ('foto', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='solicitudes', to='malbum.foto')),
            ],
            options={
                'verbose_name': 'Solicitud de imagen',
                'verbose_name_plural': 'Solicitudes de imágenes',
                'ordering': ['-fecha_solicitud'],
            },
        ),
    ]

# Generated by Django 5.0.7 on 2024-11-18 00:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('malbum', '0003_etiqueta_coleccion_foto_colecciones_foto_etiquetas'),
    ]

    operations = [
        migrations.AlterField(
            model_name='foto',
            name='licencia',
            field=models.CharField(blank=True, help_text='Detalles sobre la licencia de imagen (ej. Creative Commons, Copyright, etc.)', max_length=255, verbose_name='Licencia'),
        ),
    ]

# Generated by Django 5.0.7 on 2024-12-29 23:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('usuario', '0005_follow'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='follow',
            unique_together={('following', 'actor_url')},
        ),
        migrations.AddField(
            model_name='follow',
            name='remote_domain',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='follow',
            name='remote_username',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.RemoveField(
            model_name='follow',
            name='follower',
        ),
    ]
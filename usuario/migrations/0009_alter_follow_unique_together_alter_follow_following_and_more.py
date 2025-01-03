# Generated by Django 5.0.7 on 2025-01-03 21:35

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('usuario', '0008_alter_follow_follower_alter_follow_remote_domain_and_more'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='follow',
            unique_together={('follower', 'following')},
        ),
        migrations.AlterField(
            model_name='follow',
            name='following',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='followers_set', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterUniqueTogether(
            name='follow',
            unique_together={('follower', 'actor_url'), ('follower', 'following')},
        ),
    ]

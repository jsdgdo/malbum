from django.contrib.auth.models import AbstractUser
from django.db import models

class Usuario(AbstractUser):
  nombreCompleto = models.CharField(max_length=255)
  fotoDePerfil = models.ImageField(upload_to='profile_pics', null=True, blank=True)

  groups = models.ManyToManyField(
    'auth.Group',
    related_name='usuario_set',
    blank=True,
    help_text=('The groups this user belongs to. A user will get all premissions granted to each of their groups'),
    verbose_name=('groups'),
  )
  user_permissions = models.ManyToManyField(
    'auth.Permission',
    related_name='usuario_set',
    blank=True,
    help_text=('Specific permissions for this user.'),
    verbose_name=('user permissions')
  )

  def __str__(self):
    return self.username
  
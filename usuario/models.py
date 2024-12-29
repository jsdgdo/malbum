from django.contrib.auth.models import AbstractUser
from django.db import models
from django.urls import reverse
from malbum.config import get_config

class Usuario(AbstractUser):
  nombreCompleto = models.CharField(max_length=255)
  fotoDePerfil = models.ImageField(upload_to='profile_pics', null=True, blank=True)
  bio = models.TextField(null=True, blank=True, verbose_name="Biografía")
  email = models.EmailField(unique=True, verbose_name="Correo Electrónico")
  activitypub_id = models.URLField(
    unique=True, blank=True,
    help_text="The unique ID for ActivityPub federation."
  )

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

  def save(self, *args, **kwargs):
    if not self.activitypub_id:
        self.activitypub_id = self.get_activitypub_id()
    super().save(*args, **kwargs)

  def get_actor(self):
    config = get_config()
    domain = self.get_domain()
    
    return {
        "@context": [
            "https://www.w3.org/ns/activitystreams",
            "https://w3id.org/security/v1"
        ],
        "id": self.activitypub_id,
        "type": "Person",
        "name": self.username,
        "preferredUsername": self.username,
        "inbox": f"https://{domain}/ap/users/{self.username}/inbox",
        "outbox": f"https://{domain}/ap/users/{self.username}/outbox",
        "followers": f"https://{domain}/ap/users/{self.username}/followers",
        "following": f"https://{domain}/ap/users/{self.username}/following",
        "publicKey": {
            "id": f"https://{domain}/ap/users/{self.username}#main-key",
            "owner": self.activitypub_id,
            "publicKeyPem": config.get('PUBLIC_KEY', '')
        }
    }

  def get_domain(self):
    from django.conf import settings
    return settings.ALLOWED_HOSTS[0] if settings.ALLOWED_HOSTS else 'localhost'

  def get_activitypub_id(self):
    """Return the user's ActivityPub ID"""
    domain = self.get_domain()
    return f"https://{domain}/ap/users/{self.username}"

  def get_profile_pic_url(self):
    """Get the URL for the user's profile picture"""
    if self.fotoDePerfil:
        return self.fotoDePerfil.url
    return '/static/default-profile.jpg'  # You might want to add a default profile image

  def __str__(self):
    return self.username
  
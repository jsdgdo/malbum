from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

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
        self.activitypub_id = f"https://{self.username}.example.com/ap/actor"
    super().save(*args, **kwargs)

  def get_actor(self):
    return {
        "@context": "https://www.w3.org/ns/activitystreams",
        "id": self.activitypub_id,
        "type": "Person",
        "name": self.username,
        "preferredUsername": self.username,
        "inbox": f"https://{self.username}.example.com/ap/inbox",
        "outbox": f"https://{self.username}.example.com/ap/outbox",
        "followers": f"https://{self.username}.example.com/ap/followers",
        "following": f"https://{self.username}.example.com/ap/following",
        "publicKey": {
            "id": f"https://{self.username}.example.com/ap/actor#main-key",
            "owner": self.activitypub_id,
            "publicKeyPem": "TODO: Add Public Key",
        },
    }

  def __str__(self):
    return self.username
  
class Follow(models.Model):
    follower = models.ForeignKey(Usuario, related_name='following', on_delete=models.CASCADE)
    following = models.ForeignKey(Usuario, related_name='followers', on_delete=models.CASCADE)
    actor_url = models.URLField(max_length=500)
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        unique_together = ('follower', 'following')
  
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
import requests
from tempfile import NamedTemporaryFile
from django.core.files import File
from urllib.parse import urlparse
import os

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

  # Add related_name for reverse relationship
  following = models.ManyToManyField(
    'self',
    through='Follow',
    through_fields=('follower', 'following'),
    symmetrical=False,
    related_name='followers'
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
  
def get_default_user():
    from django.contrib.auth import get_user_model
    User = get_user_model()
    # Get or create a system user
    user, _ = User.objects.get_or_create(
        username='system',
        defaults={
            'email': 'system@localhost',
            'is_active': False,
            'nombreCompleto': 'System User'
        }
    )
    return user.id

class Follow(models.Model):
    follower = models.ForeignKey(
        Usuario, 
        on_delete=models.CASCADE, 
        related_name='following_set'
    )
    following = models.ForeignKey(
        Usuario, 
        on_delete=models.CASCADE, 
        related_name='followers_set',
        null=True,
        blank=True
    )
    actor_url = models.URLField()
    remote_username = models.CharField(max_length=255)
    remote_domain = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [
            ('follower', 'following'),
            ('follower', 'actor_url')
        ]
        
    def __str__(self):
        if self.following:
            return f"{self.follower} follows {self.following}"
        return f"{self.follower} follows {self.remote_username}@{self.remote_domain}"
  
class RemotePost(models.Model):
    remote_id = models.CharField(max_length=500, unique=True)
    actor_url = models.CharField(max_length=500)
    content = models.TextField(blank=True)
    image_url = models.URLField(max_length=500)
    local_image = models.ImageField(upload_to='remote_images/', null=True, blank=True)
    published = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(default=timezone.now)
    
    def download_image(self):
        """Download the remote image if we don't have it locally"""
        if self.image_url and not self.local_image:
            try:
                response = requests.get(self.image_url, stream=True)
                if response.status_code == 200:
                    # Get the filename from the URL
                    file_name = os.path.basename(urlparse(self.image_url).path)
                    if not file_name:
                        file_name = f"remote_image_{self.id}.jpg"
                        
                    # Create a temporary file
                    img_temp = NamedTemporaryFile(delete=True)
                    img_temp.write(response.content)
                    img_temp.flush()
                    
                    # Save the image
                    self.local_image.save(file_name, File(img_temp), save=True)
            except Exception as e:
                print(f"Error downloading image: {e}")
    
    def save(self, *args, **kwargs):
        if self._state.adding:
            self.created_at = timezone.now()
        super().save(*args, **kwargs)
        if self._state.adding:
            self.download_image()
  
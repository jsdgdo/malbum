from django.core.management.base import BaseCommand
from usuario.activitypub import sync_remote_posts

class Command(BaseCommand):
    help = 'Sync posts from remote users we follow'

    def handle(self, *args, **options):
        self.stdout.write("Starting remote post sync...")
        sync_remote_posts()
        self.stdout.write(self.style.SUCCESS('Successfully synced remote posts')) 
from django.apps import AppConfig
from django.db.models.signals import post_migrate

def populate_data(sender, **kwargs):
    """
    Populates the database with sample data if it's empty.
    """
    from django.core.management import call_command
    from .models import DebateCategory
    
    # Check if any categories already exist
    if not DebateCategory.objects.exists():
        print("Database is empty, running populate_sample_data...")
        call_command('populate_sample_data')
    else:
        print("Database already contains data, skipping population.")

class MyappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'myapp'

    def ready(self):
        """
        Connect the populate_data function to be called after migrations are run.
        """
        post_migrate.connect(populate_data, sender=self)
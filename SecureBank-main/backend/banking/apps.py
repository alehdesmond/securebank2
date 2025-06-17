from django.apps import AppConfig

class BankingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'backend.banking' 
    
# Import the signals module to ensure the signal handlers are registered
    def ready(self):
     import backend.accounts.signals       
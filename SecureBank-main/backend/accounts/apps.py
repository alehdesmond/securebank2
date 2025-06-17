from django.apps import AppConfig

class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'backend.accounts'  # This must match the folder path used in INSTALLED_APPS

    def ready(self):
        import backend.accounts.signals  # Ensures signal handlers are connected

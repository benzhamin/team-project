from django.apps import AppConfig

default_auto_field = 'django.db.models.BigAutoField'

class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'

    def ready(self):
        import accounts.signals
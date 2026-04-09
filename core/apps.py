from django.apps import AppConfig

class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'applicatie.core'  # <- dit moet overeenkomen met INSTALLED_APPS

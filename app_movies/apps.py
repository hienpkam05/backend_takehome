from django.apps import AppConfig


class AppMoviesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app_movies'

    def ready(self):
        import app_movies.signals  

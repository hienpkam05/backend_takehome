# Register your models here.
from django.contrib import admin
from .models import Movie, MovieRating

@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "title",
        "genre",
        "director",
        "release_year",
        "rating",
        "rating_count",
        "created_by",
        "is_deleted",
    ]
    list_filter = ["genre", "is_deleted", "release_year"]
    search_fields = ["title", "director", "created_by__username"]
    readonly_fields = [
        "rating",
        "rating_count",
        "created_at",
        "updated_at",
        "deleted_at",
    ]


@admin.register(MovieRating)
class MovieRatingAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "movie",
        "user",
        "score",
        "created_at",
        "updated_at",
    ]
    search_fields = ["movie__title", "user__username"]
    list_filter = ["score", "created_at"]

from decimal import Decimal, ROUND_HALF_UP

from django.db.models import Avg, Count
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import Movie, MovieRating


def recalculate_movie_rating(movie_id):
    statistics = MovieRating.objects.filter(movie_id=movie_id).aggregate(
        average_rating=Avg("score"),
        total_ratings=Count("id"),
    )
    average_rating = Decimal(
        str(statistics["average_rating"] or 0)
    ).quantize(
        Decimal("0.1"),
        rounding=ROUND_HALF_UP,
    )

    Movie.objects.filter(pk=movie_id).update(
        rating=average_rating,
        rating_count=statistics["total_ratings"] or 0,
    )


@receiver(post_save, sender=MovieRating)
def update_movie_rating_after_save(sender, instance, **kwargs):
    recalculate_movie_rating(instance.movie_id)


@receiver(post_delete, sender=MovieRating)
def update_movie_rating_after_delete(sender, instance, **kwargs):
    recalculate_movie_rating(instance.movie_id)

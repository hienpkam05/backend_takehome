from django.db import models
from decimal import Decimal
from django.utils import timezone
# Create your models here.
from django.conf import settings
from django.core.validators import MaxValueValidator,MinValueValidator

class Movie( models.Model):
    GENRE_ACTION = "action"
    GENRE_COMEDY="comedy"
    GENRE_DRAMA = "drama"
    GENRE_HORROR = "horror"
    GENRE_SCI_FI = "sci_fi"
    GENRE_OTHER = "other"
    GENRE_CHOICES = [
        (GENRE_ACTION, "Hành động"),
        (GENRE_COMEDY, "Hài"),
        (GENRE_DRAMA, "Chính kịch"),
        (GENRE_HORROR, "Kinh dị"),
        (GENRE_SCI_FI, "Khoa học viễn tưởng"),
        (GENRE_OTHER, "Khác"),
    ]
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=200,db_index=True)
    description= models.TextField()
    director= models.CharField(max_length=100,db_index=True)
    genre= models.CharField(
        max_length=50,
        choices= GENRE_CHOICES,
        db_index=True,
    )
    release_year= models.PositiveIntegerField(db_index=True)
    rating = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        default=Decimal("0.0"),
        validators=[
            MinValueValidator(Decimal("0.0")),
            MaxValueValidator(Decimal("10.0")),
        ],
        db_index=True,
    )
    rating_count = models.PositiveIntegerField(default=0)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_movies",
    )

    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "tb_movies"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["is_deleted", "genre"]),
            models.Index(fields=["is_deleted", "release_year"]),
            models.Index(fields=["is_deleted", "rating"]),
            models.Index(fields=["created_by", "is_deleted"]),
        ]

    def __str__(self):
        return self.title
    def delete(
        self,
        using=None,
        keep_parents=False,
        hard=False,
    ):
        """Mặc định xóa mềm; hard=True mới xóa thật khỏi database."""
        if hard:
            return super().delete(
                using=using,
                keep_parents=keep_parents,
            )

        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(
            update_fields=[
                "is_deleted",
                "deleted_at",
                "updated_at",
            ]
        )
        return None

class MovieRating(models.Model):
    id = models.AutoField(primary_key=True)
    movie = models.ForeignKey(
        Movie,
        on_delete=models.CASCADE,
        related_name="user_ratings",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="movie_ratings",
    )
    score = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(10),
        ]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "tb_movie_ratings"
        ordering = ["-updated_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["movie", "user"],
                name="unique_user_movie_rating",
            )
        ]

    def __str__(self):
        return (
            f"{self.user.username} - {self.movie.title}: {self.score}"
        )


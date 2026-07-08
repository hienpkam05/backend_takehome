import django_filters
from rest_framework.exceptions import ValidationError

from .models import Movie


class MovieFilter(django_filters.FilterSet):
    genre = django_filters.ChoiceFilter(
        field_name="genre",
        choices=Movie.GENRE_CHOICES,
    )
    release_year = django_filters.NumberFilter(
        field_name="release_year",
    )
    year = django_filters.NumberFilter(
        field_name="release_year",
    )
    min_year = django_filters.NumberFilter(
        field_name="release_year",
        lookup_expr="gte",
    )
    max_year = django_filters.NumberFilter(
        field_name="release_year",
        lookup_expr="lte",
    )
    min_rating = django_filters.NumberFilter(
        field_name="rating",
        lookup_expr="gte",
    )
    max_rating = django_filters.NumberFilter(
        field_name="rating",
        lookup_expr="lte",
    )
    created_by = django_filters.NumberFilter(
        field_name="created_by_id",
    )
    created_by_username = django_filters.CharFilter(
        field_name="created_by__username",
        lookup_expr="iexact",
    )
    has_rating = django_filters.BooleanFilter(
        method="filter_has_rating",
    )

    class Meta:
        model = Movie
        fields = ["genre", "release_year", "year", "created_by"]

    def filter_has_rating(self, queryset, name, value):
        if value is True:
            return queryset.filter(rating_count__gt=0) 
        if value is False:
            return queryset.filter(rating_count=0)
        return queryset
    
    def filter_queryset(self, queryset):
        """Kiểm tra min/max rồi mới áp dụng filter vào queryset."""
        min_year = self.form.cleaned_data.get("min_year")
        max_year = self.form.cleaned_data.get("max_year")
        min_rating = self.form.cleaned_data.get("min_rating")
        max_rating = self.form.cleaned_data.get("max_rating")

        errors = {}

        if min_year is not None and max_year is not None:
            if min_year > max_year:
                errors["year_range"] = (
                    "min_year không được lớn hơn max_year."
                )

        if min_rating is not None and max_rating is not None:
            if min_rating > max_rating:
                errors["rating_range"] = (
                    "min_rating không được lớn hơn max_rating."
                )

        if min_rating is not None and not 0 <= min_rating <= 10:
            errors["min_rating"] = "min_rating phải từ 0 đến 10."

        if max_rating is not None and not 0 <= max_rating <= 10:
            errors["max_rating"] = "max_rating phải từ 0 đến 10."

        if errors:
            raise ValidationError(errors)

        return super().filter_queryset(queryset)

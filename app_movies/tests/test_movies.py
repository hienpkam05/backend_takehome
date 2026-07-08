from decimal import Decimal

import pytest
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APIClient

from app_movies.models import Movie, MovieRating


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def owner(db):
    return User.objects.create_user(
        username="owner",
        password="StrongPass123!",
    )


@pytest.fixture
def other_user(db):
    return User.objects.create_user(
        username="other",
        password="StrongPass123!",
    )


@pytest.fixture
def movie(owner):
    return Movie.objects.create(
        title="Interstellar",
        director="Christopher Nolan",
        description="A long journey through space.",
        release_year=2014,
        genre=Movie.GENRE_SCI_FI,
        created_by=owner,
    )


@pytest.mark.django_db
def test_public_can_list_and_retrieve_movies(api_client, movie):
    list_response = api_client.get("/api/movies/")
    detail_response = api_client.get(f"/api/movies/{movie.id}/")

    assert list_response.status_code == status.HTTP_200_OK
    assert detail_response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_post_without_token_returns_401(api_client):
    response = api_client.post(
        "/api/movies/",
        {
            "title": "Inception",
            "director": "Christopher Nolan",
            "description": "A movie about nested dreams.",
            "release_year": 2010,
            "genre": Movie.GENRE_SCI_FI,
        },
        format="json",
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_authenticated_user_can_create_movie(api_client, owner):
    api_client.force_authenticate(owner)
    response = api_client.post(
        "/api/movies/",
        {
            "title": "Inception",
            "director": "Christopher Nolan",
            "description": "A movie about nested dreams.",
            "release_year": 2010,
            "genre": Movie.GENRE_SCI_FI,
        },
        format="json",
    )

    assert response.status_code == status.HTTP_201_CREATED
    created = Movie.objects.get(title="Inception")
    assert created.created_by == owner


@pytest.mark.django_db
def test_non_owner_cannot_update_or_delete(api_client, other_user, movie):
    api_client.force_authenticate(other_user)

    patch_response = api_client.patch(
        f"/api/movies/{movie.id}/",
        {"title": "Changed Title"},
        format="json",
    )
    delete_response = api_client.delete(f"/api/movies/{movie.id}/")

    assert patch_response.status_code == status.HTTP_403_FORBIDDEN
    assert delete_response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_owner_soft_delete_hides_movie(api_client, owner, movie):
    api_client.force_authenticate(owner)
    response = api_client.delete(f"/api/movies/{movie.id}/")

    assert response.status_code == status.HTTP_200_OK
    movie.refresh_from_db()
    assert movie.is_deleted is True
    assert movie.deleted_at is not None

    public_response = api_client.get(f"/api/movies/{movie.id}/")
    assert public_response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_hard_delete_from_model(movie):
    movie_id = movie.id
    movie.delete(hard=True)

    assert Movie.objects.filter(id=movie_id).exists() is False


@pytest.mark.django_db
def test_rate_requires_login(api_client, movie):
    response = api_client.post(
        f"/api/movies/{movie.id}/rate/",
        {"rating": 8},
        format="json",
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_same_user_rating_overwrites_old_rating(api_client, owner, movie):
    api_client.force_authenticate(owner)

    first = api_client.post(
        f"/api/movies/{movie.id}/rate/",
        {"rating": 8},
        format="json",
    )
    second = api_client.post(
        f"/api/movies/{movie.id}/rate/",
        {"rating": 10},
        format="json",
    )

    assert first.status_code == status.HTTP_200_OK
    assert second.status_code == status.HTTP_200_OK
    assert MovieRating.objects.filter(movie=movie, user=owner).count() == 1

    movie.refresh_from_db()
    assert movie.rating == Decimal("10.0")
    assert movie.rating_count == 1


@pytest.mark.django_db
def test_average_rating_from_multiple_users(
    api_client,
    owner,
    other_user,
    movie,
):
    api_client.force_authenticate(owner)
    api_client.post(
        f"/api/movies/{movie.id}/rate/",
        {"rating": 8},
        format="json",
    )

    api_client.force_authenticate(other_user)
    api_client.post(
        f"/api/movies/{movie.id}/rate/",
        {"rating": 10},
        format="json",
    )

    movie.refresh_from_db()
    assert movie.rating == Decimal("9.0")
    assert movie.rating_count == 2


@pytest.mark.django_db
def test_movie_rating_changes_recalculate_movie_summary(
    owner,
    other_user,
    movie,
):
    rating = MovieRating.objects.create(
        movie=movie,
        user=owner,
        score=8,
    )
    MovieRating.objects.create(
        movie=movie,
        user=other_user,
        score=10,
    )

    movie.refresh_from_db()
    assert movie.rating == Decimal("9.0")
    assert movie.rating_count == 2

    rating.score = 6
    rating.save()
    movie.refresh_from_db()
    assert movie.rating == Decimal("8.0")
    assert movie.rating_count == 2

    rating.delete()
    movie.refresh_from_db()
    assert movie.rating == Decimal("10.0")
    assert movie.rating_count == 1


@pytest.mark.django_db
def test_invalid_rating_returns_400(api_client, owner, movie):
    api_client.force_authenticate(owner)
    response = api_client.post(
        f"/api/movies/{movie.id}/rate/",
        {"rating": 11},
        format="json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_filter_backend_filters_year_range(api_client, movie, owner):
    Movie.objects.create(
        title="Old Movie",
        director="Old Director",
        description="An old movie used for filter tests.",
        release_year=1990,
        genre=Movie.GENRE_DRAMA,
        created_by=owner,
    )

    response = api_client.get("/api/movies/?min_year=2000&max_year=2020")

    assert response.status_code == status.HTTP_200_OK
    assert response.data["count"] == 1
    assert response.data["results"][0]["id"] == movie.id


@pytest.mark.django_db
def test_filter_backend_filters_exact_year(api_client, movie, owner):
    Movie.objects.create(
        title="Different Year Movie",
        director="Other Director",
        description="Another movie used for exact year filter tests.",
        release_year=1990,
        genre=Movie.GENRE_DRAMA,
        created_by=owner,
    )

    response = api_client.get("/api/movies/?year=2014")

    assert response.status_code == status.HTTP_200_OK
    assert response.data["count"] == 1
    assert response.data["results"][0]["id"] == movie.id


@pytest.mark.django_db
def test_top_rated_returns_at_most_10_sorted_movies(api_client, owner):
    for index in range(12):
        Movie.objects.create(
            title=f"Movie {index}",
            director="Director",
            description="A valid movie description for top rated tests.",
            release_year=2000 + index,
            genre=Movie.GENRE_ACTION,
            rating=Decimal(str((index % 10) + 1)),
            rating_count=1,
            created_by=owner,
        )

    response = api_client.get("/api/movies/top-rated/")

    assert response.status_code == status.HTTP_200_OK
    assert response.data["count"] == 10
    ratings = [Decimal(str(item["rating"])) for item in response.data["results"]]
    assert ratings == sorted(ratings, reverse=True)


@pytest.mark.django_db
def test_list_uses_custom_pagination(api_client, owner):
    for index in range(12):
        Movie.objects.create(
            title=f"Movie {index}",
            description="A valid movie description for pagination tests.",
            director="Director Test",
            genre=Movie.GENRE_DRAMA,
            release_year=2000 + index,
            created_by=owner,
        )

    response = api_client.get("/api/movies/?page=1&page_size=5")

    assert response.status_code == status.HTTP_200_OK
    assert "count" in response.data
    assert "current_page_number" in response.data
    assert "page_size" in response.data
    assert "total_pages" in response.data
    assert "next" in response.data
    assert "previous" in response.data
    assert "results" in response.data
    assert response.data["current_page_number"] == 1
    assert response.data["page_size"] == 5
    assert len(response.data["results"]) == 5
    assert response.data["total_pages"] >= 3


@pytest.mark.django_db
def test_second_page_returns_remaining_movies(api_client, owner):
    for index in range(6):
        Movie.objects.create(
            title=f"Paged Movie {index}",
            description="A valid movie description for pagination tests.",
            director="Director Test",
            genre=Movie.GENRE_ACTION,
            release_year=2010 + index,
            created_by=owner,
        )

    response = api_client.get("/api/movies/?page=2&page_size=5")

    assert response.status_code == status.HTTP_200_OK
    assert response.data["current_page_number"] == 2
    assert len(response.data["results"]) > 0

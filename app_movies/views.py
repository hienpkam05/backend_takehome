from decimal import Decimal, ROUND_HALF_UP

from django.db import transaction
from django.db.models import Avg, Count
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (
    AllowAny,
    BasePermission,
    IsAuthenticated,
)
from rest_framework.response import Response

from .filters import MovieFilter
from .models import Movie, MovieRating
from .paginations import MoviePagination
from .serializers import MovieSerializer, RateMovieSerializer


class IsMovieOwner(BasePermission):
    message = (
        "Bạn không phải người tạo phim này nên không được sửa hoặc xóa."
    )

    def has_object_permission(self, request, view, obj):
        return (
            request.user.is_authenticated
            and obj.created_by_id == request.user.id
        )


class MovieViewSet(viewsets.ModelViewSet):
    serializer_class = MovieSerializer
    pagination_class = MoviePagination

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_class = MovieFilter
    search_fields = [
        "title",
        "director",
        "description",
        "created_by__username",
    ]
    ordering_fields = [
        "id",
        "title",
        "director",
        "release_year",
        "rating",
        "rating_count",
        "created_at",
        "updated_at",
    ]
    ordering = ["-created_at"]

    def get_queryset(self):
        """
        Queryset gốc chỉ lấy phim chưa bị xóa mềm.

        Filter, search và ordering được xử lý bởi filter_backends,
        không đọc request.query_params thủ công ở đây.
        """
        return Movie.objects.filter(is_deleted=False).select_related(
            "created_by"
        )

    def get_permissions(self):
        """Chọn permission theo action mà router đang gọi."""
        public_actions = ["list", "retrieve", "top_rated"]
        authenticated_actions = ["create", "rate"]
        owner_actions = ["update", "partial_update", "destroy"]

        if self.action in public_actions:
            permission_classes = [AllowAny]
        elif self.action in authenticated_actions:
            permission_classes = [IsAuthenticated]
        elif self.action in owner_actions:
            permission_classes = [IsAuthenticated, IsMovieOwner]
        else:
            permission_classes = [IsAuthenticated]

        return [permission() for permission in permission_classes]

    def list(self, request, *args, **kwargs):
        """Public: danh sách có filter, search, ordering, pagination."""
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def retrieve(self, request, *args, **kwargs):
        """Public: lấy chi tiết một phim chưa bị xóa mềm."""
        movie = self.get_object()
        serializer = self.get_serializer(movie)
        return Response({
                "message": "Lấy thông tin phim thành công.",
                "data": serializer.data,
            },status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        """Cần JWT; backend tự gán created_by=request.user."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        movie = serializer.save(created_by=request.user)

        return Response({
                "message": "Tạo phim mới thành công.",
                "data": self.get_serializer(movie).data,
            },status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        """PUT: cần JWT và chỉ chủ phim được cập nhật toàn bộ."""
        movie = self.get_object()
        serializer = self.get_serializer(
            movie,
            data=request.data,
            partial=False,
        )
        serializer.is_valid(raise_exception=True)
        movie = serializer.save()

        return Response({
                "message": "Cập nhật toàn bộ phim thành công.",
                "data": self.get_serializer(movie).data,
            },status=status.HTTP_200_OK,)

    def partial_update(self, request, *args, **kwargs):
        """PATCH: cần JWT và chỉ chủ phim được cập nhật một phần."""
        movie = self.get_object()
        serializer = self.get_serializer(
            movie,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        movie = serializer.save()

        return Response({
                "message": "Cập nhật một phần phim thành công.",
                "data": self.get_serializer(movie).data,
            },status=status.HTTP_200_OK)

    @transaction.atomic
    def destroy(self, request, *args, **kwargs):
        """DELETE: cần JWT, chỉ chủ phim; gọi model.delete() để xóa mềm."""
        movie = self.get_object()
        movie.delete()

        return Response({
                "message": "Xóa mềm phim thành công.",
                "data": {
                    "id": movie.id,
                    "title": movie.title,
                    "is_deleted": movie.is_deleted,
                    "deleted_at": movie.deleted_at,
                },
            },status=status.HTTP_200_OK)

    @extend_schema(
        summary="Lấy top 10 phim có rating cao nhất",
        responses=MovieSerializer(many=True),
    )
    @action(detail=False, methods=["get"], url_path="top-rated")
    def top_rated(self, request):
        """Public; cho phép kết hợp filter/search trước khi lấy top 10."""
        queryset = self.filter_queryset(self.get_queryset())
        movies = (
            queryset.filter(rating_count__gt=0)
            .order_by("-rating", "-created_at")[:10]
        )
        serializer = self.get_serializer(movies, many=True)

        return Response({
                "message": "Lấy top 10 phim rating cao nhất thành công.",
                "count": len(serializer.data),
                "results": serializer.data,
            },status=status.HTTP_200_OK)

    @extend_schema(
        summary="Đánh giá hoặc cập nhật lại rating của phim",
        request=RateMovieSerializer,
        responses={
            200: OpenApiResponse(
                description="Tạo hoặc cập nhật rating thành công."
            )
        },
    )
    @action(detail=True, methods=["post"], url_path="rate")
    @transaction.atomic
    def rate(self, request, pk=None):
        """
        Cần JWT.

        Mỗi user chỉ có một MovieRating cho một phim. Lần sau gọi API
        sẽ update điểm cũ nhờ update_or_create(), sau đó tính lại điểm
        trung bình và tổng số người đánh giá.
        """
        movie = get_object_or_404(
            self.get_queryset().select_for_update(),
            pk=pk,
        )

        input_serializer = RateMovieSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)
        score = input_serializer.validated_data["rating"]

        movie_rating, created = MovieRating.objects.update_or_create(
            movie=movie,
            user=request.user,
            defaults={"score": score},
        )

        statistics = MovieRating.objects.filter(movie=movie).aggregate(
            average_rating=Avg("score"),
            total_ratings=Count("id"),
        )

        average_rating = Decimal(
            str(statistics["average_rating"] or 0)
        ).quantize(
            Decimal("0.1"),
            rounding=ROUND_HALF_UP,
        )
        total_ratings = statistics["total_ratings"] or 0

        movie.rating = average_rating
        movie.rating_count = total_ratings
        movie.save(
            update_fields=[
                "rating",
                "rating_count",
                "updated_at",
            ]
        )

        message = (
            "Đánh giá phim thành công."
            if created
            else "Cập nhật lại đánh giá phim thành công."
        )

        return Response({
                "message": message,
                "movie_id": movie.id,
                "your_rating": movie_rating.score,
                "average_rating": movie.rating,
                "rating_count": movie.rating_count,
            },status=status.HTTP_200_OK)


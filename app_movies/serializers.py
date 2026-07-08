from datetime import date
from rest_framework import serializers
from .models import Movie

class MovieSerializer(serializers.ModelSerializer):
    str= serializers.SerializerMethodField()
    created_by_username = serializers.CharField(
        source="created_by.username",
        read_only=True,
    )
    genre_display = serializers.CharField(
        source="get_genre_display",
        read_only=True,
    )

    class Meta:
        model = Movie
        fields = [
            "id",
            "title",
            "director",
            "description",
            "release_year",
            "genre",
            "genre_display",
            "rating",
            "rating_count",
            "created_by",
            "created_by_username",
            "str",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "rating",
            "rating_count",
            "created_by",
            "created_by_username",
            "genre_display",
            "str",
            "created_at",
            "updated_at",
        ]
        extra_kwargs = {
            "title": {
                "required": True,
                "allow_blank": False,
                "error_messages": {
                    "required": "Tiêu đề phim là bắt buộc.",
                    "blank": "Tiêu đề phim không được để trống.",
                    "max_length": (
                        "Tiêu đề phim không được vượt quá 200 ký tự."
                    ),
                },
            },
            "director": {
                "required": True,
                "allow_blank": False,
                "error_messages": {
                    "required": "Tên đạo diễn là bắt buộc.",
                    "blank": "Tên đạo diễn không được để trống.",
                    "max_length": (
                        "Tên đạo diễn không được vượt quá 100 ký tự."
                    ),
                },
            },
            "description": {
                "required": True,
                "allow_blank": False,
                "error_messages": {
                    "required": "Mô tả phim là bắt buộc.",
                    "blank": "Mô tả phim không được để trống.",
                },
            },
            "release_year": {
                "required": True,
                "error_messages": {
                    "required": "Năm phát hành là bắt buộc.",
                    "invalid": "Năm phát hành phải là số nguyên.",
                },
            },
            "genre": {
                "required": True,
                "error_messages": {
                    "required": "Thể loại phim là bắt buộc.",
                    "invalid_choice": "Thể loại phim không hợp lệ.",
                },
            },
        }

    def get_str(self, obj):
        return str(obj)

    def validate_title(self, value):
        value = " ".join(value.split())
        if len(value) < 2:
            raise serializers.ValidationError(
                "Tiêu đề phim phải có ít nhất 2 ký tự."
            )
        return value

    def validate_director(self, value):
        value = " ".join(value.split())
        if len(value) < 2:
            raise serializers.ValidationError(
                "Tên đạo diễn phải có ít nhất 2 ký tự."
            )
        return value

    def validate_description(self, value):
        value = value.strip()
        if len(value) < 10:
            raise serializers.ValidationError(
                "Mô tả phim phải có ít nhất 10 ký tự."
            )
        return value

    def validate_release_year(self, value):
        current_year = date.today().year
        if value < 1888:
            raise serializers.ValidationError(
                "Năm phát hành không được nhỏ hơn 1888."
            )
        if value > current_year + 2:
            raise serializers.ValidationError(
                f"Năm phát hành không được lớn hơn {current_year + 2}."
            )
        return value

    def validate(self, attrs):
        """
        Một user không được có hai phim chưa xóa với cùng tiêu đề
        và cùng năm phát hành.
        """
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return attrs

        title = attrs.get("title", getattr(self.instance, "title", None))
        release_year = attrs.get(
            "release_year",
            getattr(self.instance, "release_year", None),
        )

        if not title or release_year is None:
            return attrs

        queryset = Movie.objects.filter(
            created_by=request.user,
            title__iexact=title.strip(),
            release_year=release_year,
            is_deleted=False,
        )

        if self.instance is not None:
            queryset = queryset.exclude(pk=self.instance.pk)

        if queryset.exists():
            raise serializers.ValidationError(
                {
                    "movie": (
                        "Bạn đã tạo một phim có cùng tiêu đề "
                        "và năm phát hành."
                    )
                }
            )

        return attrs


class RateMovieSerializer(serializers.Serializer):
    rating = serializers.IntegerField(
        min_value=1,
        max_value=10,
        required=True,
        error_messages={
            "required": "Bạn phải gửi điểm rating.",
            "invalid": "Rating phải là số nguyên.",
            "min_value": "Rating không được nhỏ hơn 1.",
            "max_value": "Rating không được lớn hơn 10.",
        },
    )

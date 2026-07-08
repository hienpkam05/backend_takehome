# Bài test Take-home — Backend Intern

Chào bạn! Cảm ơn bạn đã tham gia quy trình tuyển dụng tại Metatwin.

## Thông tin bài test

- **Thời gian:** 48 giờ kể từ khi nhận đề
- **Nộp bài:** Link GitHub repo (public hoặc invite reviewer)
- **Stack:** Python 3.10+, Django 4.x, Django REST Framework, PostgreSQL, Docker
- **Được dùng AI** nhưng phỏng vấn phải giải thích được từng dòng.

## Đề bài — Django app `app_movies`

Xây REST API quản lý phim từ đầu, có soft delete, pagination custom, filter + search, custom action, test bằng pytest.

## Setup môi trường

```bash
# Local (venv)
python -m venv venv
source venv/bin/activate    # Windows: venv\Scripts\activate
pip install -r requirements.txt
docker-compose up -d        # start PostgreSQL
python manage.py migrate
python manage.py runserver

# Hoặc full Docker
make build && make up && make migrate
```

## Yêu cầu

### 1. Project structure
```
movies-api/
├── manage.py
├── core/
│   ├── settings.py
│   └── urls.py
├── app_movies/
│   ├── models.py
│   ├── serializers.py
│   ├── views.py
│   ├── urls.py
│   ├── admin.py
│   └── tests/
│       └── test_movies.py
├── docker-compose.yml
├── Dockerfile
├── Makefile
├── requirements.txt
└── README.md
```

### 2. Model `Movie` (`app_movies/models.py`)

- `id` AutoField PK
- `title` CharField(200)
- `director` CharField(100)
- `release_year` IntegerField
- `genre` CharField với choices `action / drama / comedy / horror / sci_fi / other` (dùng hằng `GENRE_ACTION = "action"` etc)
- `rating` IntegerField với `MinValueValidator(1)` + `MaxValueValidator(10)`
- `is_deleted` BooleanField default `False`
- `created_at` / `updated_at` auto
- `Meta.db_table = "tb_movies"`, `ordering = ["-created_at"]`
- `__str__` trả `self.title`

### 3. Soft delete

Override `delete()`:
- Mặc định set `is_deleted=True`, không xóa DB row.
- `hard=True` → xóa thật.

### 4. Serializer

`MovieSerializer(ModelSerializer)` — `fields = "__all__"` + thêm `str = SerializerMethodField()` trả `obj.__str__()`.

### 5. ViewSet + endpoints

`MovieViewSet(ModelViewSet)` với:
- `get_queryset()` filter `is_deleted=False`.
- Pagination custom (page_size=10), response format:
  ```json
  { "count": 50, "total_pages": 5, "current_page_number": 2,
    "next": "...", "previous": "...", "results": [...] }
  ```
- `?genre=action` — filter genre.
- `?min_year=2000&max_year=2010` — filter range `release_year`.
- `?search=keyword` — icontains `title`.
- Custom action `GET /movies/top-rated/` — top 10 phim theo rating desc, tiebreak `-created_at`.
- Custom action `POST /movies/{id}/rate/` — body `{"rating": 1-10}`, cập nhật rating; validate ngoài range trả 400.

Dùng `DefaultRouter`, URL gốc `/api/movies/`.

### 6. Docker

- `docker-compose.yml` chạy PostgreSQL 15 + service Django.
- `Dockerfile` Python 3.10-slim.
- `docker compose up` xong: API tại `http://localhost:8000/api/movies/`.

### 7. Makefile

Target: `build`, `up`, `migrate`, `test`, `shell`.

### 8. README.md

- Cách setup local + docker.
- Liệt kê endpoint + ví dụ curl.
- Section "Trade-off": vì sao chọn soft-delete? Vì sao custom pagination?

### 9. Test (BẮT BUỘC) — ≥ 5 test pytest, tất cả pass

Trong `app_movies/tests/test_movies.py`:
1. POST tạo Movie → 201.
2. DELETE → `is_deleted=True`, GET list không thấy; kiểm hard delete từ shell.
3. `/top-rated/` — max 10 item, sort đúng.
4. `/{id}/rate/` — body hợp lệ 200 + rating cập nhật; body ngoài [1,10] → 400.
5. Filter `?min_year=2000&max_year=2010` — chỉ trả phim trong range.

Chạy `pytest -q` xanh. Gợi ý: `pytest-django` + `APIClient`.

### Bonus (không bắt buộc)

- **JWT auth** (`djangorestframework-simplejwt`): `POST /api/token/` trả `access` + `refresh`; POST/PATCH/DELETE/rate yêu cầu `IsAuthenticated`, GET public. Thêm 1 test cho "POST không token → 401".
- API docs qua `drf-yasg` hoặc `drf-spectacular`.
- `.env.example`.
- Pre-commit hook (black/ruff).
- GitHub Actions chạy pytest.
- FK `created_by` → `User`, gán tự động trong serializer.

## Lưu ý

- Đây là bài tự làm cá nhân.
- Được dùng tài liệu, internet, AI — miễn hiểu và giải thích được.
- Nếu đề chưa rõ, reply email hỏi thẳng.

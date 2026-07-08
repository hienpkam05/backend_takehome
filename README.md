# Movies API

REST API quan ly phim bang Django REST Framework, co soft delete, custom pagination, filter/search, JWT auth va test bang pytest.

## Setup Local

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
docker compose up -d db
python manage.py migrate
python manage.py runserver
```

API chay tai `http://localhost:8000/api/movies/`.

## Setup Docker

```bash
make build
make up
make migrate
```

## Test

```bash
pytest -q
```

Khi chay pytest, project dung SQLite test database rieng de khong phu thuoc quyen `CREATE DATABASE` cua PostgreSQL local.

## Endpoints

- `GET /api/movies/`: danh sach phim, public.
- `GET /api/movies/{id}/`: chi tiet phim, public.
- `POST /api/movies/`: tao phim, can JWT.
- `PATCH /api/movies/{id}/`: sua phim, chi owner.
- `DELETE /api/movies/{id}/`: soft delete, chi owner.
- `GET /api/movies/top-rated/`: top 10 phim co rating cao nhat.
- `POST /api/movies/{id}/rate/`: danh gia phim, can JWT.
- `POST /api/token/`: lay access/refresh token.
- `POST /api/token/refresh/`: refresh access token.
- `GET /api/docs/`: Swagger UI.

## Curl Examples

```bash
curl http://localhost:8000/api/movies/
curl "http://localhost:8000/api/movies/?genre=action&min_year=2000&max_year=2020&search=matrix"
curl http://localhost:8000/api/movies/top-rated/
```

```bash
curl -X POST http://localhost:8000/api/token/ ^
  -H "Content-Type: application/json" ^
  -d "{\"username\":\"owner\",\"password\":\"StrongPass123!\"}"
```

```bash
curl -X POST http://localhost:8000/api/movies/ ^
  -H "Authorization: Bearer <access_token>" ^
  -H "Content-Type: application/json" ^
  -d "{\"title\":\"Inception\",\"director\":\"Christopher Nolan\",\"description\":\"A movie about nested dreams.\",\"release_year\":2010,\"genre\":\"sci_fi\"}"
```

```bash
curl -X POST http://localhost:8000/api/movies/1/rate/ ^
  -H "Authorization: Bearer <access_token>" ^
  -H "Content-Type: application/json" ^
  -d "{\"rating\":9}"
```

## Trade-off

Soft delete giu lai du lieu de audit, khoi phuc va tranh mat lien ket rating/user. Doi lai, moi query doc phim can filter `is_deleted=False`.

Custom pagination giup response on dinh theo format de bai, gom tong so item, tong so trang, trang hien tai, link next/previous va results. Doi lai, code pagination phai tu bao tri thay vi dung response mac dinh cua DRF.

`Movie.rating` dang luu diem trung binh dang decimal, con diem tung user nam trong `MovieRating.score`. Cach nay phu hop hon voi nghiep vu nhieu user cung danh gia mot phim, du khac voi mo ta toi thieu trong de la `IntegerField`.

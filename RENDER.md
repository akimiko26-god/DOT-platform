# Деплой на Render.com (бесплатно)

Один Docker-сервис: frontend (сборка) + FastAPI + SQLite.

## Быстрый старт (5 минут)

1. Зарегистрируйтесь: [render.com](https://render.com) → **Get Started** → войдите через **GitHub**
2. Откройте Blueprint (подставит `render.yaml` из репозитория):

   **https://dashboard.render.com/blueprint/new?repo=https://github.com/akimiko26-god/DOT-platform**

3. Нажмите **Apply** / **Create**
4. Дождитесь сборки (~5–10 мин, первая сборка дольше)
5. Откройте URL вида `https://dot-platform.onrender.com`

Проверка: `https://ВАШ-URL.onrender.com/api/health` → `{"status":"ok",...}`

## После деплоя

| Что | Где |
|-----|-----|
| Сайт и кабинет | `https://dot-platform-xxxx.onrender.com` |
| API docs | `/docs` |
| Супер-админ | см. `SUPERADMIN.txt` (создаётся при первом старте) |

`FRONTEND_URL` для QR и ссылок подставляется из `RENDER_EXTERNAL_URL` автоматически.

## Ограничения free tier

- Сервис **засыпает** без трафика (~50 сек пробуждение при первом заходе)
- SQLite и загрузки **сбрасываются** при пересборке/редеплое
- 750 часов/месяц — достаточно для MVP и демо

## Обновление

Каждый `git push` в `main` → автодеплой (если включён в Render).

## Переменные (Dashboard → dot-platform → Environment)

| Переменная | Обязательно | Описание |
|------------|-------------|----------|
| `SECRET_KEY` | да (auto) | JWT, генерируется Blueprint |
| `DATABASE_URL` | да | SQLite в контейнере |
| SMTP_* | нет | Почта для сброса пароля |

## Если сборка падает

1. **Logs** в Render Dashboard → посмотреть ошибку Docker build
2. Локально проверить: `docker build -t dot-test .`
3. Убедиться, что ветка **`main`** и файл `render.yaml` в корне репозитория

## Платный апгрейд (позже)

- **Persistent Disk** — сохранить SQLite и uploads
- **PostgreSQL** на Render — для продакшена

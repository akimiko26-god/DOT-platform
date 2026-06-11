# ./dot platform — инструкции для агентов

## Стек

- **Backend:** Python 3, FastAPI, SQLAlchemy, SQLite (`backend/dot_local.db`)
- **Frontend:** React 18, Vite (`frontend/`)
- **Прокси:** Vite проксирует `/api` → `http://127.0.0.1:8000`

## Cursor Cloud — быстрый старт

После `install` поднимаются два терминала (см. `.cursor/environment.json`):

| Сервис   | URL |
|----------|-----|
| Frontend | http://localhost:5173 |
| API      | http://localhost:8000 |
| Health   | http://localhost:8000/api/health |
| API docs | http://localhost:8000/docs |

Проверка: `curl -s http://localhost:8000/api/health` → `{"status":"ok",...}`

## Команды разработки (локально в VM)

```bash
# Зависимости (уже в install, повтор при необходимости)
python3 -m venv backend/.venv && backend/.venv/bin/pip install -r backend/requirements.txt
npm ci --prefix frontend

# Backend
cd backend && .venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Frontend (другой терминал)
npm run dev --prefix frontend -- --host 0.0.0.0 --port 5173

# Production-сборка frontend
npm run build --prefix frontend
```

## Секреты (Cursor Dashboard → Cloud Agents → Secrets)

Опционально для облака:

| Переменная | Назначение |
|------------|------------|
| `SECRET_KEY` | JWT (иначе дефолт из config.py) |
| `DATABASE_URL` | По умолчанию `sqlite:///./dot_local.db` в `backend/` |
| `FRONTEND_URL` | Для ссылок в QR и сбросе пароля |

Не коммитить `.env` с реальными ключами.

## Структура

```
backend/app/     — FastAPI routers, models, migrate.py
frontend/src/    — React pages и components
.cursor/         — конфиг Cloud Agent
```

## Супер-админ

Создаётся при старте backend (`bootstrap.py`). Учётные данные — в `SUPERADMIN.txt` (не публиковать).

## Docker (альтернатива)

```bash
docker compose up --build
```

## Перед PR

1. Убедиться, что API отвечает на `/api/health`
2. Проверить основные страницы кабинета в браузере
3. Не включать в коммит: `.venv/`, `node_modules/`, `*.db`, `uploads/`, `.env`

# ./dot — MVP цифровой платформы для МСБ

MVP по техническому заданию: единая платформа для малого и среднего бизнеса в Казахстане — онлайн-представительство, заявки, CRM, каталог, QR и мессенджеры.

## Стек (по ТЗ)

| Слой | Технология |
|------|------------|
| Backend | Python, FastAPI, REST API |
| Frontend | React, Vite |
| БД | PostgreSQL |
| Инфраструктура | Docker, Docker Compose, Nginx |

## Реализовано в MVP (этап 2)

- **Регистрация и личный кабинет** — профиль компании, контакты, мессенджеры, модули
- **Заявки** — приём с публичной формы, статусы, комментарии, история
- **CRM** — база клиентов, счётчик обращений, автосоздание из заявок
- **Цифровой каталог** — товары/услуги, цены, категории, адаптивная публичная страница
- **QR** — генерация PNG для страницы, каталога, формы заявки
- **Мессенджеры** — deep links WhatsApp и Telegram с готовым текстом
- **Базовая аналитика** — заявки, источники, конверсия, повторные клиенты

## Быстрый старт (Docker)

```bash
cd dot-platform
docker compose up --build
```

- Сайт и кабинет: http://localhost (через Nginx)
- API: http://localhost/api/docs
- Frontend dev напрямую: http://localhost:5173
- Backend напрямую: http://localhost:8000

## Локальная разработка без Docker (Windows)

**Один скрипт** — откроет backend и frontend в двух окнах:

```powershell
cd C:\Users\Admin\dot-platform
.\start-dev.ps1
```

Или вручную в **двух терминалах**:

**Терминал 1 — backend (порт 8000, SQLite):**

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

**Терминал 2 — frontend (порт 5173):**

```powershell
cd frontend
npm install
npm run dev
```

Сайт: http://localhost:5173 — регистрация и вход работают только когда **оба** сервера запущены.

## Сценарий проверки

1. Откройте http://localhost:5173 → «Начать бесплатно»
2. Зарегистрируйте аккаунт и компанию (slug латиницей, например `demo-cafe`)
3. Заполните профиль в «Компания», добавьте позиции в «Каталог»
4. Откройте публичную страницу `/c/demo-cafe`, отправьте заявку
5. В кабинете «Заявки» смените статус и добавьте комментарий
6. В «QR» скачайте код для печати

## Структура API

| Метод | Путь | Описание |
|-------|------|----------|
| POST | `/api/auth/register` | Регистрация |
| POST | `/api/auth/login` | JWT токен |
| GET/POST/PATCH | `/api/companies` | Компании |
| GET/PATCH | `/api/companies/{id}/leads` | Заявки |
| GET/POST | `/api/companies/{id}/customers` | CRM |
| GET/POST | `/api/companies/{id}/catalog` | Каталог |
| GET | `/api/companies/{id}/analytics` | Аналитика |
| GET | `/api/companies/{id}/qr/image` | QR PNG |
| GET/POST | `/api/public/companies/{slug}/...` | Публичные страницы |

## Новые возможности

- **Сброс пароля** — `/forgot-password` (письмо на email; без SMTP ссылка в `backend/reset_emails.log`)
- **Сотрудники** — логины, карточки, должности, права на модули (`/app/employees`)
- **Админ-панель** — пользователи, компании, статистика (`/app/admin`, первый пользователь = админ)
- **QR** — шаблоны (минимальный, брендовый, визитка, стикер), скачивание PNG, публикация в соцсетях

## Следующие этапы (по ТЗ)

- Этап 3: тестирование на реальном МСБ
- Этап 4: админ-панель платформы, расширенные интеграции (Telegram Bot, WhatsApp Business API)

## Безопасность

- Пароли: bcrypt
- API: JWT Bearer
- Разграничение: владелец видит только свои компании
- Для production: смените `SECRET_KEY`, включите HTTPS, настройте бэкапы PostgreSQL

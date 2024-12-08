## ExamScoresBot

**ExamScoresBot** — это Telegram-бот для работы с баллами ЕГЭ. Он позволяет пользователям регистрироваться, добавлять, обновлять и просматривать свои результаты по различным предметам. Бот использует асинхронные технологии для взаимодействия с базой данных и реализации бизнес-логики.

### Функциональность
- **Регистрация пользователей**: Проверка регистрации пользователя и добавление в базу данных, если он новый
- **Добавление баллов**: Пользователи могут вводить свои результаты по экзаменам с выбором предмета и балла
- **Обновление баллов**: При наличии записей в базе бот позволяет обновить существующий балл
- **Просмотр результатов**: Вывод всех сохраненных баллов в структурированном виде

---

### Структура проекта

```
    ExamScoresBot/
    ├── bot/
    │   ├── dao/
    │   │   └── base.py           # Базовый DAO с методами CRUD
    │   ├── users/
    │   │   ├── dao.py            # Реализация DAO для работы с пользователями
    │   │   ├── models.py         # SQLAlchemy-модели таблицы пользователей
    │   │   ├── schemas.py        # Pydantic-схемы для валидации данных пользователей
    │   │   ├── service.py        # Логика управления пользователями
    │   │   └── router.py         # Роутер для обработки команд и сообщений пользователя
    │   ├── scores/
    │   │   ├── dao.py            # Реализация DAO для работы с баллами
    │   │   ├── models.py         # SQLAlchemy-модели таблицы баллов
    │   │   ├── schemas.py        # Pydantic-схемы для валидации данных баллов
    │   │   ├── service.py        # Логика управления баллами
    │   │   ├── keyboards.py      # Генерация инлайн-клавиатур
    │   │   └── router.py         # Роутер для обработки взаимодействия с баллами
    │   ├── config.py             # Настройки конфигурации (токен бота, параметры БД)
    │   ├── database.py           # Подключение к базе данных и управление сессиями
    │   └── main.py               # Основной файл запуска бота
    ├── migrations/               # Миграции для управления схемой базы данных
    ├── alembic.ini               # Конфигурация Alembic для миграций
    ├── docker-compose.yml        # Конфигурация Docker Compose для разворачивания проекта
    ├── Dockerfile                # Образ приложения для Docker
    ├── requirements.txt          # Файл зависимостей Python
    ├── .gitignore                # Исключение файлов и папок из контроля версий
    ├── README.md                 # Описание проекта
    └── .env                      # Переменные окружения
```

---

### Основные технологии
- **Python 3.10+**
- **Aiogram**: Асинхронная библиотека для разработки Telegram-ботов
- **SQLAlchemy**: ORM для работы с базой данных
- **Alembic**: Инструмент для управления миграциями базы данных
- **Pydantic**: Для валидации данных и работы с API
- **PostgreSQL**: Реляционная база данных
- **Docker**: Контейнеризация приложения
- **Loguru**: Удобная библиотека для логирования

---

### Быстрый старт

#### 1. Клонируйте репозиторий:
```bash
git clone https://github.com/KhripkovaNA/ExamScoresBot.git
cd ExamScoresBot
```

#### 2. Настройте переменные окружения:
Создайте файл `.env` и заполните его:
```env
BOT_TOKEN=ваш_токен_бота
DB_HOST=хост_БД
DB_PORT=порт_БД
DB_NAME=название_БД
DB_USER=имя_пользователя_БД
DB_PASS=пароль_БД
```

#### 3. Установите зависимости:
```bash
pip install -r requirements.txt
```

#### 4. Запустите миграции:
```bash
alembic upgrade head
```

#### 5. Запустите бота:
```bash
python -m bot.main
```

#### 6. (Опционально) Используйте Docker:
```bash
docker-compose up --build
```

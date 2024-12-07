
```
    ExamScoresBot/
    │
    ├── bot/
    │   ├── config.py         # Настройки конфигурации (токен бота, параметры БД)
    │   ├── main.py           # Основной файл приложения
    │   ├── database.py       # Подключение к базе данных
    │   └── migrations/       # Миграции Alembic
    │
    ├── users/
    │   ├── router.py         # Логика регистрации пользователей
    │   └── models.py         # SQLAlchemy-модели для пользователей
    │
    ├── scores/
    │   ├── router.py         # Логика работы с баллами ЕГЭ
    │   └── models.py         # SQLAlchemy-модели для баллов ЕГЭ
    │
    ├── docker-compose.yml    # Конфигурация Docker
    ├── Dockerfile            # Образ приложения
    ├── requirements.txt      # Зависимости Python
    └── .env                  # Переменные окружения
```
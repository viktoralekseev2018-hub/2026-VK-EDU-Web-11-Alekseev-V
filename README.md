# AskSpace · ДЗ3 · Этап 1

Добавлены модели, миграции, PostgreSQL и админка. Публичные страницы показывают примеры из ДЗ2.

## Запуск через Docker Compose

В папке с `manage.py` создайте файлы окружения. Команда использует стандартную библиотеку Python и генерирует ключ Django и пароль базы.

```console
python init_env.py
docker compose up --build -d
```

Откройте [главную страницу](http://localhost:8000/). При первом запуске Django применит миграции. Создайте учётную запись администратора.

```console
docker compose exec web python manage.py createsuperuser
```

Админка доступна по адресу [/admin/](http://localhost:8000/admin/). Команда `docker compose down` останавливает сервисы. Именованный том `pg_data` сохраняет базу между запусками.

## Локальный запуск

Понадобятся Python 3.12 или 3.13 и PostgreSQL. Для запуска только базы через Compose выполните `docker compose up -d db` после создания файлов окружения. Если используете собственный PostgreSQL, создайте базу и пользователя с правом создания таблиц в этой базе, затем укажите их параметры в `.env.local`.

```console
python init_env.py
python -m venv .venv
```

В Windows PowerShell активируйте окружение командой `.\.venv\Scripts\Activate.ps1`, а в Linux или macOS выполните `source .venv/bin/activate`. Затем запустите:

```console
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Скрипт `init_env.py` выполняется один раз. В `.env.local` хост базы по умолчанию — `127.0.0.1`, в `.env.docker` — имя сервиса `db`. Оба файла исключены из Git и Docker-образа. Перечень переменных приведён в `.env.example`.

## Проверка админки

После входа в /admin/ доступны профили, вопросы, ответы, теги и оба вида лайков. Профиль редактируется также на странице пользователя, ответы — на странице вопроса.

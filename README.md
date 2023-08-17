# foodgram-project-react

Foodgram - «Продуктовый помощник». На этом сервисе пользователи могут публиковать рецепты, подписываться на публикации других пользователей, добавлять понравившиеся рецепты в список «Избранное», а перед походом в магазин скачивать сводный список продуктов, необходимых для приготовления одного или нескольких выбранных блюд

Бэйдж, который показывает статус workflow:

# [![Django-app workflow](https://github.com/Katerinair8/yamdb_final/actions/workflows/yamdb_workflow.yml/badge.svg?branch=master)](https://github.com/Katerinair8/yamdb_final/actions/workflows/yamdb_workflow.yml)

# IP сервера:

158.160.58.80

# Как запустить приложения в контейнерах:

Развернуть проект через docker-compose:

```
docker-compose up -d
```

# Выполнить миграции:

```
docker-compose exec web python manage.py migrate
```

# Создать суперпользователя:

```
docker-compose exec web python manage.py createsuperuser
```

# Собрать статику:

```
docker-compose exec web python manage.py collectstatic --no-input
```

### Использованные технологии:

Python 3.7
Django REST Framework 3.13.1
DRF Simple JWT 4.8.0

### Как запустить проект:

Клонировать репозиторий и перейти в него в командной строке:

```
https://github.com/Katerinair8/foodgram-project-react.git
```

Cоздать и активировать виртуальное окружение:

```
python -m venv venv
```
В зависимости от операционной системы
```
source venv/Scripts/activate или source venv/bin/activate
```

Установить зависимости из файла requirements.txt:

```
python -m pip install --upgrade pip
```

```
pip install -r requirements.txt
```

Создать и выполнить миграции:

```
python manage.py makemigrations
```

```
python manage.py migrate
```

Запустить проект:

```
python manage.py runserver

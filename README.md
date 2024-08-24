# **Проект Foodgram**
Данный сервис позволяет публиковать свои рецепты, смотреть рецепты и подписываться на других пользователей, а также добавлять рецепты в корзину для получения списка всех необходимых ингридиентов.

## Использованные технологии

[![Python](https://img.shields.io/badge/-Python-464646?style=flat&logo=Python&logoColor=56C0C0&color=008080)](https://www.python.org/)
[![Django](https://img.shields.io/badge/-Django-464646?style=flat&logo=Django&logoColor=56C0C0&color=008080)](https://www.djangoproject.com/)
[![Django REST Framework](https://img.shields.io/badge/-Django%20REST%20Framework-464646?style=flat&logo=Django%20REST%20Framework&logoColor=56C0C0&color=008080)](https://www.django-rest-framework.org/)
[![PostgreSQL](https://img.shields.io/badge/-PostgreSQL-464646?style=flat&logo=PostgreSQL&logoColor=56C0C0&color=008080)](https://www.postgresql.org/)
[![Nginx](https://img.shields.io/badge/-NGINX-464646?style=flat&logo=NGINX&logoColor=56C0C0&color=008080)](https://nginx.org/ru/)
[![Docker](https://img.shields.io/badge/-Docker-464646?style=flat&logo=Docker&logoColor=56C0C0&color=008080)](https://www.docker.com/)
[![Docker Hub](https://img.shields.io/badge/-Docker%20Hub-464646?style=flat&logo=Docker&logoColor=56C0C0&color=008080)](https://www.docker.com/products/docker-hub)

## Как развернуть проект на сервере:

Первым делом необходимо обновить пакет APT на сервере:

```
sudo apt update
```
```
sudo apt upgrade -y
```

В папку foodgram на сервере создать файл _.env_ и заполнить его своими данными:

```
touch .env
nano .env

POSTGRES_USER=<POSTGRES_USER>
POSTGRES_PASSWORD=<POSTGRES_PASSWORD>
POSTGRES_DB=<POSTGRES_DB>
DB_HOST=<DB_HOST>
DB_PORT=<DB_PORT>
SECRET_KEY=<SECRET_KEY>
DEBUG=<DEBUG>
ALLOWED_HOSTS=<ALLOWED_HOSTS>
```

Установить на сервер Docker и Docker-compose:

```
sudo apt install docker.io
```
```
sudo curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
```
```
sudo chmod +x /usr/local/bin/docker-compose
```

Проверить, что всё установилось правильно:

```
sudo  docker-compose --version
```

## После деплоя:

На сервере собрать docker-compose:

```
sudo docker compose -f docker-compose.production.yml up -d
```

Проверить, запущены ли контейнеры:

```
sudo docker compose -f docker-compose.production.yml ps
```

Если всё сделано правильно, то дальше собрать статику и применить миграции:

```
sudo docker compose -f docker-compose.production.yml exec backend python manage.py collectstatic
```
```
sudo docker compose -f docker-compose.production.yml exec backend cp -r /app/collected_static/. /backend_static/static
```
```
sudo docker compose -f docker-compose.production.yml exec backend python manage.py makemigrations
```
```
sudo docker compose -f docker-compose.production.yml exec backend python manage.py migrate
```

Последний шаг - создать админа. После чего зайти в админ-зону и создать хотя бы 1 тэг и 1 ингридиент:

```
sudo docker compose -f docker-compose.production.yml exec backend python manage.py createsuperuser
```

## Наполнение БД данными:

В файлах проекта подготовлен специальный файл _ingredients.json_
Чтобы заполнить БД:

```
 sudo docker compose -f docker-compose.production.yml exec backend python manage.py loaddata data/ingredients.json
```

## Документация:

http://localhost/api/docs/

## Примеры запросов:

```
http://localhost/api/users/

{
  "email": "vpupkin@yandex.ru",
  "username": "vasya.pupkin",
  "first_name": "Вася",
  "last_name": "Иванов",
  "password": "Qwerty123"
}
```

```
http://localhost/api/recipes/{id}/

{
  "id": 0,
  "tags": [
    {
      "id": 0,
      "name": "Завтрак",
      "slug": "breakfast"
    }
  ],
  "author": {
    "email": "user@example.com",
    "id": 0,
    "username": "string",
    "first_name": "Вася",
    "last_name": "Иванов",
    "is_subscribed": false,
    "avatar": "http://foodgram.example.org/media/users/image.png"
  },
  "ingredients": [
    {
      "id": 0,
      "name": "Картофель отварной",
      "measurement_unit": "г",
      "amount": 1
    }
  ],
  "is_favorited": true,
  "is_in_shopping_cart": true,
  "name": "string",
  "image": "http://foodgram.example.org/media/recipes/images/image.png",
  "text": "string",
  "cooking_time": 1
}
```

## Проект:

http://onlyfood.webhop.me/

## Об Авторе:

[Павлов Никита](https://github.com/jojo3228).
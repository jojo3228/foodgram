h1 **Проект Foodgram** h1
Данный сервис позволяет публиковать свои рецепты, смотреть рецепты и подписываться на других пользователей, а также добавлять рецепты в корзину для получения списка всех необходимых ингридиентов.

h2 Как развернуть проект на сервере:

Первым делом необходимо обновить пакет APT на сервере:

```
sudo apt update
```
```
sudo apt upgrade -y
```

В редакторе nano откройте конфиг Nginx:

```
nano /etc/nginx/sites-enabled/default 
```

И измените настройки location в секции server:

```
server {
    server_name <your_server_name>;
    root /var/www/foodgram/;
    location / {
      proxy_set_header Host $http_host;
      proxy_pass http://127.0.0.1:<you_working_port>;
      client_max_body_size 20M;
    }
```

Проверьте, что конфигурацию конфига написана правильно. Если да, то перезагрузите его:

```
sudo nginx -t
```
```
sudo service nginx reload
```

В папку foodgram на сервере скопировать файл _docker-compose.production.yml_
Также в папке создать файл _.env_ и заполнить его своими данными:

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

h2 После деплоя: h2

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
sudo docker-compose -f docker-compose.production.yml exec backend python manage.py createsuperuser
```

h2 Проект: h2

http://onlyfood.webhop.me/

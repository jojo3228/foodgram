python manage.py makemigrations --no-input
python manage.py migrate --no-input
python manage.py collectstatic --no-input
python manage.py loaddata data/ingredients.json --no-input
gunicorn --bind 0.0.0.0:8000 backend.wsgi
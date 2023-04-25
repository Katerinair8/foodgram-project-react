python manage.py makemigrations
python manage.py migrate
python manage.py collectstatic
python manage.py loaddata data/ingredients.json
python manage.py loaddata data/tags.json
python manage.py createsuperuser
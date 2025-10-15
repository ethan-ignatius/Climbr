# Climbr
An app where individuals can post, view, and rate outdoor climbs. 


Delete db.sqlite3 anf run the following command to load data and run server

python manage.py makemigrations
python manage.py migrate
python manage.py loaddata routes_sample.json
python manage.py runserver

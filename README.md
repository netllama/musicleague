# musicleague

A python Flask based app for hosting music leagues, using Youtube links to reference music tracks in league submissions.

## Requirements

* python-3.x (tested with 3.10 & 3.11)
* PostgreSQL (tested with 12.x)
* A web server (tested with Apache-2.4.57)

## Initial setup

1. Checkout the git repository locally.
2. Create a local python virtual environment: `python -m venv musicleague_virtenv`
    - Enter the new virtual env: `source musicleague_virtenv/bin/activate`
3. Install requirements from the checked out git repo using pip: `pip install -r requirements.txt`
4. In the top level of the git repo, create the file `.flaskenv` and populate it with the following variables:
```
FLASK_APP=musicleague
PG_USER=
PG_PASSWD=
SECRET_KEY=
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=1
MAIL_USERNAME=
MAIL_PASSWORD=
ADMIN_EMAIL=
YT_API_KEY=
```
5. `FLASK_DEBUG=0 flask run`

This project is **not** associated and **not** affiliated with 'Music League' ( https://musicleague.com ) in any way.

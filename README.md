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
4. Create a new database for the league, preferably using a dedicated (new) database user.
    - You can create the schema using the `ml.sql` file included in the git repo, with `psql`: `psql -f ml.sql`
4. In the top level of the git repo, create the file `.flaskenv` and populate it with the following variables:
```
FLASK_APP=musicleague   # Can be set to any string, but the default provided here normally makes sense.
PG_USER=                # The postgres database user
PG_PASSWD=              # The postgres database user's password
DB_NAME=                # The name of the postgres database that you wish to use
SECRET_KEY=             # Prevents CSRF abuse for web forms. Should be a random generated, alphanumeric string at least 60 characters in length.
MAIL_SERVER=            # The hostname of your SMTP mail server.
MAIL_PORT=              # Port number required to connect to the SMTP mail server.
MAIL_USE_TLS=           # Set to 1 if your SMTP mail server requires TLS for connections.
MAIL_USERNAME=          # Email account username
MAIL_PASSWORD=          # Email account's password
ADMIN_EMAIL=            # The music league admin's email address (should be associated with MAIL_USERNAME )
YT_API_KEY=             # Required for processing youtube video URLs. This API key which grants access to Google's Youtube service ( also see https://developers.google.com/youtube/registering_an_application ).
APP_WEB_PATH=           # Set to a a path value if you want to host the music league from a path other than the top level ( http://example.com/ ) such as 'ml' ( http://example.com/ml ). Otherwise leave unset.
PREFERRED_URL_SCHEME=   # either http or https, based on whether you are using an SSL cert for your web server
SERVER_NAME=            # default hostname of the server (eg. 'music.example.com')
SLACK_BOT_TOKEN=        # Slack OAuth API token, needed to send notices to a slack channel
SLACK_CHANNEL=          # name of Slack channel to send notices. Must start with # symbol.
```
5. Start up the app locally by running `FLASK_DEBUG=0 flask run` and you should be able to connect to http://127.0.0.1:5000 to test drive everything.
6. Once you are confident that everything is working as expected, move the app behind a real, production quality, secure web server (nginx, apache, etc) and run as some sort of WSGI service (such as gunicorn).
    - Do not expose the app to the internet using the developer Flask built-in web server (port 5000 from the previous step), as it cannot handle concurrent requests, and is insecure.
    - If you want to use gunicorn, then add it to the virtenv with `pip install gunicorn` and run as `gunicorn -b localhost:5000 -w 1 run:app`
        - Note this will run via port 5000 on localhost, and only spawn a single thread. Adjust as appropriate for your needs and environment.
7. If you wish to generate emails to users when each music league round begins, voting starts and voting ends, then create a cronjob on the server which calls `send_notices.py`.
    - Optionally, if you want to send the notices to a slack channel, you must populate both SLACK_BOT_TOKEN and SLACK_CHANNEL variables inside of your `.flaskenv` file.
    - The cronjob job should run using the python inside of your music league virtual environemnt (not the external, OS level python binary that may have shipped with the OS). For example:
        - `/home/netllama/stuff/flask/bin/python send_noticess.py`
    - Running every 10 or 15 minutes should be sufficient, but there is no requirement that it run with a specific frequency:
        - `*/10  *   *   *   *   /home/netllama/stuff/flask/bin/python send_notices.py`

This project is **not** associated and **not** affiliated with 'Music League' ( https://musicleague.com ) in any way.

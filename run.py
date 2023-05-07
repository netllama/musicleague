# used to load the app via an WSGI server as 'run:app'
import os

from dotenv import load_dotenv
from musicleague import app


load_dotenv('.flaskenv')

if __name__ == '__main__':
    app.run(load_dotenv=True)

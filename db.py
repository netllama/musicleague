import os

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import sessionmaker

DB_USER = os.environ.get('PG_USER')
DB_PASSWD = os.environ.get('PG_PASSWD')
DB_URL = f'postgresql://{DB_USER}:{DB_PASSWD}@localhost:5432/ml'
SQLALCHEMY_DATABASE_URI = DB_URL

#class User(db.Model):
#    """User mgmt class."""




def get_engine():
    """Get DB engine."""
    engine = create_engine(DB_URL, pool_size=10)
    return engine


def get_session():
    """Get DB session."""
    engine = get_engine()
    session = sessionmaker(bind=engine)()
    return session


def get_users(session):
    """Get users table model."""
    base = automap_base()
    base.prepare(autoload_with=engine)
    users = base.classes.users
    return users


def get_leagues(session):
    """Get users table model."""
    base = automap_base()
    base.prepare(autoload_with=engine)
    leagues = base.classes.leagues
    return leagues


def select_tbl_data(tbl_name, session, app):
    """Select all rows from specified table."""
    db = SQLAlchemy()
    db.init_app(app)
    

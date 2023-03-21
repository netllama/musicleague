import os

from flask import Flask
from sqlalchemy import create_engine
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import sessionmaker


#class User(db.Model):
#    """User mgmt class."""
    

def get_engine():
    """Get DB engine."""
    passwd = os.environ.get('PG_PASSWD')
    url = f'postgresql://ml:{passwd}@localhost:5432/ml'
    engine = create_engine(url, pool_size=10)
    return engine


def get_session():
    """Get DB session."""
    engine = get_engine()
    session = sessionmaker(bind=engine)()
    return session

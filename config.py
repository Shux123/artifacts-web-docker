from app.all_requests import get_account_name
import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
            'sqlite:///' + os.path.join(basedir, 'data.sqlite')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.environ.get('SECRET_KEY')
    Y_MIN_MAX = {'y_min': -5, 'y_max': 22,}
    ARTIFACTS_ACCOUNT = get_account_name()
    CELERY = dict(
        broker_url="redis://redis:6379/0",
        result_backend="redis://redis:6379/0",
    )
    NAMES = []
    EVENTS = []

config = Config()
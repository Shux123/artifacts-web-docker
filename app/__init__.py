from flask import Flask
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from config import config
from flask_migrate import Migrate
from redis import Redis
from celery import Celery, Task

def celery_init_app(app):
    class FlaskTask(Task):
        def __call__(self, *args: object, **kwargs: object) -> object:
            with app.app_context():
                return self.run(*args, **kwargs)

    celery_app = Celery(app.name, task_cls=FlaskTask)
    celery_app.config_from_object(app.config["CELERY"])
    celery_app.set_default()
    app.extensions["celery"] = celery_app
    return celery_app

bootstrap = Bootstrap5()
db = SQLAlchemy()
migrate = Migrate()
r = Redis(host='redis', port=6379, db=1)


def create_app():
    app = Flask(__name__)
    app.config.from_object(config)

    bootstrap.init_app(app)
    db.init_app(app)
    migrate.init_app(app, db)
    celery_init_app(app)

    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)
    from .char import char as char_blueprint
    app.register_blueprint(char_blueprint)

    return app

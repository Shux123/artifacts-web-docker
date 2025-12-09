from flask import Blueprint

char = Blueprint('char', __name__)

from . import views
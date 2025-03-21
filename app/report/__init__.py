from flask import Blueprint

report = Blueprint('report', __name__, 
                  template_folder='templates',
                  static_folder='static',
                  static_url_path='/report/static')

from . import generator

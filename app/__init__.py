from app.controller import datauser
from app.controller import eadmin
from app.controller import tadmin
from app.controller import frontend
from app.controller import log
from app.controller import oconvener
from app.controller import pay
from app.controller import seadmin
from app.controller import user
from flask import Flask


def register_blueprints(app):
  app.register_blueprint(user.userBP, url_prefix='/user')
  app.register_blueprint(frontend.frontendBP, url_prefix='/frontend')
  app.register_blueprint(datauser.datauserBP, url_prefix='/datauser')
  app.register_blueprint(oconvener.oconvenerBP, url_prefix='/oconvener')
  app.register_blueprint(pay.payBP, url_prefix='/pay')
  app.register_blueprint(log.logBP,url_prefix='/log')
  app.register_blueprint(eadmin.eadminBP, url_prefix='/eadmin')
  app.register_blueprint(tadmin.tadminBP, url_prefix='/tadmin')
  app.register_blueprint(seadmin.seadminBP, url_prefix='/seadmin')
def register_plugin(app):
  from app.models.base import db
  db.init_app(app)
  with app.app_context():
    db.create_all()


def create_app():
  app = Flask(__name__,
              template_folder='templates',
              static_folder='static')
  app.config.from_object('app.config.secure')
  register_blueprints(app)
  register_plugin(app)
  return app

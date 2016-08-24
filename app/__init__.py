import os
from flask import Flask
from flask.ext.login import LoginManager
from flask_restful import Api
from datetime import timedelta
import cloudant

app = Flask(__name__)
app.config.from_object('config')

#logging 
if app.debug is not True:   
    import logging
    from logging.handlers import RotatingFileHandler
    file_handler = RotatingFileHandler('ml-service.log', maxBytes=1024 * 1024 * 100, backupCount=20)
    file_handler.setLevel(logging.WARNING)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(formatter)
    app.logger.setLevel(logging.WARNING)
    app.logger.addHandler(file_handler)     

#equip this app with Restful-API support
api = Api(app)


#connect to Cloudant database
db_account = cloudant.Account(app.config['CLOUDANT_USER'])
login = db_account.login(app.config['CLOUDANT_USER'], app.config['CLOUDANT_PWD'])

#equip this app with login manager
lm = LoginManager()
lm.init_app(app)
lm.login_view = 'login'
app.permanent_session_lifetime = timedelta(minutes=app.config['SESSION_TIMEOUT_MINUTES'])

from app import views, user, RESTful_APIs
import os
basedir = os.path.abspath(os.path.dirname(__file__))

SQLALCHEMY_DATABASE_URI = 'sqlite:///'+ os.path.join(basedir, 'app.db')
SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'db_repository')
SQLALCHEMY_TRACK_MODIFICATIONS = True

#CSRF used for SWAGGER JSON file
WTF_CSRF_ENABLED = True

#sercret key used for generating Restful API access key
SECRET_KEY = 'Torsten'

#Cloudant Database Credentials
CLOUDANT_USER = 'fac72456-4c6a-4410-8bab-f9ed19270c52-bluemix'
CLOUDANT_PWD = '58d008a552549010938b5536d2a13c9aa28376b6fb9d48403ba2d28c6e586ee3'

#Browser session settings
SESSION_TIMEOUT_MINUTES = 15
from flask.ext.wtf import Form
from flask.ext.wtf.html5 import EmailField
from wtforms import PasswordField, BooleanField, StringField
from wtforms.validators import DataRequired


class LoginForm(Form):
    username = StringField('username', validators=[DataRequired()])
    password = PasswordField('password', validators=[DataRequired()])
    remember_me = BooleanField('remember_me', default=False)

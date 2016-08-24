from flask import render_template, flash, redirect, abort, session, url_for, request, g, send_from_directory, jsonify
from flask.ext.login import login_user, logout_user, current_user, login_required
from app import app, lm
from .forms import LoginForm
from .user import User
import db_operations as dbop
from flask.ext.cors import CORS, cross_origin
import os 
import sys
import traceback
import cf_apis as cf
import dashdb_operations as dashdb
import xml.etree.ElementTree as ET
#from threading import Thread
from time import gmtime, strftime
#from RESTful_APIs import access_key_required
import exceptions as e
#user_loader is required for Flask-login extension

# #error handler to log exceptions
# @app.errorhandler(Exception)
# def internal_error(error):
# 	exce_value = sys.exc_info()[1]
# 	info = str(error.__class__.__name__) + ': ' + str(exce_value)
# 	app.logger.error(info)

@lm.user_loader
def load_user(id):
	return User.retrieve_user(id)

@app.before_request
def before_request():
	g.user = current_user
	session.permanent = True
	session.modified = True

@app.route('/catalog')
@login_required
def catalog():
	return render_template('catalog.html',
						   title='catalog', user=g.user)

@app.route('/')
def intro():
	return render_template('intro.html',
						   title='Machine Learning Service')

@app.route('/login', methods=['GET', 'POST'])
def login():
	if g.user is not None and g.user.is_authenticated:
		#if user is authenticated
		if not g.user.is_setup:
			#redirect to /setup page if the user did not setup
			return redirect(url_for('setup'))
		else:
			#otherwise redirect to /catalog
			return redirect(url_for('catalog'))
	#this form is used for logging in user
	form = LoginForm()
	if form.validate_on_submit():
		#if user clicks the 'login' button on login page
		session['remember_me'] = form.remember_me.data
		try_login_username, try_login_password = form.username.data, form.password.data
		#try to authenticate this username/password by retrieving a token from Cloud Foundry
		#If a token is issued from Cloud Foundry, it means this account is authenticated
		#This token is used to interact with Cloud Foundry 
		auth_and_token = User.get_token(try_login_username, try_login_password)
		if auth_and_token:
			try:
				#if authentication succeeds, firstly try to retrieve this user from database
				user = User.retrieve_user(username=try_login_username)
			except e.UserNotExistsError as error:
				#if the user is not in database, create a new user
				user = User(username=try_login_username, token=auth_and_token)
				user.generate_access_key()
			#refresh the old token by this newly generated token
			#or store this token for  new user
			user.token = auth_and_token
			user.commit()
			remember_me = False
			if 'remember_me' in session:
				remember_me = session['remember_me']
				session.pop('remember_me', None)
			login_user(user, remember=remember_me)
			if user.is_setup:
				#if the user set up his/her catalog before, redirect to /catalog
				return redirect(request.args.get('next') or url_for('catalog'))
			else:
				#else, redirect to /setup page
				return redirect(url_for('setup'))
		else:
			#if Cloud Foundry refuse to issue a token,
			#it means this username/password is not valid
			flash('Invalid login. Please try again.')
			return redirect(url_for('login'))
	return render_template('login.html',
						   title='Sign In',
						   form=form)
	
@app.route('/setup', methods=['GET', 'POST'])
@login_required
def setup():
	user = g.user
	if request.method == 'POST':
		print request.get_json()
		data = request.get_json()
		try:
			#try to create app and services and bind them
			user.set_up(data['region'], data['org_name'], data['org_guid'], 
						data['space_name'], data['space_guid'], 
						data['dashdb_guid'], data['dashdb_name'])
			#delploy the sample models and retrieve all exsiting
			#models in bound services. Then store them to database
			user.deploy_sample_and_get_all_models(data['samples'])
			user.is_setup = True
			user.commit()
			return jsonify(**{'message': 'setup successfully'})
		except Exception as error:
			if 'msg' in error.__dict__:
				#if 'msg' is one of the attributes of the error,
				#it means this is an error defined this application
				info = 'Setting up failed: '+str(error.__class__.__name__)+error.msg
				app.logger.error(info)
				return info, 500
			else:
				exc_value = sys.exc_info()[1]
				info = "Setting up failed with unexpected error: "+\
					   str(error.__class__.__name__)+", "+str(exc_value)
				app.logger.error(info)
				#raise error
				return info, 500
	return render_template('setup.html', user=g.user)

@app.route('/logout')
def logout():
	logout_user()
	return redirect(url_for('catalog'))

@app.route('/model')
@login_required
def model():
	try:
		user = g.user
		#get request arguments
		args = request.args
		model_name = args['name']
		model = user.retrieve_model(model_name)
		if 'to' in args and args['to'] == 'metadata':
			return render_template('metadata.html', model_name=model_name, type=model.model_type, 
									metadata=model.input_metadata, output_metadata=model.output_metadata)
		elif 'to' in args and args['to'] == 'score':
			return render_template('score.html', model_name=model_name, 
									metadata=model.input_metadata, output_metadata=model.output_metadata)
		elif 'to' in args and args['to'] == 'refresh':
			return render_template('refresh.html', type=model.model_type)
		elif 'to' in args and args['to'] == 'api':
			return render_template('api.html')
		elif 'to' in args and args['to'] == 'history':
			return render_template('history.html')
		elif 'to' in args and args['to'] == 'overview':
			return render_template('overview.html', model=model)
		elif 'to' in args and args['to'] == 'visualization':
			filename='./outputs/'+user.username+model.model_name+'.jpg'
			if model.model_type == 'DashDB In-database Model':
				is_visualized = model.is_visualized
			else:
				is_visualized = False
			return render_template('visualization.html', pic_exist=is_visualized, filename=filename)
		else:
			#if jumping to which section is not defined, 
			#redirect to overview page
			all_models = user.list_models()
			models_except_current = [model_each['model_name'] for model_each \
									 in all_models if model_each['model_name'] != model_name]
			if 'page' in args:
				page = args['page']
			else:
				page = 'overview'
			return render_template('model.html', user=g.user, model=model, 
									models=models_except_current, page=page)
	except e.ModelNotExistsError as error:
		abort(404)
	except Exception as error:
		if 'msg' in error.__dict__:
			#if 'msg' is one of the attributes of the error,
			#it means this is an error defined this application
			info = 'error: '+str(error.__class__.__name__+error.msg)
			app.logger.error(info)
			return info, 500
		else:
			exc_value = sys.exc_info()[1]
			info = "Unexpected error: "+\
				   str(error.__class__.__name__)+", "+str(exc_value)
			app.logger.error(info)
			#raise error
			return info, 500


@app.route('/new-model')
@login_required
def new_model():
	return render_template('add_new_model.html', user=g.user)




"""
### Since retrieving metadata requires a lot of time, we use another thread to finish it.
### By this way, the setup process should be faster.
def async(f):
	def wrapper(*args, **kwargs):
		thr = Thread(target=f, args=args, kwargs=kwargs)
		thr.start()
	return wrapper

@async
def setup_user_model_metadata(app, spss_models, dashdb_models, user):
	#app_context has to be maintained, otherwise db connection will be lost
	with app.app_context():

		for dashdb_model in dashdb_models:
"""

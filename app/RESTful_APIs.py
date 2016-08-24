from flask import render_template, flash, redirect, session, url_for, request, g, jsonify, abort, make_response, send_from_directory
from flask_restful import Resource, reqparse
from flask.ext.login import login_user, logout_user, current_user, login_required
from app import app, api, lm
from app.model import Model
from flask.ext.cors import CORS, cross_origin
from user import User
import db_operations as dbop
import cf_apis as cf
from time import gmtime, strftime
from functools import wraps
import dashdb_operations as dashdb
import exceptions as e
from werkzeug import secure_filename
import sys
import os


def access_key_error_handler(no_access_key=False):
	""" error handler for wrong access key """
	if no_access_key:
		res = make_response('{"error":"No access key provided."}')
	else:
		res = make_response('{"error":"Unauthorized Access"}')
	res.status_code = 401
	#Since we don't need browser prompting a login window,
	# "Key" is used as scheme instead of "Basic"
	res.headers['WWW-Authenticate'] = 'Key realm="mlservice"'
	return res


def access_key_required(f):
	"""decorator for Restful APIs which need access key."""
	@wraps(f)
	def decorated(*args, **kwargs):
		print request.args
		in_args = request.args
		# We need to ignore authentication headers for OPTIONS to avoid
		# unwanted interactions with CORS.
		# Chrome and Firefox issue a preflight OPTIONS request to check
		# Access-Control-* headers, and will fail if it returns 401.
		if request.method != 'OPTIONS':
			if not 'access_key' in in_args:
				return access_key_error_handler(no_access_key=True)
			access_key = in_args['access_key']
			print "access_key"+access_key
			user = User.verify_access_key(access_key)
			# pass the user to g global, so that it can be used during request
			g.user = user
			print user
			if not user:
				return access_key_error_handler()
		return f(*args, **kwargs)
	return decorated

class generate_access_key(Resource):
	"""Generate access key for Restful APIs"""
	@access_key_required
	def get(self):
		access_key = g.user.generate_access_key()
		return jsonify({'access_key': access_key.decode('ascii')})

class send_pic(Resource):
	"""Send model visualization result form disk."""
	@cross_origin()
	def get(self, filename):
		current_dir = os.getcwd()
		return send_from_directory(os.path.join(current_dir, 'outputs'), filename)

class bluemix_orgs(Resource):
	"""
	This API is used to retrieve user's Bulemix organizations 
	in a region. 

	status_code:
	-------
	200
		response body is organizations as options of html select.
	500
		response body is error message
	"""
	@access_key_required
	def get(self):
		try:
			parser = reqparse.RequestParser()
			parser.add_argument('region', type=str, location='args', 
										  help='region where the bluemix account locates')
			args = parser.parse_args()
			orgs_raw = cf.get_orgs(args['region'], access_token = g.user.token)
			orgs = [(org['name'], org['guid']) for org in orgs_raw]
			return render_template('options_with_value.html', options=orgs)
		except Exception as error:
			if 'msg' in error.__dict__:
				#if 'msg' is one of the attributes of the error,
				#it means this is an error defined this application
				info = 'Getting bluemix organizations failed: '+\
									  str(error.__class__.__name__+error.msg)
				app.logger.error(info)
				return make_response(info, 500)
			else:
				exc_value = sys.exc_info()[1]
				#raise error
				info = "Getting bluemix organizations failed with unexpected error: "+\
					   str(error.__class__.__name__)+", "+str(exc_value)
				app.logger.error(info)
				return make_response(info, 500)


class bluemix_spaces(Resource):
	"""
	This API is used to retrieve user's Bulemix spaces in a given organization. 

	status_code:
	-------
	200
		response body is spaces as options of html select.
	500
		response body is error message
	"""
	@access_key_required
	def get(self):
		try:
			parser = reqparse.RequestParser()
			parser.add_argument('region', type=str, location='args', help='region where the bluemix account locates')
			parser.add_argument('org', type=str, location='args', help='in which organization you want to list all spaces ')
			args = parser.parse_args()
			spaces_raw = cf.get_spaces(args['region'], args['org'], access_token = g.user.token)
			spaces = [(space['name'], space['guid']) for space in spaces_raw]
			return render_template('options_with_value.html', options=spaces)
		except Exception as error:
			if 'msg' in error.__dict__:
				#if 'msg' is one of the attributes of the error,
				#it means this is an error defined this application
				info = 'Getting bluemix spaces failed: '+\
									  str(error.__class__.__name__+error.msg)
				app.logger.error(info)
				return make_response(info, 500)
			else:
				exc_value = sys.exc_info()[1]
				#raise error
				info = "Getting bluemix spaces failed with unexpected error: "+\
					   str(error.__class__.__name__)+", "+str(exc_value)
				app.logger.error(info)
				return make_response(info, 500)


class instances(Resource):
	"""
	This API is used to retrieve user's service instances in a given region. 

	query_argument:
	-------
	service: str
		the type if service. cloud either be 'dashdb' or 'spss'
	region:
		region where the service instances locate

	status_code:
	-------
	200
		response body is service instances as options of html select.
	500
		response body is error message
	"""
	@access_key_required
	def get(self):
		try:
			parser = reqparse.RequestParser()
			parser.add_argument('service', type=str, location='args', help='service should either be dashdb or spss')
			parser.add_argument('region', type=str, location='args', help='region where the dashDB instances locate')
			args = parser.parse_args()
			if args['service'] == 'dashdb':
				names = cf.get_dashdb_instances_in_region(args['region'], token = g.user.token)
			return render_template('options_with_value.html', options=names)
		except Exception as error:
			if 'msg' in error.__dict__:
				#if 'msg' is one of the attributes of the error,
				#it means this is an error defined this application
				info = 'Getting dashdb instances failed: '+\
									  str(error.__class__.__name__+error.msg)
				app.logger.error(info)
				return make_response(info, 500)
			else:
				exc_value = sys.exc_info()[1]
				#raise error
				info = "Getting dashdb instances failed with unexpected error: "+\
					   str(error.__class__.__name__)+", "+str(exc_value)
				app.logger.error(info)
				return make_response(info, 500)


class get_tables(Resource):
	"""
	Get table names or table details from user's dashdb instance

	query_argument:
	------
	table: str
		if this argument is not empty, it indicates we are trying
		to get table details of this given table name. Otherwise
		we are going to get table names in a schema
	sample: str
		could either be 'true' or 'false'
		if 'true', we are trying to get table names from SAMPLES schema
		Otherwise, we are trying get table names from user's schema
	
	"""
	@access_key_required
	def get(self):
		try:
			user = g.user
			parser = reqparse.RequestParser()
			parser.add_argument('sample', type=str, location='args', help='use sample tables or not')
			parser.add_argument('table', type=str, location='args', help='the table name')
			args = parser.parse_args()
			if args['table']:
				table = dashdb.get_table_details(args['table'], user)
				return table
			elif args['sample'] == 'true':
				table_names = dashdb.get_table_names(is_sample=True, user=user)
				return render_template('options.html',options=table_names)
			elif args['sample'] == 'false':
				table_names = dashdb.get_table_names(is_sample=False, user=user)
				return render_template('options.html',options=table_names)
			else:
				return make_response("Query arguments in URL are not correct", 400)
		except Exception as error:
			if 'msg' in error.__dict__:
				#if 'msg' is one of the attributes of the error,
				#it means this is an error defined this application
				info = 'Getting tables failed: '+\
									  str(error.__class__.__name__+error.msg)
				app.logger.error(info)
				return make_response(info, 500)
			else:
				exc_value = sys.exc_info()[1]
				#raise error
				info = "Getting tables failed with unexpected error: "+\
					   str(error.__class__.__name__)+", "+str(exc_value)
				app.logger.error(info)
				return make_response(info, 500)

class get_columns(Resource):
	"""
	Get column names of a given table from user's dashdb instance

	query_argument:
	------
	table: str
		name of the table we want to retrieve cloumns from
	header: str
		could either given in URL argument or not
		if given, we return the result as table header <th></th>
		Otherwise, we return the result as options <option></option>

	"""
	@access_key_required
	def get(self):
		try:
			user = g.user
			parser = reqparse.RequestParser()
			parser.add_argument('table', type=str, location='args', help='the table name')
			parser.add_argument('header', type=str, location='args', help='return as headers or not')
			args = parser.parse_args()
			if args['table']:
				columns = dashdb.get_column_names(args['table'], user)
			else:
				return "Query arguments in URL are not correct", 400
			if args['header']:
				#argument 'header' is given can cloud be abitrary value
				#return result as headers
				return render_template('headers.html', headers = columns)
			else:
				#otherwise return results as options
				return render_template('options.html',options=columns)
		except Exception as error:
			if 'msg' in error.__dict__:
				#if 'msg' is one of the attributes of the error,
				#it means this is an error defined this application
				info = 'Getting columns failed: '+\
									  str(error.__class__.__name__+error.msg)
				app.logger.error(info)
				return make_response(info, 500)
			else:
				exc_value = sys.exc_info()[1]
				#raise error
				info = "Getting columns failed with unexpected error: "+\
					   str(error.__class__.__name__)+", "+str(exc_value)
				app.logger.error(info)
				return make_response(info, 500)

class swagger(Resource):
	"""
	Get the swagger json file used for Swgger UI
	"""
	@cross_origin()
	@access_key_required
	def get(self, name):
		try:
			user = g.user
			model = user.retrieve_model(name)
			#first check whether the json file exists
			filename = './swagger_json/'+user.username+name+'.json'
			json_exist = os.path.isfile(filename)
			current_dir = os.getcwd()
			if not json_exist:
				#open the template json file
				if model.model_type == 'SPSS Predictive Model':
					#spss model and dashdb model have different json file.
					#the difference is to upload/refresh model
					print 'spss'
					with open (os.path.join(current_dir, 'swagger_json/spss_model.json'), "r") as myfile:
						#replace the modelname and accesskey
						script=myfile.read().replace('<ModelName>', name)
						script=script.replace('<Accesskey>', g.user.access_key)
				else:
					with open (os.path.join(current_dir, 'swagger_json/dashdb_model.json'), "r") as myfile:
						#replace the modelname and accesskey
						script=myfile.read().replace('<ModelName>', name)
						script=script.replace('<Accesskey>', g.user.access_key)
				json_name = os.path.join(current_dir, 'swagger_json/'+user.username+name+'.json')
				#store the json file to folder
				with open(json_name, 'wb') as outfile:
					outfile.write(script)
			return send_from_directory(os.path.join(current_dir, 'swagger_json'), user.username+name+'.json')
		except Exception as error:
			if 'msg' in error.__dict__:
				#if 'msg' is one of the attributes of the error,
				#it means this is an error defined this application
				info = 'Generating JSON file failed: '+\
									  str(error.__class__.__name__+error.msg)
				app.logger.error(info)
				return make_response(info, 500)
			else:
				exc_value = sys.exc_info()[1]
				#raise error
				info = "Generating JSON file failed with unexpected error: "+\
					   str(error.__class__.__name__)+", "+str(exc_value)
				app.logger.error(info)
				return make_response(info, 500)

class score_hint(Resource):
	"""This is the API for getting / changing hint on real time scoring."""
	@access_key_required
	def get(self, name):
		try:
			user = g.user
			#parse query arguments
			parser = reqparse.RequestParser()
			#if response type is html, then return result as html file
			#otherwise return json
			parser.add_argument('response_type', type=str, location='args', 
										help='response type must be json or html')
			args = parser.parse_args()
			model = user.retrieve_model(name)
			hint = model.score_hint
			if args['response_type'] == 'html':
				return render_template('modal.html', id='real-time-score-hint', hint=hint)
			else:
				return {'hint': hint}
		except Exception as error:
			if 'msg' in error.__dict__:
				#if 'msg' is one of the attributes of the error,
				#it means this is an error defined this application
				info = 'Getting hint failed: '+\
									  str(error.__class__.__name__+error.msg)
				app.logger.error(info)
				return make_response(info, 500)
			else:
				exc_value = sys.exc_info()[1]
				#raise error
				info = "Getting hint failed with unexpected error: "+\
					   str(error.__class__.__name__)+", "+str(exc_value)
				app.logger.error(info)
				return make_response(info, 500)
	@access_key_required
	def post(self, name):
		try:
			user = g.user
			#get inputs from user
			inputs = request.get_json()
			model = user.retrieve_model(name)
			model.score_hint = inputs['hint']
			model.commit()
			return {'message': 'succeed to change score hint'}
		except Exception as error:
			if 'msg' in error.__dict__:
				#if 'msg' is one of the attributes of the error,
				#it means this is an error defined this application
				info = 'Chaning hint failed: '+\
									  str(error.__class__.__name__+error.msg)
				app.logger.error(info)
				return make_response(info, 500)
			else:
				exc_value = sys.exc_info()[1]
				#raise error
				info = "Chaning hint failed with unexpected error: "+\
					   str(error.__class__.__name__)+", "+str(exc_value)
				app.logger.error(info)
				return make_response(info, 500)

class description(Resource):
	"""This is the API for getting / changing description on a given model."""
	@access_key_required
	def get(self, name):
		try:
			user = g.user
			#parse query arguments
			parser = reqparse.RequestParser()
			#if response type is html, then return result as html file
			#otherwise return json
			parser.add_argument('response_type', type=str, location='args', 
										help='response type must be json or html')
			args = parser.parse_args()
			model = user.retrieve_model(name)
			descri = model.description
			return {'description': descri}
		except Exception as error:
			if 'msg' in error.__dict__:
				#if 'msg' is one of the attributes of the error,
				#it means this is an error defined this application
				info = 'Getting description failed: '+\
									  str(error.__class__.__name__+error.msg)
				app.logger.error(info)
				return make_response(info, 500)
			else:
				exc_value = sys.exc_info()[1]
				#raise error
				info = "Getting description failed with unexpected error: "+\
					   str(error.__class__.__name__)+", "+str(exc_value)
				app.logger.error(info)
				return make_response(info, 500)
	@access_key_required
	def post(self, name):
		try:
			user = g.user
			#get inputs from user
			inputs = request.get_json()
			model = user.retrieve_model(name)
			model.description = inputs['description']
			model.commit()
			return {'message': 'succeed to change description'}
		except Exception as error:
			if 'msg' in error.__dict__:
				#if 'msg' is one of the attributes of the error,
				#it means this is an error defined this application
				info = 'Chaning description failed: '+\
									  str(error.__class__.__name__+error.msg)
				app.logger.error(info)
				return make_response(info, 500)
			else:
				exc_value = sys.exc_info()[1]
				#raise error
				info = "Chaning description failed with unexpected error: "+\
					   str(error.__class__.__name__)+", "+str(exc_value)
				app.logger.error(info)
				return make_response(info, 500)
			


class get_records(Resource):
	"""
	Get all models in database to dynamically show catalog.
	"""
	@access_key_required
	def get(self):
		try:
			user = g.user
			models = user.list_models(fields=['model_name','model_type', 
										 'creation_time','last_refreshed','source'])
			return models
		except Exception as error:
			if 'msg' in error.__dict__:
				#if 'msg' is one of the attributes of the error,
				#it means this is an error defined this application
				info = 'Getting models from database failed: '+\
									  str(error.__class__.__name__+error.msg)
				app.logger.error(info)
				return make_response(info, 500)
			else:
				exc_value = sys.exc_info()[1]
				#raise error
				info = "Getting models from database failed with unexpected error: "+\
					   str(error.__class__.__name__)+", "+str(exc_value)
				app.logger.error(info)
				return make_response(info, 500)

class get_history(Resource):
	"""
	Get history records of a model from database.
	"""
	@access_key_required
	def get(self, name):
		try:
			user = g.user
			#retrieve the corresponding model 
			model = user.retrieve_model(name)
			#parse query arguments
			parser = reqparse.RequestParser()
			parser.add_argument('type', type=str, location='args', 
										help='type must be refresh or score or visualize')
			parser.add_argument('sort', type=str, location='args', help='sort mush be desc or asc')
			args = parser.parse_args()
			if args['type'] and args['sort']:
				records = model.get_history(behaviour=args['type'], sort=args['sort'])
			elif args['type'] and not args['sort']:
				records = model.get_history(behaviour=args['type'])
			elif not args['type'] and args['sort']:
				records = model.get_history(sort=args['sort'])
			else:
				records = model.get_history()
			return records
		except Exception as error:
			if 'msg' in error.__dict__:
				#if 'msg' is one of the attributes of the error,
				#it means this is an error defined this application
				info = 'Getting history from database failed: '+\
									  str(error.__class__.__name__+error.msg)
				app.logger.error(info)
				return make_response(info, 500)
			else:
				exc_value = sys.exc_info()[1]
				#raise error
				info = "Getting history from database failed with unexpected error: "+\
					   str(error.__class__.__name__)+", "+str(exc_value)
				app.logger.error(info)
				return make_response(info, 500)

class get_history_details(Resource):
	"""
	Get detail information on a specific histroy record
	"""
	@access_key_required
	def get(self, name):
		try:
			user = g.user
			#retrieve the corresponding model 
			model = user.retrieve_model(name)
			parser = reqparse.RequestParser()
			parser.add_argument('type', type=str, location='args', 
										help='type must be refresh or score or visualization')
			parser.add_argument('time', type=str, location='args', 
										help='the time when this history event is recorded')
			parser.add_argument('io', type=str, location='args', 
									  help='input or output table') #take value of 
																	#input or output 
			args = parser.parse_args()
			#retrieve this record from database
			record = dbop.retrieve_history_record(model, args['type'], args['time'])
			#if the record is empty, it means there is history record at this time
			if not record:
				abort(404)
			else:
				history_value = record[0]['value']
			if args['type'] == 'score': 
				if  history_value['score_type'] == 'real_time_score':
					#if real-time-score, we can display
					#input and output directly
					if args['io'] == 'input':
						metadata = model.input_metadata
						records = history_value['input']
					else:
						metadata = model.output_metadata
						records = history_value['output']
					return render_template('history_details.html', header=metadata, 
											records=records, type='score', score_type='real_time_score')
				else:
					#if batch score, we firstly get the table name
					#then retrieve content of the table
					if args['io'] == 'input':
						table_name = history_value['input']
					else:
						table_name = history_value['output']
					table = dashdb.get_table_details(table_name, user)
					header = table[0].keys()
					return render_template('history_details.html', header=header, records=table, 
											type='score', score_type=history_value['score_type'])
			elif args['type'] == 'visualize':
				filename = './outputs/'+user.username+name+'.jpg'
				return render_template('history_details.html', type='visualization', file=filename)
			else:
				#the last possiblity is 'refreshing'
				if model.model_type == 'DashDB In-database Model':
					table_name = history_value.split(' ')[-1]
					table = dashdb.get_table_details(table_name, user)
					header = table[0].keys()
					return render_template('history_details.html', type='refresh',
											 model_type=model.model_type, header=header, records=table)
				else:
					return render_template('history_details.html', type='refresh', 
											model_type=model.model_type, detail=history_value)
		except Exception as error:
			if 'msg' in error.__dict__:
				#if 'msg' is one of the attributes of the error,
				#it means this is an error defined this application
				info = 'Getting history from database failed: '+\
									  str(error.__class__.__name__+error.msg)
				app.logger.error(info)
				return make_response(info, 500)
			else:
				exc_value = sys.exc_info()[1]
				#raise error
				info = "Getting history from database failed with unexpected error: "+\
					   str(error.__class__.__name__)+", "+str(exc_value)
				app.logger.error(info)
				return make_response(info, 500)

class real_time_score(Resource):
	@access_key_required
	def post(self, name):
		try:
			user = g.user
			#retrieve the corresponding model 
			model = user.retrieve_model(name)
			#parse query arguments
			parser = reqparse.RequestParser()
			#if response type is html, then return result as html file
			#otherwise return json
			parser.add_argument('response_type', type=str, location='args', 
										help='response type must be json or html')
			args = parser.parse_args()
			value = request.get_json()
			if args['response_type'] == 'html':
				#transfrom the format of input data
				#so that we can use for scoring 
				headers = value.keys()
				data = []
				for i in range(len(value[headers[0]])):
					every_data = []
					for key in value.keys():
						every_data.append(value[key][i])
					data.append(every_data)
			else:
				headers = value['header']
				data = value['data']
			#score with input data
			result = model.real_time_score(header=headers, data=data)
			if args['response_type'] == 'html':
				return render_template('score_output.html', result=result)
			else:
				return result, 200
		except Exception as error:
			if 'msg' in error.__dict__:
				#if 'msg' is one of the attributes of the error,
				#it means this is an error defined this application
				info = 'Real time scoring failed: '+\
									  str(error.__class__.__name__)+': '+error.msg
				app.logger.error(info)
				return {'error': info}, 500
			else:
				exc_value = sys.exc_info()[1]
				#raise error
				info = "Real time scoring failed with unexpected error: "+\
					   str(error.__class__.__name__)+": "+str(exc_value)
				app.logger.error(info)
				return {'error':info}, 500

class batch_score(Resource):
	@access_key_required
	def post(self, name):
		try:	
			user = g.user
			#retrieve the corresponding model 
			model = user.retrieve_model(name)
			#if model is 'SPSS Predictive Model',
			#return an exception
			if model.model_type == 'SPSS Predictive Model':
				raise e.OperationNotSupportError(msg="SPSS Predictive Model "
												"dose not support batch score.")
			inputs = request.get_json()
			#parse query arguments
			parser = reqparse.RequestParser()
			#if response type is html, then return result as html file
			#otherwise return json
			parser.add_argument('response_type', type=str, location='args', 
										help='response type must be json or html')
			args = parser.parse_args()
			#if 'table_name' is one of the input data,
			#then use this name as output table name
			if 'table_name' in inputs.keys():
				result = model.batch_score(inputs['input_table'],\
									inputs['primary_key'], custom_table_name=inputs['table_name'])
			else:
				result = model.batch_score(inputs['input_table'], inputs['primary_key'])
			if args['response_type'] == 'html':
				#get the output table name from scoring result
				score_table = result['output']
				#retrive the result content from dashDB
				table = dashdb.get_table_details(score_table, user)
				#reformat so that template engine can process
				result_html = {}
				result_html['header'] =  table[0].keys()
				result_html['data'] = [row.values() for row in table]
				return render_template('score_output.html', result=result_html)
			else:
				result['result_table_url'] = url_for('get_tables', _external=True) \
													  +'?table'+result['output']
				return result
		except Exception as error:
			if 'msg' in error.__dict__:
				#if 'msg' is one of the attributes of the error,
				#it means this is an error defined this application
				info = 'Batch scoring failed: '+\
									  str(error.__class__.__name__)+': '+error.msg
				app.logger.error(info)
				return {'error':info}, 500
			else:
				exc_value = sys.exc_info()[1]
				#raise error
				info = "Batch scoring failed with unexpected error: "+\
					   str(error.__class__.__name__)+": "+str(exc_value)
				app.logger.error(info)
				return {'error': info}, 500

class visualize(Resource):
	@access_key_required
	def get(self, name):
		try:	
			user = g.user
			#retrieve the corresponding model 
			model = user.retrieve_model(name)
			#if model is 'SPSS Predictive Model',
			#return an exception
			if model.model_type == 'SPSS Predictive Model':
				raise e.OperationNotSupportError(msg="SPSS Predictive Model "
												"dose not support visualization.")
			if not model.is_visualized:
				model.visualize()
			url = url_for('send_pic', filename=user.username+ \
									 model.model_name+'.jpg', _external=True)
			return {'message':'ok', 'pic_url': url, 'username': user.username}
		except Exception as error:
			if 'msg' in error.__dict__:
				#if 'msg' is one of the attributes of the error,
				#it means this is an error defined this application
				info = 'visualization failed: '+\
									  str(error.__class__.__name__)+': '+error.msg
				app.logger.error(info)
				return {'error':info}, 500
			else:
				exc_value = sys.exc_info()[1]
				#raise error
				info = "visualization failed with unexpected error: "+\
					   str(error.__class__.__name__)+": "+str(exc_value)
				app.logger.error(info)
				return {'error': info}, 500

class metadata(Resource):
	"""
	This is the API for retrieving, deploying, refreshing or deleting model.
	"""
	@access_key_required
	def get(self, name):
		try:
			user = g.user
			#retrieve the corresponding model 
			model = user.retrieve_model(name)
			metadata = {
			'InputMetadata' : model.input_metadata,
			'OutputMetadata': model.output_metadata
			}
  			return metadata
  		except Exception as error:
			if 'msg' in error.__dict__:
				#if 'msg' is one of the attributes of the error,
				#it means this is an error defined this application
				info = 'Getting metadata failed: '+\
									  str(error.__class__.__name__)+': '+error.msg
				app.logger.error(info)
				return {'error':info}, 500
			else:
				exc_value = sys.exc_info()[1]
				#raise error
				info = 'Getting metadata failed: '+\
					   str(error.__class__.__name__)+": "+str(exc_value)
				app.logger.error(info)
				return {'error': info}, 500

class ml_service_model(Resource):
	"""
	This is the API for retrieving, deploying, refreshing or deleting model.
	"""
	@access_key_required
	def get(self, name):
		try:
			user = g.user
			#retrieve the corresponding model 
			model = user.retrieve_model(name)
			model_json = {  
							"description": model.description,
						    "source": model.source,
						    "creation_time": model.creation_time,
						    "type": model.model_type,
						    "last_refreshed": model.last_refreshed,
						    "metadata": url_for('metadata', name=name, _external=True),
						    "real_time_score": url_for('real_time_score', name=name, _external=True),
						    "batch_score": url_for('batch_score', name=name, _external=True),
						    "visualize": url_for('visualize', name=name, _external=True),
						    "history": url_for('get_history', name=name, _external=True)
  						  }
  			return model_json
  		except Exception as error:
			if 'msg' in error.__dict__:
				#if 'msg' is one of the attributes of the error,
				#it means this is an error defined this application
				info = 'Getting model '+name+' failed: '+\
									  str(error.__class__.__name__)+': '+error.msg
				app.logger.error(info)
				return {'error':info}, 500
			else:
				exc_value = sys.exc_info()[1]
				#raise error
				info = 'Getting model '+name+' failed: '+\
					   str(error.__class__.__name__)+": "+str(exc_value)
				app.logger.error(info)
				return {'error': info}, 500
	@access_key_required
	def post(self, name):
		try:
			#get the current user
			user = g.user
			inputs = request.get_json()
			parser = reqparse.RequestParser()
			#if response type is html, then return result as html file
			#otherwise return json
			parser.add_argument('response_type', type=str, location='args', 
										help='response type must be json or html')
			args = parser.parse_args()
			#firstly try to make sure the request body is correct enough to use
			if len(request.files.values()) == 0 and \
			   (inputs and (set(inputs.keys()) != set(['schema', 'input_table', 'target_column', 'primary_key']) \
			             and set(inputs.keys()) != set(['input_table', 'target_column', 'primary_key']))):
				return {'error': 'can not understand input body 1'}, 400
			# try to retrive this model from database
			try:
				#retrieve the corresponding model 
				model = user.retrieve_model(name)
				#if the retrieved model is SPSSModel and there is file uploaded from client
				if model.model_type == 'SPSS Predictive Model' and len(request.files.values()) != 0:
					uploaded_file = request.files.values()[0]
					#refresh this model with uploaded file
					model.refresh(secure_filename(uploaded_file.filename), uploaded_file)
				#if the retrieved model is DashdhModel and there is correct creation information
				elif model.model_type == 'DashDB In-database Model' and \
					inputs and (set(inputs.keys()) == set(['schema', 'input_table', 'target_column', 'primary_key']) \
			                 or set(inputs.keys()) == set(['input_table', 'target_column', 'primary_key'])):
					if 'schema' in inputs.keys():
						input_table = inputs['schema'] + '.' + inputs['input_table']
					else:
						input_table = inputs['input_table']
					model.refresh(input_table, inputs['target_column'], 
								  inputs['primary_key'], False)
				else:
					return {'error': 'can not understand input body 2'}, 400
				if args['response_type'] == 'html':
					return render_template('modal_alert.html', id="add-new-model-alert",
						info='Model has been refreshed. Click the button back to Catalog',
						jump_to='/catalog')
				else:
					return {'message' : model.model_type+' '+name+' has been successfully refreshed.',
							'url': url_for('ml_service_model', name=name, _external=True)}
			#if model does not exist in database,
			#create a model from input
			except e.ModelNotExistsError:
				if len(request.files.values()) != 0:
					uploaded_file = request.files.values()[0]
					#create a new spss model object
					model = Model.create_spss_model(name, user, secure_filename(uploaded_file.filename), uploaded_file)
				elif set(inputs.keys()) == set(['schema', 'input_table', 'target_column', 'primary_key']) \
						 or set(inputs.keys()) == set(['input_table', 'target_column', 'primary_key']):
					if 'schema' in inputs.keys():
						input_table = inputs['schema'] + '.' +inputs['input_table']
					else:
						input_table = inputs['input_table']
					model = Model.create_dashdb_model(name, user, input_table, inputs['target_column'], 
								  		inputs['primary_key'], is_sample=False)
				else:
					return {'error': 'can not understand input body 3'}, 400
				#after the model is created, retrieve their metadata
				model.retrieve_metadata()
				#finally store this model to database by committing
				model.commit()
				if args['response_type'] == 'html':
					return render_template('modal_alert.html', id="add-new-model-alert",
									info='Model has been created. Click the button back to Catalog',
									jump_to='/catalog')
				else:
					return {'message' : model.model_type+' '+name+' has been successfully created.',
							'url': url_for('ml_service_model', name=name, _external=True)}
		except Exception as error:
			if 'msg' in error.__dict__:
				#if 'msg' is one of the attributes of the error,
				#it means this is an error defined this application
				info = 'Deploying/refreshing model '+name+' failed: '+\
									  str(error.__class__.__name__)+': '+error.msg
				app.logger.error(info)
				return {'error':info}, 500
			else:
				exc_value = sys.exc_info()[1]
				#raise error
				info = 'Deploying/refreshing model '+name+' failed: '+\
					   str(error.__class__.__name__)+": "+str(exc_value)
				app.logger.error(info)
				return {'error': info}, 500
	@access_key_required
	def delete(self, name):
		try:
			user = g.user
			#retrieve the corresponding model 
			model = user.retrieve_model(name)
			model.delete()
			return {'message': model.model_type+' '+name+' has been successfully deleted.'}
		except Exception as error:
			if 'msg' in error.__dict__:
				#if 'msg' is one of the attributes of the error,
				#it means this is an error defined this application
				info = 'Deleting model '+name+' failed: '+\
									  str(error.__class__.__name__)+': '+error.msg
				app.logger.error(info)
				return {'error':info}, 500
			else:
				exc_value = sys.exc_info()[1]
				#raise error
				info = 'Deleting model '+name+' failed: '+\
					   str(error.__class__.__name__)+": "+str(exc_value)
				app.logger.error(info)
				return {'error': info}, 500




api.add_resource(generate_access_key, '/get-access-key')   
api.add_resource(bluemix_orgs, '/orgs')
api.add_resource(bluemix_spaces, '/spaces')
api.add_resource(instances, '/instances')  
api.add_resource(get_tables, '/tables')    
api.add_resource(get_columns, '/columns') 
api.add_resource(get_records, '/records')  
api.add_resource(send_pic,'/outputs/<string:filename>')
api.add_resource(ml_service_model, '/api/<string:name>')
api.add_resource(description, '/api/<string:name>/description')
api.add_resource(score_hint, '/api/<string:name>/hint')
api.add_resource(swagger,'/api/<string:name>/swagger')
api.add_resource(get_history_details, '/<string:name>/history/details')  
api.add_resource(get_history, '/api/<string:name>/history')  
api.add_resource(real_time_score, '/api/<string:name>/real_time_score')
api.add_resource(batch_score, '/api/<string:name>/batch_score')
api.add_resource(visualize, '/api/<string:name>/visualize')
api.add_resource(metadata, '/api/<string:name>/metadata')

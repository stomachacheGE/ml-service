
import cf_apis as cf
from itsdangerous import JSONWebSignatureSerializer, BadSignature
import model
import db_operations as dbop
import dashdb_operations as dashdb
import sys
import exceptions as e

class User(object):
	"""This is the user class for the application."""

	def __init__(self, username, token, access_key=None, region=None,
				organization_guid=None, organization_name=None,
				 space_guid=None, space_name=None, dashDB_instance=None,
				dashDB_service_address=None, dashDB_service_user=None,
				 dashDB_service_pwd=None, predictive_analytics_instance=None,
				predictive_analytics_url=None,predictive_analytics_access_key=None,
				is_setup=False, **kwargs):
		if '_id' in kwargs:
			self._id = kwargs['_id']
		else:
			self._id = username
		self.username = username
		self.token = token
		self.access_key = access_key
		self.region = region
		self.organization_guid = organization_guid
		self.organization_name = organization_name
		self.space_guid = space_guid
		self.space_name = space_name
		self.dashDB_service_address = dashDB_service_address
		self.dashDB_service_user = dashDB_service_user
		self.dashDB_service_pwd = dashDB_service_pwd
		self.predictive_analytics_url = predictive_analytics_url
		self.predictive_analytics_access_key = predictive_analytics_access_key
		self.is_setup = is_setup
		self.dashDB_instance = dashDB_instance
		self.predictive_analytics_instance = predictive_analytics_instance
		for key, value in kwargs.items():
			setattr(self, key, value)


	@property
	def is_authenticated(self):
		return True

	@property
	def is_active(self):
		return True

	@property
	def is_anonymous(self):
		return False

	def commit(self):
		"""
		Create/Refresh a user in remote Cloudant 'model_info_db' database.

		Raises:
		-------
		UnknowDatabaseError 
		"""
		#firstly, get all variables and values of this model
		content = self.__dict__.copy()  
		#if '_rev' is one of the variables of this model instance,
		#it means this user is retrived from database. 
		#We are actually going to update the model document in database
		#instead of creating a new user document.
		res = dbop.update_create_user_in_database(self._id, content)    
		self._id = res['id']
		self._rev = res['rev']

	def get_id(self):
		return unicode(self.username)

	def generate_access_key(self):
		"""Generate access key used for Restful API user authentication."""
		from app import app
		s = JSONWebSignatureSerializer(app.config['SECRET_KEY'])
		access_key = s.dumps({'username': self.username}) 
		self.access_key = access_key

	def set_up(self, region, org_name, org_guid, space_name, space_guid, dashdb_guid=None, dashdb_name=None):
		try:
			#try to create app and services and bind them
			if dashdb_name:
				#if 'dashdb_name' is specified by user,
				#then we do not have to create a new dashdb instance.
				#we only need to create an app with name 'ML*SERVICE' 
				#and a new predictive analytics service instance and bind them.
				spss_credentials = cf.create_app_and_bind_services(region, 'ML*SERVICE', space_guid, 
																	self.token, dashdb=False)['Predictive Analytics']
				#However, we still have to retrieve Dashdb instance credentials
				dashdb_credentials = cf.get_dashdb_credentials(region, dashdb_guid, self.token)
				#store the name of bound services
				self.dashDB_instance = dashdb_name
				self.predictive_analytics_instance = 'ML*SERVICE-PA-DONT-DELETE'
			else:
				#if 'dashdb_name' is not provided,
				#we create a new dashdb instance and bind it with 'ML*SERVICE' app
				credentials = cf.create_app_and_bind_services(region, 
															  'ML*SERVICE',space_guid, self.token, dashdb=True)
				spss_credentials = credentials['Predictive Analytics']
				dashdb_credentials =  credentials['dashDB']
				#store the name of bound services
				self.dashDB_instance = 'ML*SERVICE-DASHDB-DONT-DELETE'
				self.predictive_analytics_instance = 'ML*SERVICE-PA-DONT-DELETE'
			#if setup app and services succesfully, store the relevant infomation
			print spss_credentials
			print dashdb_credentials
			self.region = region
			self.organization_name = org_name
			self.organization_guid = org_guid
			self.space_name = space_name
			self.space_guid = space_guid
			self.dashDB_service_address = dashdb_credentials[0]
			self.dashDB_service_user = dashdb_credentials[1]
			self.dashDB_service_pwd = dashdb_credentials[2]
			self.predictive_analytics_url = spss_credentials[0]
			self.predictive_analytics_access_key = spss_credentials[1]
		except e.UnknownCloudFoundryError as error:
			raise e.Error(msg='Create app/services failed: '+error.msg)

	def deploy_sample_and_get_all_models(self, sample_model_names):
		"""
		Deploy sample models to service instances and retrieve models from them.
		This method is used when user sets up their catalog.

		Params:
		-----
		sample_model_names: list
			This list contains zero or any number of the following sample modes:
				'SAMPLE_CUSTOMER', 'SAMPLE_DRUG', 'SAMPLE_CHURN', 'SAMPLE_ACQUISITION'
		"""
		models = []
		try:
			#first try to deploy all the sample models the user specified
			if 'churn' in sample_model_names:
				churn = model.Model.create_dashdb_model('SAMPLE_CHURN', self, 
												  'CUSTOMER_CHURN', 'CENSOR', 'CUST_ID',True)
				models.append(churn)
			if 'acquisition' in sample_model_names:
				acqui = model.Model.create_dashdb_model('SAMPLE_ACQUISITION', self, 
												  'CUSTOMER_ACQUISITION', 'ACQUIRED', 'CUST_ID',True)	
				models.append(acqui)
			if 'drug' in sample_model_names:
				path = './app/sample_models/Drug.str'
				with open (path, "rb") as str_file:
					drug = model.Model.create_spss_model('SAMPLE_DRUG', self, 'Drug.str', str_file)
					models.append(drug)
			if 'customer' in sample_model_names:
				path = './app/sample_models/catalog_timeseries.str'
				with open (path, "rb") as str_file:
					customer =model.Model.create_spss_model('SAMPLE_CUSTOMER', self, 
															'catalog_timeseries.str', str_file)
					models.append(customer) 
			#then check the existing models in bound services
			deployed_spss_models = model.SPSSModel.get_deployed_models(self)
			print deployed_spss_models
			deployed_dashdb_models = model.DashdbModel.get_deployed_models(self)
			print deployed_dashdb_models
			deployed_models = deployed_spss_models + deployed_dashdb_models
			print "deployed: " 
			print deployed_models
			#the existing models include the sample models we just deployed,
			#so we have to exclude these sample models 
			left_models = []
			for each_model in deployed_models:
				if not each_model.model_name in ['SAMPLE_CUSTOMER', 'SAMPLE_DRUG', 
												 'SAMPLE_CHURN', 'SAMPLE_ACQUISITION']:
					left_models.append(each_model)
			models += left_models
			print models
			#then for each model, retrieve its metadata and store them to database
			for each_model in models:
				each_model.retrieve_metadata()
				each_model.commit()
		except Exception as error:
			if 'msg' in error.__dict__:
				#if 'msg' is one of the attributes of the error,
				#it means this is an error defined this application
				raise e.Error(msg='Deploying sample models or retrieving existing models failed: '+error.msg)
			else:
				raise error


	def retrieve_model(self, model_name):
		"""
		Retrive a model from database.

		Returns:
		------
		Model object
			This object could be SPSSModel object or
			DashdbModel object according to different model type.

		Raises:
		------
		ModelNotExistsError
			An exception raised when failed to find a model in database
		"""
		model_detail = dbop.get_model(self, model_name)
		#since the 'owner' field of model_detail is only owner's username,
		#we have to change it to a User object
		#In this case, the owner of this model is the user itself
		model_detail['owner'] = self
		if model_detail['model_type'] == 'SPSS Predictive Model':
			return model.SPSSModel(**model_detail)
		elif model_detail['model_type'] == 'DashDB In-database Model':
			return model.DashdbModel(**model_detail)

	def list_spss_models(self, fields=['model_name']):
		"""
		List all SPSS models in database.

		Params:
		------
		fields: list
			each item of the list is a field name of detailed
			information on model

		Returns:
		------
		List
			A list with SPSS model 
		"""
		models = dbop.get_models(self, model_type='SPSS Predictive Model', fields=fields)
		return models

	def list_dashdb_models(self, fields=['model_name']):
		"""
		List all DashDB models in database.

		Params:
		------
		fields: list
			each item of the list is a field name of detailed
			information on model

		Returns:
		------
		List
			A list with DashDB model 
		"""
		models = dbop.get_models(self, model_type='DashDB In-database Model', fields=fields)
		return models

	def list_models(self, fields=['model_name']):
		"""
		List all models in database.

		Params:
		------
		fields: list
			each item of the list is a field name of detailed
			information on model

		Returns:
		------
		List
			A list with DashDB model 
		"""
		models = dbop.get_models(self, model_type='all', fields=fields)
		return models

	@classmethod
	def retrieve_user(cls, username):
		"""
		Retrive a user from database.

		Returns:
		-------
		User object

		Raises:
		------
		UserNotExistsError
			An error raised when failed to retrive a user from database
		"""
		user_detail = dbop.get_user(username)
		return cls(**user_detail)

	@staticmethod		
	def get_token(username, password):
		"""Get token from Cloud Foundary. """
		token = cf.get_token(username, password)
		return token

	@staticmethod
	def verify_access_key(key):
		from app import app
		s = JSONWebSignatureSerializer(app.config['SECRET_KEY'])
		try:
			data = s.loads(key)
		except BadSignature:
			return None # invalid key
		user = User.retrieve_user(data['username'])
		return user

	def __repr__(self):
		return '<User %r>' %  (self.username)
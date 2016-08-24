import db_operations as dbop
import dashdb_operations as dashdb
import exceptions as e
import requests
from time import gmtime, strftime

class Model(object):
	"""This is the base class for different type of models."""

	def __init__(self, model_name, owner, source, model_type, bound_service, 
				 creation_time=strftime("%Y-%m-%d %H:%M:%S", gmtime()),
				 last_refreshed="", input_metadata=None, output_metadata=None,
				 description="There is currently no description.",
				 score_hint="There is currently no hints on input", **kwargs):
		self.model_name = model_name
		self.owner = owner
		self.model_type = model_type
		self.source = source
		self.bound_service = bound_service
		self.last_refreshed = last_refreshed
		self.creation_time = creation_time
		self.input_metadata = input_metadata
		self.output_metadata = output_metadata
		self.description = description
		self.score_hint = score_hint
		for key, value in kwargs.items():
			setattr(self, key, value)

	def retrieve_metadata(self):
		"""Retrieve model's metadata from service instance."""
		pass

	def refresh(self):
		"""Refresh this model itself."""
		pass

	def real_time_score(self, header, data):
		"""Score with input data."""
		pass

	def delete(self):
		"""
		Delete this model from corresponding service instance and 
		its relevant data in the database.
		"""
		pass

	def commit(self):
		"""
		Create/Refresh a document of this model in remote Cloudant 'model_info_db' database.

		Raises:
		-------
		UnknowDatabaseError 
		"""
		#firstly, get all variables and values of this model
		content = self.__dict__.copy()  
		#Because self.owner is a User object,  it can not be stored in the database.
		#we have to replace it with User.username before create/update the model in database.
		content['owner'] = self.owner.username
		#if '_id' is one of the variables of this model instance,
		#it means this model is retrived from database. 
		#We are actually going to update the model document in database
		#instead of creating a new model document.
		#To update the document, we have to remove '_id' field.
		if '_id' in content.keys():
			document_id = content.pop('_id')
			res = dbop.update_model_in_database(document_id, content)    
		else:
			res = dbop.create_model_in_database(content)
		self._id = res['id']
		self._rev = res['rev']

	def get_history(self, behaviour='all', sort='desc', **kwargs):
		"""
		Get model's history records from Cloudant 'model_info_db' database.

		Params:
		------
		behaviour: str
			'score', 'refresh', 'visualize', or 'all'
		sort: str
			'desc' or 'asc'

		Raises:
		-------
		UnknowDatabaseError 
		"""
		records = dbop.retrieve_history(self, behaviour, sort)
		return records

	@staticmethod
	def create_spss_model(name, owner, source_file_name, source_file):
		"""
		Deploy a spss model by uploading a .str file to 
		user's Predictive Analytics service instance. 

		Returns:
		------
		SPSSModel object

		Raises:
		------
		ModelCreationError
			An exception with an error message in 'msg' attribute
		ModelAlreadyExistsError
			An exception raised when the model name conflicts with existing model
		"""
		#firstly, we retrieve all the models deployed in the predictive analytics service.
		#So that we can assure the model name we want to use doesn't conflict with existing model name.
		req_models = requests.request('GET',owner.predictive_analytics_url+ \
									  '/model?accesskey='+owner.predictive_analytics_access_key)
		if req_models.status_code != 200:
			#if the response code is not 200,
			#there must be something wrong
			raise e.ModelCreationError(msg='Model creation failed when trying to get existing models')
		else:
			#even the response code is 200,
			#it is also possible that operation is not succesful.
			#For this case spss will return a dict with 'flag' value
			if isinstance(req_models.json(), dict):
				raise e.ModelCreationError(msg=req_models.json())
			else:
				names = [item['id'] for item in req_models.json()]
				if name in names:
					#if the name conflicts, raise an exception.
					raise e.ModelAlreadyExistsError(name, "The name " + name + " conflicts with existing model. \
													Try with another name.")


		files = {'file': (source_file_name, source_file)}
		req = requests.request('PUT', owner.predictive_analytics_url +'/model/'+name+ \
								'?accesskey='+owner.predictive_analytics_access_key, files=files)
		print req
		if req.status_code != 200:
			#if the response code is not 200,
			#there must be something wrong
			raise e.ModelCreationError(msg='Model creation failed with \
											response code '+str(req.status_code))
		else:
			#even the response code is 200,
			#it is also possible that model creation is not succesful.
			#This case is indicated by a 'flag' boolean value
			if not req.json()['flag']:
				print req.text
				raise e.ModelCreationError(msg=req.json()['message'])
			else:
				#if "update" in req.json()['message'].split(" "):
				source = source_file_name
				return SPSSModel(name, owner, source)

	@staticmethod
	def create_dashdb_model(model_name, owner, input_table, target_column, 
							primary_key, is_sample=False, algorithm='decision_tree'):
		"""
		Deploy a dashdb model  to user's DasdDB service instance. 

		Returns:
		------
		DashdbModel object

		Raises:
		------
		ModelCreationError
			An exception with an error message in 'msg' attribute
		ModelAlreadyExistsError
		"""
		#firstly, we retrieve all the models existed in database.
		#So that we can assure the model name we want to use doesn't conflict with existing model name.
		names = owner.list_models()
		if model_name in names:
			#if the name conflicts, raise an exception.
			raise e.ModelAlreadyExistsError(model_name, "The name " + model_name + " conflicts with existing model. \
											Try with another name.")

		#if input table is from SAMPLES schema, append 'SAMPLES.' to input table name
		if is_sample:
			input_table = 'SAMPLES.' + input_table
		try:
			dashdb.model_create(input_table, target_column, primary_key, model_name, owner)
		except e.UnknownDashdbError as error:
			raise e.ModelCreationError(msg='Create model in Dashdb failed: '+error.msg)
		return DashdbModel(model_name, owner, source=input_table, is_visualized=False,
						   target_column=target_column, primary_key=primary_key)


class SPSSModel(Model):
	"""This is spss model class. Inherited from base model class. """

	def __init__(self, model_name, owner, source, **kwargs):
		if not 'bound_service' in kwargs.keys():
			#if this instance is created from uploading a .str file,
			#its bound service is the user's current predictive analytics service instance
			super(SPSSModel, self).__init__(model_name, owner, source, model_type="SPSS Predictive Model",  
				  bound_service=owner.predictive_analytics_instance, **kwargs)
		else:
			#if this instance is retrieved from database,
			#its bound service is in the document detail
			super(SPSSModel, self).__init__(model_name, owner, source, **kwargs)


	def retrieve_metadata(self):
		"""
		Retrieve model's metadata from service instance.
		For SPSS model, only input metadata can be retrieved.
		Output metadata is automatically assgined when scoring.

		Raises:
		------
		RetrieveMetadataError
			An exception raised when try to retrieve metadata from service provider. 
			Details are in the 'msg' attribute
		"""

		req = requests.request('GET', self.owner.predictive_analytics_url+'/metadata/'+self.model_name+ \
								'?accesskey='+self.owner.predictive_analytics_access_key)
		if req.status_code != 200:
			#if the response code is not 200,
			#there must be something wrong
			raise e.RetrieveMetadataError(msg='Retrieving metadata failed with \
											   response code '+str(req.status_code))
		else:
			#even the response code is 200,
			#it is also possible that retrieving metadata is not succesful.
			#This case is indicated by a 'flag' value
			if not req.json()['flag']:
				raise e.RetrieveMetadataError(msg=req.json()['message'])
			else:
				#since the metadata is given by xml style,
				#we have to parse it to a dict.
				metadata_xml = req.json()['message']
				input_metadata = xmlparsing(metadata_xml)
				self.input_metadata = input_metadata
				self.output_metadata = 'Output Metadata is only available after first scoring'

	def refresh(self, source_file_name, source_file):
		"""
		Refresh this model itself by uploading a .str file. 
		If refresh succesfully, a refreshing history record will be 
		stored into 'model_history_db' database

		Raises:
		------
		ModelRefreshError
			An exception with an error message in 'msg' attribute

		UnknownDatabaseError:
			An exception raised when interacting with database. 
			Details are in the 'msg' attribute.
		"""
		files = {'file': (source_file_name, source_file)}
		req = requests.request('PUT', self.owner.predictive_analytics_url +'/model/'+self.model_name+ \
								'?accesskey='+self.owner.predictive_analytics_access_key, files=files)
		if req.status_code != 200:
			#if the response code is not 200,
			#there must be something wrong
			raise e.ModelRefreshError(msg='Model refreshing failed with \
											response code '+str(req.status_code))
		else:
			#even the response code is 200,
			#it is also possible that model refreshing is not succesful.
			#This case is indicated by a 'flag' value
			if not req.json()['flag']:
				raise e.ModelRefreshError(msg=req.json()['message'])
			else:
				self.last_refreshed = strftime("%Y-%m-%d %H:%M:%S", gmtime())
				self.source = source_file_name
				#after refreshing, metadata has to change
				self.retrieve_metadata()
				self.commit()
				#store this history record into database
				dbop.store_history_record(self, 'refresh', 'Model has been refreshed with file ' \
															+ source_file_name, source=source_file_name)

	def real_time_score(self, header, data):
		"""Score with input data.
		   If score succesfully, a scoring history record will be 
		   stored into 'model_history_db' database

		Params:
		------
		headers: list
			A list with input names. This could be retrived from 
			Model.input_metadata. If we treat input as a table,
			this list could be considered as the first row with column names.
		data: list 
			A list with input data. Each item of this list should also be
			a list, which can be considered as a row of the input table.

		Returns:
		-------
		dict 
			This dict can also be regarded as a table.
			It has two keys: header, data
			Header is the output data name.

		Raises:
		-------
		ModelScoreError
			An exception raised when try to score in corresponding SPSS service instance.
		"""
		score_input = {}
		score_input['tablename'] = 'scoreInput'
		score_input['header'] = header
		score_input['data'] = data
		req = requests.request('POST', self.owner.predictive_analytics_url+'/score/'+ \
									   self.model_name+'?accesskey='+self.owner.predictive_analytics_access_key, json=score_input)
		if req.status_code != 200:
			#if the response code is not 200,
			#there must be something wrong
			raise e.ModelScoreError(msg='Score failed with response code '+str(req.status_code))
		else:
			#even the response code is 200,
			#it is also possible that scoring is not succesful.
			#This case is indicated by a 'flag' value
			if isinstance(req.json(), dict):
				raise e.ModelScoreError(msg='Score failed with reason:' + req.json()['message'])
			else:
				#since output metadata of SPSS model can only be retrived from scoring result.
				#if model's output metadata is not available so far,
				#we will store it now
				if not isinstance(self.output_metadata, dict):
					output_metadata = []
					#reformat the output metadata 
					for header in req.json()[0]['header']:
						output_metadata.append({'name': header,
												'measurementLevel': '',
												'storageType': ''})
					self.output_metadata = output_metadata
					self.commit()
				#create a history record
				record = {
						  'input': data,
						  'output': req.json()[0]['data'],
						  'score_type': 'real_time_score'
						 }
				#store this record into database
				dbop.store_history_record(self, 'score', value=record)
				return req.json()[0]

	def delete(self):
		"""
		Delete this model from corresponding SPSS service instance and 
		its relevant data in the database.


		Raises:
		------
		ModelDeleteError
			An exception raised when failed to delete model from SPSS service instance

		UnknownDatabaseError:
			An exception raised when interacting with database. 

		ModelNotExistsError:
			An exception raised when could not find this model in database.
		"""
		req = requests.request('DELETE', self.owner.predictive_analytics_url+'/model/'+ \
										 self.model_name+'?accesskey='+self.owner.predictive_analytics_access_key)
		if req.status_code != 200:
			#if the response code is not 200,
			#there must be something wrong
			raise e.ModelDeleteError(msg='Failed to delete model with \
											response code '+str(req.status_code))
		else:
			#even the response code is 200,
			#it is also possible that model refreshing is not succesful.
			#This case is indicated by a 'flag' value
			if not req.json()['flag']:
				raise e.ModelDeleteError(msg=req.json()['message'])
			else:
				#if delete succuessfully from service instance, 
				#the we have to delete it relavant data in database
				dbop.del_model_from_database(self.owner, self.model_name)

	@classmethod	
	def get_deployed_models(cls, user):
		"""
		Get all spss models in user's spss service instance

		Returns:
		------
		list
			each item of the list is a SPSSModel object
		"""
		#firstly, we retrieve all the models deployed in the predictive analytics service.
		req_models = requests.request('GET',user.predictive_analytics_url+ \
									  '/model?accesskey='+user.predictive_analytics_access_key)
		if req_models.status_code != 200:
			#if the response code is not 200,
			#there must be something wrong
			raise e.UnknownSPSSError(msg='Retrieving models in SPSS instance \
										  failded with response:'+req_models.text)
		else:
			#even the response code is 200,
			#it is also possible that operation is not succesful.
			#For this case spss will return a dict with 'flag' value
			if isinstance(req_models.json(), dict):
				raise e.UnknownSPSSError(msg='Retrieving models in SPSS instance \
										  failded with response:'+req_models.json())
			else:
				models = []
				print req_models.json()
				for item in req_models.json():
					model = cls(item['id'], user, item['stream'])
					models.append(model)
				return models

	def __repr__(self):
		return '<SPSSModel %r for User %r>' %  (self.model_name, self.owner.username)

class DashdbModel(Model):
	"""This is dashdb model class. Inherited from base model class. """

	def __init__(self, model_name, owner, source, is_visualized=False, **kwargs):
		if not 'bound_service' in kwargs.keys():
			#if this instance is created from running R scripts in Dashdb,
			#its bound service is the user's current dashdb service instance
			super(DashdbModel, self).__init__(model_name, owner, source, model_type="DashDB In-database Model",  
				  bound_service=owner.dashDB_instance, **kwargs)
		else:
			#if this instance is retrieved from database,
			#its bound service is in the document detail
			super(DashdbModel, self).__init__(model_name, owner, source, **kwargs)
		self.is_visualized = is_visualized

	def __repr__(self):
		return '<DashdbModel %r for User %r>' %  (self.model_name, self.owner.username)

	def retrieve_metadata(self):
		"""
		Retrieve model's metadata from service instance.
		Both input metadata and output metadata are retrieved.
		Metadata are stored in DashdbModel.input_metadata and 
		DashdbModel.output_metadata if retrieved succesfully.


		Raises:
		------
		RetrieveMetadataError
			An exception raised when try to retrieve metadata from service provider. 
			Details are in the 'msg' attribute
		"""
		try:
			metadata = dashdb.metadata(self.model_name, self.owner)
			self.input_metadata = metadata['InputMetadata']
			self.output_metadata = metadata['OutputMetadata']
		except e.UnknownDashdbError as error:
			raise e.RetrieveMetadataError(msg= 'Retrieving metadata failed with \
												reason '+error.msg)

	def refresh(self, input_table, target_column, 
				primary_key, is_sample=False, algorithm='decision_tree'):
		"""
		Refresh this model itself by running R script in DashDB. 
		If refresh succesfully, a refreshing history record will be 
		stored into 'model_history_db' database

		Raises:
		------
		ModelRefreshError
			An exception with an error message in 'msg' attribute

		UnknownDatabaseError:
			An exception raised when interacting with database. 
			Details are in the 'msg' attribute.
		"""
		#if input table is from SAMPLES schema, append 'SAMPLES.' to input table name
		if is_sample:
			input_table = 'SAMPLES.' + input_table
		try:
			dashdb.model_create(input_table, target_column, primary_key, self.model_name, self.owner)
		except e.UnknownDashdbError as error:
			raise e.ModelRefreshError(msg='Refresh model in Dashdb failed: '+error.msg)
		#if refresh successfully, change the corresponding model information
		self.last_refreshed = strftime("%Y-%m-%d %H:%M:%S", gmtime())
		self.source = input_table
		self.target_column = target_column
		self.primary_key = primary_key
		#after refreshing, metadata has to change
		self.retrieve_metadata()
		self.is_visualized = False
		self.commit()
		#store this history record into database
		dbop.store_history_record(self, 'refresh', 'Model has been refreshed with table ' \
													+ input_table, source= input_table)

	def real_time_score(self, header, data, custom_table_name=''):
		"""Score with input data.
		   If score succesfully, a scoring history record will be 
		   stored into 'model_history_db' database

		Params:
		------
		headers: list
			A list with input names. This could be retrived from 
			DashdbModel.input_metadata. If we treat input as a table,
			this list could be considered as the first row with column names.
		data: list 
			A list with input data. Each item of this list should also be
			a list, which can be considered as a row of the input table.
		custom_table_name: str
			if a table name is provided, the scoring result will be stored in
			Dashdb instance with that name.

		Returns:
		-------
		dict 
			This dict can also be regarded as a table.
			It has two keys: header, data
			Header is the output data name. 
			Each item of the data is also a list, 
			which is the class predicted by this model.
			(Since we consider a decision tree model, output is class)

		Raises:
		-------
		ModelScoreError
			An exception raised when try to score in corresponding Dashdb service instance.
		UnknownDatabaseError
		"""
		try:
			output_data = dashdb.real_time_score(self.model_name, header, data, self.owner, custom_table_name)
		except e.UnknownDashdbError as error:
			raise e.ModelScoreError(msg='Score failed with reason: '+error.msg)

		output = {
					'header': [item['name'] for item in self.output_metadata],
					'data': output_data
				 }
		#create a history record
		record = {
				  'input': data,
				  'output': output_data,
				  'score_type': 'real_time_score'
				 }
		#store this record into database
		dbop.store_history_record(self, 'score', value=record)
		return output

	def batch_score(self, input_table, primary_key, is_sample=False, custom_table_name=''):
		"""Batch score with a table in Dash instance.
		   If score succesfully, a scoring history record will be 
		   stored into 'model_history_db' database

		Params:
		------
		is_sample: boolean
			True if the input table is in SAMPLES schema of DashDB
		custom_table_name: str
			Use custom table name for result table.
			If this is an empty str, a table name will be given automatically.

		Returns:
		-------
		dict 
			This dict has two keys:
			  input: the table name of the input table
			  output: the table name of the result table

		Raises:
		-------
		ModelScoreError
			An exception raised when try to score in corresponding DashDB service instance.
		UnknownDatabaseError
		"""
		if is_sample:
			input_table = 'SAMPLES.' + input_table
		try:
			output = dashdb.batch_score(self.model_name, input_table, 
										  primary_key, custom_table_name, self.owner)
		except e.UnknownDashdbError as error:
			raise e.ModelScoreError(msg='Score failed with reason: '+error.msg)

		result = {
				  'input': input_table,
				  'output': output['table_name'],
				  'score_type': 'batch_score'
				 }
		#store this record into database
		dbop.store_history_record(self, 'score', value=result)
		result.pop('score_type')
		return result


	def delete(self):
		"""
		Delete this model from corresponding DashDB service instance and 
		its relevant data in the database.


		Raises:
		------
		ModelDeleteError
			An exception raised when failed to delete model from SPSS service instance

		UnknownDatabaseError:
			An exception raised when interacting with database. 

		"""
		try:
			dashdb.delete_model(self.model_name, self.owner)
		except e.UnknownDashdbError as error:
			raise e.ModelDeleteError(msg='Failed to delete model with reason: '+error.msg)
		dbop.del_model_from_database(self.owner, self.model_name)

	def visualize(self):
		"""
	    visualize decision tree model in Dashdb.
	    The visualization image is stored in folder 'outputs' 
	    with filename 'username+model_name.jpg'

	    Raises:
	    -----
	    UnknownDashdbError
	    """
		try:
			dashdb.visualize(self.model_name, self.owner)
			#store this history record into database
			dbop.store_history_record(self, 'visualize', 'Model has been visualized.')
			self.is_visualized = True
			self.commit()
		except e.UnknownDashdbError as error:
			raise e.ModelVisualizeError(msg='Failed to visualize model with reason: '+error.msg)

	@classmethod	
	def get_deployed_models(cls, user):
		"""
		Get all dashdb models in user's dashdb service instance

		Returns:
		------
		list
			each item of the list is a DashdbModel object
		"""
		#firstly, we retrieve all the models deployed in the predictive analytics service.
		try: 
			models = []
			model_names_list = dashdb.retrieve_models(user)
			print model_names_list
			for model_name in model_names_list:
				model = cls(model_name, user, 'Not available')
				models.append(model)
			return models
		except e.UnknownDashdbError as error:
			raise e.UnknownDashdbError(msg='Get deloyed models failed: '+error.msg)

	def __repr__(self):
		return '<DashdbModel %r for User %r>' %  (self.model_name, self.owner.username)
###parse xml file from Predictive Model metadata response
def xmlparsing(xml_string):

	import xml.etree.ElementTree as ET

	root = ET.fromstring(xml_string)
	uri = tag_uri_and_name(root)[0] 
	fields = root.findall(".//*[@name='scoreInput']/{"+uri+"}field")
	entries = []
	for field in fields:
		entries.append(field.attrib)
	return entries
			
def tag_uri_and_name(elem):
	if elem.tag[0] == "{":
		uri, ignore, tag = elem.tag[1:].partition("}")
	else:
		uri = None
		tag = elem.tag
	return uri, tag
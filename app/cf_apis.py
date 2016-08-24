# -*- coding: utf-8 -*-
"""
Created on Fri Nov 13 13:05:23 2015

@author: pool84
"""

import exceptions as e
import requests

regions = { 
			'United Kingdom' : 'http://api.eu-gb.bluemix.net',
			'US' : 'http://api.ng.bluemix.net',
			'Sydney' : 'http://api.au-syd.bluemix.net'
		  }

shared_guid = '7ae0c4d2-a5f6-44c6-9ae9-9226827d20ed'
dash_db_guid ='071532f7-71c9-4797-87e4-09591fe7aa1d'
spss_pm_guid = '4a463d24-6920-4e0f-bb40-f91de66607e5'
space_dev_guid = 'c0b689dd-bfb3-4c54-bd95-f4863064f027'
space_space2_guid = 'd73d77a8-4b90-47d5-a5f0-862152f6c3fe'
entry_service_plan_guid = {'United Kingdom': '0f3014fb-51bd-477d-896a-219875a72485',
						   'US' : 'b06c9513-ee1a-4fa3-9637-4ffbd8f93432',
						   'Sydney': '5be673fc-1d8e-4698-82c2-5c90d9676e41'} 
free_service_plan_guid = { 'United Kingdom' : 'a3edd2d7-69d2-4921-9604-7076a244e3b8',
							'US' : 'bffc1ae9-71f5-4d27-b403-224ae8e14c7c'} #for Predictive Analytics
dashdb_service_plans_url = {'United Kingdom': '/v2/services/eef01413-dcc9-4fd9-888f-a91411577506/service_plans',
							'US': '/v2/services/7c87c148-e1a4-4cb8-81f8-c5e74be7684b/service_plans',
							'Sydney':'/v2/services/c3ebfe49-3687-4f44-9305-09d37c0f5d4c/service_plans'}

def get_token(username, password):    
	"""
	Get token from Cloud Foundry using Bluemix username/password.
	This token is used to interact with Cloud Foundry, including
	creating and binding application and services.

	Returns:
	-------
	str
		if a token is obtained from Cloud Foundry successfully, 
		return the token as a str
	"""
	headers = {'Content-Type': 'application/x-www-form-urlencoded'}    
	params = {
			  'password':password,           
			  'username':username,          
			  'grant_type':'password',          
			  'scope':''
			  }    
	url = 'https://login.eu-gb.bluemix.net/UAALoginServerWAR/oauth/token'    
	r = requests.request('POST', url, params=params,headers=headers,auth=('cf',''))    
	return r.json()['access_token'] if (r.status_code==200) else None
	
def url(url, method='GET', access_token='', params={}, data={},json={}):
	"""
	Make a http request to Cloud Foundry with given url, method, token and parameters

	Returns:
	-------
	A Response Object
	"""    
	headers = {'Accept': 'application/json',            	  
			   'Authorization':'bearer '+ access_token} 
	if json:
		return requests.request(method,url,headers=headers,params=params,data=data,json=json)
	else:
		return requests.request(method,url,headers=headers,params=params,data=data)

def get_orgs(region, access_token):
	"""
	Get account's organizations in specific region.

	Params:
	-------
	region: str
		Region cloud be 'US', 'United Kingdom', 'Sydney'
	access_token: str
	    The token used to authenticate HTTP request

	Returns:
	------
	list
		A list of organizations.
		Each item of the list is a dict. It has two keys:
			name: name of the organization
			guid: id of the organization

	Raises:
	------
	UnknownCloudFoundryError
	"""
	api = regions[region] + '/v2'
	req_orgs = url(api+'/organizations','GET', access_token)
	if req_orgs.status_code != 200:
		raise e.UnknownCloudFoundryError(msg='Get organizations in region '+region \
											  +' failed. Reason: '+str(req_orgs.json()))
	else:
		req_orgs = req_orgs.json()['resources']
		orgs = []
		for item in req_orgs:
			name_guid = { 'name' : item['entity']['name'], 
						  'guid' : item['metadata']['guid'] }
			orgs.append(name_guid)
		return orgs

def get_spaces(region, org_guid, access_token):
	"""
	Get account's spaces in specific organization.

	Params:
	-------
	region: str
		Region cloud be 'US', 'United Kingdom', 'Sydney'
	org_guid: str
		ID of the organization where we want to retrieve spaces
	access_token: str
	    The token used to authenticate HTTP request

	Returns:
	------
	list
		A list of spaces.
		Each item of the list is a dict. It has two keys:
			name: name of the space
			guid: id of the space

	Raises:
	------
	UnknownCloudFoundryError
	"""
	api = regions[region] + '/v2'
	req_spaces = url(api+'/organizations/'+org_guid+'/spaces', 'GET', access_token)
	if req_spaces.status_code != 200:
		raise e.UnknownCloudFoundryError(msg='Get spaces in region '+region \
											  +' failed. Reason: '+str(req_spaces.json()))
	else:
		req_spaces = req_spaces.json()['resources']
		spaces = []
		for item in req_spaces:
			name_guid = { 'name' : item['entity']['name'], 
						  'guid' : item['metadata']['guid'] }
			spaces.append(name_guid)
		return spaces

# def get_service_instances(region, access_token, type):
# 	api = regions[region] + '/v2'
# 	services = url(api+'/service_instances','GET', access_token)

def get_dashdb_instances_in_region(region, token):
	"""
	Get user's exsiting Dashdb service instances in a specific region

	Returns:
	-------
	list
		A list of Dashdb instances.
		Each item of the list is a tuple. It has two elements:
			first element: name of Dashdb instance
			second element: id of the Dashdb instance

	Raises:
	------
	UnknownCloudFoundryError
	"""
	#firstly, we have to get all Dashdb service plans in that region
	dashdb_service_plan_url = dashdb_service_plans_url[region]
	dashdb_service_plan_raw = url(regions[region]+dashdb_service_plan_url, access_token=token)
	if dashdb_service_plan_raw.status_code != 200:
		raise e.UnknownCloudFoundryError(msg='Retrieving Dashdb service plans in region '+region \
											  +' failed. Reason: '+str(dashdb_service_plan_raw.json()))
	else:
		dashdb_services_plan_guids = []  #this list stores all Dashdb 
										 #service plans in that region
		for item in dashdb_service_plan_raw.json()['resources']:
			guid = item['metadata']['guid']
			dashdb_services_plan_guids.append(guid)

		dashdb_instances = [] #this list stores all Dashdb
							  #instances in that region
		for guid in dashdb_services_plan_guids:
			dashdb_instance_details_res = url(regions[region]+'/v2/service_plans/'+\
											  guid+'/service_instances', access_token=token)
			if dashdb_instance_details_res.status_code != 200:
				raise e.UnknownCloudFoundryError(msg='Retrieving Dashdb service instances in region '+region \
											          +' failed. Reason: '+str(dashdb_instance_details_res.json()))
			else:
				dashdb_instance_details = dashdb_instance_details_res.json()['resources']
				guid_name = []  #this list stores Dashdb 
								#instances for a specific service plan
				for each in dashdb_instance_details:
					guid_name.append((each['entity']['name'], each['metadata']['guid']))
				dashdb_instances += guid_name
			return dashdb_instances

# def get_dashdb_instances_names(access_token):
# 	names = []
# 	for region in regions.keys():
# 		names_in_region = get_dashdb_instances_in_region(region, access_token)
# 		names += names_in_region
# 	return names

def get_dashdb_credentials(region, instance_guid, access_token):
	"""
	Get credentials call 'ml-service' for a Dashdb instance given instance ID. 

	Returns:
	--------
	Tuple 
		This tuple has three elements:
		  1st element: host of this dashdb instance
		  2nd element: username of this dashdb instance
		  3rd element: password of this dashdb instance

	Raises:
	------
	UnknownCloudFoundryError
	"""
	#firstly, try to get all service keys in that region.
	#if a service key called 'ml-service' exists, 
	#we just return that service key instead of creating a new one
	all_credentials_res = url(regions[region]+'/v2/service_keys','GET', access_token)
	if all_credentials_res.status_code != 200:
		raise e.UnknownCloudFoundryError(msg='Retrieving all Dashdb credentials in region '+region \
								          +' failed. Reason: '+str(all_credentials_res.json()))
	else:
		all_credentials = all_credentials_res.json()['resources']
		for credential in all_credentials:
			if credential['entity']['name'] == 'ml-service':
				#if a service key call 'ml-service' exsits
				#,since it could be credentials for other instance we used before,
				#we have to delete it.
				guid = credential['metadata']['guid']
				try_delete = url(regions[region]+'/v2/service_keys/'+guid,'DELETE', access_token)
				if try_delete.status_code != 204:
					raise e.UnknownCloudFoundryError(msg='Deleting exsiting Dashdb credentials'
								          +' failed. Reason: '+str(try_delete.json()))		
		#if the service key does not exist, create it		
		credentials_res = url(regions[region]+'/v2/service_keys','POST', 
										access_token=access_token,
										json={'service_instance_guid': instance_guid,
										  					   'name':'ml-service'})
		if credentials_res.status_code != 201:
			raise e.UnknownCloudFoundryError(msg='Creating Dashdb credentials in region '+region \
									          +' failed. Reason: '+str(credentials_res.json()))
		else:
			credentials = credentials_res.json()['entity']['credentials']
			return (credentials['host'],
					credentials['username'],
					credentials['password'])


def create_app(region, space_guid, app_name, access_token):
	"""
	Create an app in a Bluemix space.

	Returns:
	--------
	str
		ID of the app created

	Raises:
	------
	UnknownCloudFoundryError
	"""
	api = regions[region] + '/v2'
	create_res = url(api+'/apps','POST', access_token=access_token, 
										 json={'name':app_name,
											   'space_guid':space_guid})
	if create_res.status_code != 201:
		raise e.UnknownCloudFoundryError(msg='Create app '+app_name+ \
								         	 ' failed. Reason: '+str(create_res.json()))
	else:
		return create_res.json()['metadata']['guid']

def bind_service(region, service_guid, app_guid, access_token):
	"""
	Bind a service instance with an app.

	Returns:
	--------
	dict
		This dict contains credentials to access the service instance

	Raises:
	------
	UnknownCloudFoundryError
	"""
	api = regions[region] + '/v2'
	bind = url(api+'/service_bindings', method='POST', 
										access_token=access_token, 
										json={
											 'service_instance_guid':service_guid,
											 'app_guid':app_guid})
	if bind.status_code != 201:
		raise e.UnknownCloudFoundryError(msg='Bind service failed. Reason: '+str(bind.json()))
	else:
		return bind.json()['entity']['credentials']

		
def create_service(region, name, service_plan, space_guid, access_token):
	"""
	Create a service instance in a Bluemix space.

	Returns:
	--------
	str
		ID of the service created

	Raises:
	------
	UnknownCloudFoundryError
	"""
	api = regions[region] + '/v2'
	create = url(api +'/service_instances?accepts_incomplete=true',
											 method='POST', 
											 access_token=access_token,
											 json={
												   'name':name,
												   'service_plan_guid': service_plan,
												   'space_guid':space_guid})
	if create.status_code != 201:
		raise e.UnknownCloudFoundryError(msg='Create service '+name+' failed. Reason: '+str(create.json()))
	else:
		return create.json()['metadata']['guid']


def create_app_and_bind_services(region, app_name, space_guid, access_token, dashdb):
	"""
	Create an app and services in a Bluemix space and bind them.

	Params:
	------
	region: str
		Region could be 'US', 'United Kingdom' or 'Sydney'
	app_name: str
		Name of the app to be created
	space_guid: str
		ID of the space where the app locates
	access_token: str
		Token used to interact with Cloud Foundry
	dashdb: boolean:
		True if want to create a Dashdb service instance

	Returns:
	--------
	dict
		This dict contains credentials to access services.
		Depends on what services are created, the possible keys are:
		'dashDB': dashdb credentials if dashdb instance is created
		'Predictive Analytics': Predictive Analytics credent if this instance is created

	Raises:
	------
	UnknownCloudFoundryError
	"""
	try:
		#firstlt try to create an app with given name
		app_guid = create_app(region, space_guid, app_name, access_token)
		if dashdb:
			#if we want to create a dashdb service instance
			#get the ID of the instance created and bind it with the app
			dashDB_guid = create_service(region, app_name+'-DASHDB-DONT-DELETE', 
										 entry_service_plan_guid[region], space_guid, access_token)
			credentials = bind_service(region, dashDB_guid, app_guid, access_token)
			dashDB_credentials = (credentials['host'], credentials['username'], credentials['password'])
		#Then create a predictive analytics service instance
		#get the ID of the instance created and bind it with the app
		predictive_analytics_guid = create_service(region, app_name+'-PA-DONT-DELETE', 
												   free_service_plan_guid[region], space_guid, access_token)
		credentials = bind_service(region, predictive_analytics_guid, app_guid, access_token)
		PA_credentials = (credentials['url'], credentials['access_key'])
		return {'dashDB' : dashDB_credentials,
				'Predictive Analytics' : PA_credentials } if dashdb else {'Predictive Analytics' : PA_credentials }
	except e.UnknownCloudFoundryError as error:
		#If an exception is raised, simply reraise it.
		raise error
		   

	

"""
services.json()
services = cf.url(cf.api_v2+'/services', token=token)
services = cf.url(cf.api_v2+'/services', access_token=token)
services.json()
res = services.json()['resources']
services_plans = []
for item in res:
	service = {}
	key = service['entity']['label']
	value =  service['entity']['service_plans_url']
	service[key] = value
	services_plans.append(service)
	
services.json()
res = services.json()['resources']
for item in res:
	service = {}
	key = item['entity']['label']
	value =  item['entity']['service_plans_url']
	service[key] = value
	services_plans.append(service)
	
services_plans
dashdb_eu_service_plan = services_plans['dashdb']
for item in res:
	key = item['entity']['label']
	value =  item['entity']['service_plans_url']
	service_plans[key] = value
 
service_plans = {}
for item in res:
	key = item['entity']['label']
	value =  item['entity']['service_plans_url']
	service_plans[key] = value
	
service_plans
dashdb_eu_service_plan = services_plans['dashdb']
dashdb_eu_service_plan = service_plans['dashdb']
dashdb_eu_service_plan = service_plans['dashDB']
dashdb_service_plan = cf.url(cf.api_v2+'/'+dashdb_eu_service_plan, access_token=token)
dashdb_service_plan.json()
dashdb_service_plan = cf.url(cf.api_v2+'/'+dashdb_eu_service_plan, access_token=token)
dashdb_eu_service_plan = service_plans['dashDB'][2:]
dashdb_eu_service_plan
dashdb_eu_service_plan = service_plans['dashDB'][3:]
dashdb_eu_service_plan
dashdb_service_plan = cf.url(cf.api_v2+dashdb_eu_service_plan, access_token=token)
dashdb_service_plan
dashdb_service_plan.json()
dashdb_services_plan_guids = []
for item in dashdb_service_plan.json()['resources']:
	guid = item['metadata']['guid']
	dashdb_services_plan_guids.append(guid)
	
	
	
dashdb_services_plan_guids
dashdb_services_details =cf. url(cf.api_v2+'/service_plans/'+dashdb_services_plan_guids[0]+'/service_instances', access_token=token).json()['resources']
dashdb_services_details
dashdb_services_details[0]['entity']['name']



def get_token(username, password):    
	headers = {'Content-Type': 'application/x-www-form-urlencoded'}    
	params = {
			  'password':password,           
			  'username':username,          
			  'grant_type':'client_credentials',          
			  'scope':''
			  }    
	url = 'https://login.eu-gb.bluemix.net/UAALoginServerWAR/oauth/token'    
	r = requests.request('POST', url, params=params,headers=headers,auth=('mlservice','4gmWXrwZbRQcxVZp'))    
	return r.json()['access_token'] if (r.status_code==200) else None


token = get_token(username, password)

token
Out[23]: u'eyJhbGciOiJIUzI1NiJ9.eyJqdGkiOiI4YzQ1YjljNS00N2NlLTRjYmItYTY3Ni1jNDY4ZjAyYzdlMGMiLCJzdWIiOiJtbHNlcnZpY2UiLCJhdXRob3JpdGllcyI6WyJzZXJ2aWNlX2Jyb2tlciIsIm9wZW5pZCJdLCJzY29wZSI6WyJvcGVuaWQiLCJzZXJ2aWNlX2Jyb2tlciJdLCJjbGllbnRfaWQiOiJtbHNlcnZpY2UiLCJjaWQiOiJtbHNlcnZpY2UiLCJhenAiOiJtbHNlcnZpY2UiLCJncmFudF90eXBlIjoiY2xpZW50X2NyZWRlbnRpYWxzIiwicmV2X3NpZyI6IjkyODI2OGU1IiwiaWF0IjoxNDQ5MDUwNzkxLCJleHAiOjE0NDkwOTM5OTEsImlzcyI6Imh0dHBzOi8vdWFhLm5nLmJsdWVtaXgubmV0L29hdXRoL3Rva2VuIiwiemlkIjoidWFhIiwiYXVkIjpbIm1sc2VydmljZSIsIm9wZW5pZCJdfQ.JUIGwbqCCP507cai7BUYsTEyaBn-UQLtQ8_cdrNI1J8'

services = cf.url(cf.api_v2+'/services', access_token=token)

services
Out[25]: <Response [401]>

services.json()
Out[26]: 
{u'code': 1000,
 u'description': u'Invalid Auth Token',
 u'error_code': u'CF-InvalidAuthToken'} 

services = cf.url(cf.regions['US']+'/v2/services', access_token=token)
res = services.json()['resources']
service_plans = {}
for item in res:
	key = item['entity']['label']
	value =  item['entity']['service_plans_url']
	service_plans[key] = value
print service_plans """
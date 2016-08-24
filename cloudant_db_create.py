"""
Cloudant database initialization module.

This script will create three databases in Cloudant account. They are:
	1. user_db: store app user infomation
	2. model_info_db: store model's basic information
	3. model_history_db: store model's history

This script will firstly connect to Cloudant. If any of the three databases exists,
delete it. Then create three new databases and create indexes for each database.
These indexes are used to query documents.
 

This script is used for following cases:
	1. Deploy this application for the first time and initialize database.
	2. Change to another Cloudant account.
	3. Delete app data and reset the application. 

"""

from config import CLOUDANT_USER, CLOUDANT_PWD
from app.exceptions import (DatabaseConnectError,
						   DatabaseDeleteError,
						   DatabaseCreateError,
						   IndexCreateError)

def create_index(db, db_name, indexes):
	"""
	Create index for given db.

	Raises:
	-------
		DatabaseDeleteError
	"""
	for each_index in indexes:
		index = {
			"index": {"fields": each_index},
			"type": "json"}
		try_index = db.post(path='_index', params = index)
		if try_index.status_code != 200:
			#if storing index is not successful, raise an exception
			raise IndexCreateError(msg="Create index for " + db_name + \
										" failed.")


import cloudant

account = cloudant.Account(CLOUDANT_USER)
login = account.login(CLOUDANT_USER, CLOUDANT_PWD)

#raise an exception when connecting to database failed
if login.status_code != 200:
	raise DatabaseConnectError("Connect to Cloudant failed with reason: " + login.text)

databases = ['user_db', 'model_info_db', 'model_history_db']

for db_name in databases: 
	if account.get(db_name).status_code != 404:
		#if this database already exists, delete it.
		try_delete = account.database(db_name).delete()
		if try_delete.status_code != 200:
			raise DatabaseDeleteError(msg="Delete database "+ db_name + \
										  " failed with reason: " + try_delete.text)

	#otherwise create this database
	db = account.database(db_name)
	create_db = db.put()
	if create_db.status_code != 201:
		raise DatabaseCreateError(msg="Create database "+ db_name + \
										" failed with reason: " + create_db.text)		
	#if create database succeeds, put indexes into it
	elif db_name == 'model_history_db':
		indexes = [['owner', 'model_name'],
				   ['owner', 'model_name', 'type'],
				   ['owner', 'model_name', 'creation_time', 'behaviour'],
				   ['owner', 'model_name', 'creation_time', 'type' ],
				   ['owner', 'model_name', 'value.score_type']]
		create_index(db, db_name, indexes)
	elif db_name == 'model_info_db':
		indexes = [['owner'],
				   ['owner', 'model_name'], 
				   ['owner', 'model_type']]
		create_index(db, db_name, indexes)
	else:
		pass

print ("Databases 'user_db', 'model_info_db', " 
	  "'model_history_db' have been successfully created in Cloudant." )




			



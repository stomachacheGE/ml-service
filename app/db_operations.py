# -*- coding: utf-8 -*-
"""
Created on Wed Sep 16 15:44:12 2015

@author: pool84
"""
import cloudant
from time import gmtime, strftime
import exceptions as e

#import remote Cloudant account
from app import db_account

#from app import db_account

def get_user(username):
    """
    Get details of a user from database.

    Returns:
    ------
    dict
        A dict with detailed inforamtion on this user.

    Raises:
    ------
    UserNotExistsError
    """
    db = db_account.database('user_db')
    user_doc = db.get(username)
    if  user_doc.status_code != 200:
        raise e.UserNotExistsError(username, 'User '+ username + ' does not exist.')
    else:
        return user_doc.json()

def store_history_record(model, behaviour, value, **kwargs):
    """
    Store history record to 'model_history_db' database.

    Raises:
    -------
    UnknownDatabaseError
    """
    data_db = db_account.database('model_history_db')
    data = {}
    data['owner'] = model.owner.username
    data['type'] = 'history'
    data['behaviour'] = behaviour
    data['model_name'] = model.model_name
    data['value'] = value
    data['creation_time'] = strftime("%Y-%m-%d %H:%M:%S", gmtime())
    data['bound_service'] = model.bound_service
    for arg_name,arg in kwargs.items():
        data[arg_name] = arg
    res = data_db.post('', params = data)
    if res.status_code != 201:
        raise e.UnknownDatabaseError('Storing refreshing history failed \
                                      with status code ' + str(res.status_code))
    else: 
        pass

def query(db, selector, fields=[], sort=[]):
    """
    Make a query to given database.

    Returns:
    -------
    dict
        A dict with key 'docs'.
    """
    query = {
        "selector": selector,
        "fields": fields,
        "sort": sort}
    res = db.post(path='_find', params=query)
    if res.status_code != 200:
        raise e.UnknownDatabaseError('Retrieving documents failed with status code ' \
                                       + str(res.status_code) + '; details: '+ res.text)
    else: 
        return res.json()

def get_model(user, model_name):
    """
    Get details of a model.

    Returns:
    ------
    dict
        A dict with detailed inforamtion on this model.

    Raises:
    ------
    ModelNotExistsError
    """
    db = db_account.database('model_info_db')
    model = query(db, {'owner': user.username,'model_name': model_name})['docs']
    if not model:
        raise e.ModelNotExistsError(model_name, 'Model '+ model_name + ' does not exist.')
    else:
        return model[0]

def get_models(user, model_type, fields):
    """
    List all models with given type in database.

    Params:
    -------
    user: User Object
    model_type: str
        This could be 'all', 'SPSS Predictive Model',
        and 'Dashdb In-database Model'.
    fields: list
        each item of the list is a field name of detailed
        information on model

    Returns:
    ------
    List
        A list with model infromation

    Raises:
    ------
    UnknownDatabaseError
    """
    db = db_account.database('model_info_db')
    if model_type == 'all':
        models = query(db, {'owner': user.username}, fields=fields)['docs']
    else:
        models = query(db, {'owner': user.username,'model_type': model_type}, fields=fields)['docs']
    return models

def del_model_from_database(user, model_name):
    """
    Delete model from 'model_info_db' database.

    Raises:
    ------
    ModelNotExistsError
    UnknownDatabaseError
    """
    #firstly find the model in 'model_info_db' database and delete it
    info_db = db_account.database('model_info_db')
    model = query(info_db, {'owner': user.username,'model_name': model_name})['docs']
    if not model:
        #if model is not found, raise an exception
        raise e.ModelNotExistsError(model_name, 'Model '+ model_name + ' does not exist in database.')
    else:
        try_delete = info_db.delete(model[0]['_id'], params={'rev': model[0]['_rev']})
        if try_delete.status_code != 200:
            raise e.UnknownDatabaseError("Unable to delete "+model_name+ \
                                          " from database model_info_db.")
    #then delete the model's relevant data in 'model_history_db'
    history_db = db_account.database('model_history_db')
    #get all history records in 'model_history_db'
    selector = {'owner': user.username,'model_name': model_name, 'type': 'history'} 
    sort = [ {'owner':'desc'}, {'model_name': 'desc'}, {'type':'desc'} ]
    fields = ['_id', '_rev']
    documents = query(history_db, selector=selector, sort=sort )['docs']
    for doc in documents:
        try_delete_history = history_db.delete(doc['_id'], params={'rev': doc['_rev']})
        #if delete history data is not successful, raise an exception
        if try_delete_history.status_code != 200:
            raise e.UnknownDatabaseError("Unable to delete "+model_name+ \
                                          "'s history records from database 'model_history_db'."
                                          " Reason: " + try_delete_history.text)

def update_model_in_database(document_id, document_content):
    """
    Updata a model document to 'model_info_db'.

    Raises:
    ------
    UnknownDatabaseError
    """
    db = db_account.database('model_info_db')
    try_put = db.put(document_id, params=document_content)
    if try_put.status_code != 201:
        raise e.UnknownDatabaseError("Failed to update model "+document_content['model_name']+ \
                                      " in  model_info_db database. Reason: "+ try_put.text)
    return try_put.json()

def create_model_in_database(document_content):
    """
    Create a model document to 'model_info_db'.

    Raises:
    ------
    UnknownDatabaseError
    """
    db = db_account.database('model_info_db')
    try_create = db.post('', params=document_content)
    if try_create.status_code != 201:
        raise e.UnknownDatabaseError("Failed to create model "+document_content['model_name']+ \
                                      " in  model_info_db database. Reason: "+ try_create.text)
    return try_create.json()

def update_create_user_in_database(document_id, document_content):
    """
    Update/create a user document to 'user_db'.

    Raises:
    ------
    UnknownDatabaseError
    """
    db = db_account.database('user_db')
    try_put = db.put(document_id, params=document_content)
    if try_put.status_code != 201:
        raise e.UnknownDatabaseError("Failed to update/create user "+document_content['username']+ \
                                      " in user_db database. Reason: "+ try_put.text)
    return try_put.json()

def retrieve_history(model, behaviour, sort):
        """
        Get model's history records from Cloudant 'model_info_db' database.

        Raises:
        -------
        UnknowDatabaseError 
        """
        data_db = db_account.database('model_history_db')
        if behaviour == 'all':
            query_sort = [ 
                           {'owner': sort}, 
                           {'model_name':sort},
                           {'creation_time':sort},
                           {'type': sort}
                         ]
            index = { 
                     'owner': model.owner.username, 
                     'model_name':model.model_name,
                     'creation_time':{ "$gt": None },
                     'type': 'history'
                    }
        else:
            query_sort = [ 
               {'owner': sort}, 
               {'model_name':sort},
               {'creation_time':sort}
             ]
            index = { 
                     'owner': model.owner.username, 
                     'model_name':model.model_name,
                    'behaviour': behaviour,
                     'creation_time':{ "$gt": None }

                    }
        fields = ['behaviour', 'value', 'creation_time']
        try: 
            records = query(data_db, index, fields=fields, sort=query_sort)['docs']
            return records
        except e.UnknownDatabaseError as error:
            raise e.UnknownDatabaseError('Retrieving history records failed: '+error.msg)


def retrieve_history_record(model, behaviour, creation_time):
    """"
    Get model's history record at a specific time.
    """
    data_db = db_account.database('model_history_db')
    index = { 
             'owner': model.owner.username, 
             'model_name': model.model_name,
             'creation_time': creation_time,
             'behaviour': behaviour
            }
    query_sort = [ 
               {'owner': 'desc'}, 
               {'model_name':'desc'},
               {'creation_time':'desc'},
               {'behaviour': 'desc'}
             ]
    if behaviour == 'refresh':
        #if behaviour is refreshing, 
        #we might also want the source used to refresh
        fields = ['value', 'source']
    else:
        fields = ['value']
    try: 
        records = query(data_db, index, fields=fields, sort=query_sort)['docs']
        return records
    except e.UnknownDatabaseError as error:
        raise e.UnknownDatabaseError('Retrieving history record at time:'+\
                                     creation_time+' failed: '+error.msg)
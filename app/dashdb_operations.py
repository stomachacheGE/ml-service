# -*- coding: utf-8 -*-
"""
Created on Wed Oct 21 17:18:21 2015

@author: pool84
"""

import requests
import ast
import re
import shutil
import os
import exceptions as e


def runR(script, user):
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    params = {'cmd':'RScriptRunScript', 
          'command':script,
          'fileName':'',
          'profileName':'BLUDB'}
    url = 'https://'+user.dashDB_service_address+':8443/console/blushiftservices/BluShiftHttp.do'
    r = requests.request('POST', url, params=params,headers=headers,auth=(user.dashDB_service_user,user.dashDB_service_pwd))
    if r.status_code != 200:
        raise e.UnknownDashdbError('Running R script failed. Reason: '+r.text)
    else:
        if 'items' in r.json().keys():
            return r.json()['items']
        else:
            raise e.UnknownDashdbError('Running R script failed. Cannot \
                                        retrieve information from: '+r.text)

def runSQL(sql, user):
    """
    Run SQL in user's dashdb service instance

    Raises:
    ------
    UnknownDashdbError
    """
    params = {'sql':sql, 
          'dbProfileName':'BLUDB',
          'RSBufferingType':'FLAT_ROWS',
          'cmd':'execSQL',}
    url = 'https://'+user.dashDB_service_address+':8443/services/healthsnapshot/HealthViewsResultSetDataProvider.form'
    res = requests.request('GET', url, params=params,auth=(user.dashDB_service_user,user.dashDB_service_pwd))
    if res.status_code != 200:
        raise e.UnknownDashdbError('Running SQL failed. Reason: '+res.text)
    else:
        return res.json()

def model_create(input_table, target_column, primary_key, model_name, user):
    """Create a decision tree model in Dashdb.

    Returns:
    ------
    dict 
        return {'message': 'Ok'} if model creation succeeds

    Raises:
    -----
    UnknownDashdbError
    """
    with open ('./app/static/Rscripts/TREE_model_creation.R', "r") as myfile:
        script=myfile.read().replace('<targetcolumn>',str(target_column))
        script=script.replace('<intable>',str(input_table))
        script=script.replace('<primary_key>',str(primary_key))
        script=script.replace('<model_name>',str(model_name))
    #get the R console output
    try:
        res = runR(script, user)
        #parse the output
        output = parse(res)
        return output
    except e.UnknownDashdbError as error:
        raise e.UnknownDashdbError(msg='Create model failed with reson: '+ error.msg)

def batch_score(model_name, input_table, primary_key ,table_name, user):
    """
    Score a dashdb model with input table.

    Returns:
    ------
    dict
        This dict has two keys:
          message: 'OK' if score succesfully
          table_name: the table name of the result table

    """
    with open ('./app/static/Rscripts/TREE_batch_score.R', "r") as myfile:
        script=myfile.read().replace('<model_name>',str(model_name))
        script=script.replace('<intable>',str(input_table))
        script=script.replace('<primary_key>',str(primary_key))
        if table_name:
            script=script.replace('<custom_name>', 'TRUE')
            script=script.replace('<table_name>',str(table_name))
        else:
            script=script.replace('<custom_name>', 'FALSE')
    try:
        res = runR(script, user)
        res = parse(res)
        return res
    except e.UnknownDashdbError as error:
        raise e.UnknownDashdbError(msg='batch scoring failed with reson: '+ error.msg)

def real_time_score(model_name, headers, datas, user, table_name):
    """
    Score a dashdb model with input data.

    Returns:
    ------
    list 
        Each item of the list is also a list, 
        which is class predicted by this model.
        (Since this is a decision tree model, output is class)
    """
    #fisrtly we have to change the inputs format 
    #so that we can use it as R script
    #for example, headers = ['sex', 'amount'], datas = [['Male', 2],['Female', 3]]
    #after formatting, formatted = "sex=c('Male', 'Female'), amount=c(2,3), ID=c(0,1)"
    formatted_table_values = []
    for number in range(len(headers)):
        column_values = []
        for data in datas:
            if isinstance(data[number], unicode):
                column_values.append(data[number].encode('ascii'))        
            else:
                column_values.append(data[number])
        if isinstance(column_values[0], str):
            formatted_column_values = str(column_values).strip('[]')
        else:
            formatted_column_values = ','.join([str(i) for i in column_values])
        equition = "%s=c(%s)" % (headers[number], formatted_column_values)
        formatted_table_values.append(equition) 
    #generate ID column for input data
    IDs = range(len(datas))
    id_equition = "ID=c(%s)" % (','.join([str(i) for i in IDs]))
    formatted_table_values.append(id_equition)
    formatted = ', '.join(formatted_table_values)

    with open ('./app/static/Rscripts/TREE_score.R', "r") as myfile:
        script=myfile.read().replace('<model_name>', str(model_name))
        if table_name:
            script=script.replace('<custom_name>', 'TRUE')
            script=script.replace('<table_name>',str(table_name))
        else:
            script=script.replace('<custom_name>', 'FALSE')
        script=script.replace('<value>',str(formatted))
    try:
        res = runR(script, user)
        res = parse(res)
        return res['output']
    except e.UnknownDashdbError as error:
        raise e.UnknownDashdbError(msg='Real time scoring failed with reson: '+ error.msg)
    
def metadata(model_name, user):
    """
    Retrieve metadata of a given model.

    Raises:
    -------
    UnknownDashdbError
    """
    with open ('./app/static/Rscripts/TREE_metadata.R', "r") as myfile:
        script=myfile.read().replace('<model_name>',str(model_name))
    try:
        res = runR(script, user)
        metadata = parse(res)
        return metadata
    except e.UnknownDashdbError as error:
        raise e.UnknownDashdbError(msg='Retrieving metadata failed with reson: '+ error.msg)

def retrieve_models(user):
    """
    Retrieve deployed models on a user's dashdb instance.

    Returns:
    -------
    list
        each item of the list is a model name

    Raises:
    -------
    UnknownDashdbError
    """
    with open ('./app/static/Rscripts/retrieve_models.R', "r") as myfile:
        script=myfile.read()
    try:
        res = runR(script, user)
        models = parse(res)
        return models['models']
    except e.UnknownDashdbError as error:
        raise e.UnknownDashdbError(msg='Retrieving models failed with reson: '+ error.msg)

# def get_columns(model_name, user):
#     with open ('./app/static/Rscripts/get_columns.R', "r") as myfile:
#         script=myfile.read().replace('<model_name>',str(model_name))
#     res = runR(script, user)['items']
#     print res
#     columns = parse(res)
#     return columns
    
# def show_tables(user):
#     with open ('./app/static/Rscripts/show_tables.R', "r") as myfile:
#         script=myfile.read()
#     res = runR(script, user)['items']
#     print res
#     tables = parse(res)
#     return tables
    
def delete_tables(table_names, user):
    """
    Delete a specific table on a user's dashdb instance.

    Params:
    -------
    table_names: list
        each item of the list is a table name
    user: User object

    Returns:
    -------
    dict
        {'message': 'Ok'} if succeeds
    Raises:
    -------
    UnknownDashdbError
    """
    table_names_str = str(table_names).strip('[]')
    with open ('./app/static/Rscripts/delete_tables.R', "r") as myfile:
        script=myfile.read().replace('<table_names>',str(table_names_str))
    try:
        res = runR(script, user)['items']
        message = parse(res)
        return message
    except e.UnknownDashdbError as error:
        raise e.UnknownDashdbError(msg='Deleting tables '+table_names+' failed with reson: '+ error.msg)

def delete_model(model_name, user):
    """
    delete a decision tree model in Dashdb.

    Returns:
    ------
    dict 
        {'message': 'Ok'} if succeeds

    Raises:
    -----
    UnknownDashdbError
    """
    with open ('./app/static/Rscripts/delete_model.R', "r") as myfile:
        script=myfile.read().replace('<model_name>',str(model_name))
    try:
        res = runR(script, user)
        message = parse(res)
    except e.UnknownDashdbError as error:
        raise e.UnknownDashdbError(msg='Deleting model'+model_name+' failed with reson: '+ error.msg)

def visualize(model_name, user):
    """
    visualize decision tree model in Dashdb.
    The visualization image is stored in folder 'outputs' 
    with filename 'user_model_name.jpg'

    Raises:
    -----
    UnknownDashdbError
    """
    path = './app/static/Rscripts/TREE_visualization.R'
    with open (path, "r") as myfile:
        script=myfile.read().replace('<modelname>',str(model_name))
    res = runR(script, user)
    path = get_pic_path(res)
    url = 'https://'+user.dashDB_service_address+':8443/console/services/RModeldownload'
    params = {'path':path}
    pic = requests.request('GET', url, params=params, stream=True, 
                            auth=(user.dashDB_service_user,user.dashDB_service_pwd))
    if pic.status_code != 200:
        #if downloading the image from Dashdb is not successful,
        #raise an exception
        raise e.UnknownDashdbError('Failed to get visualization results from DashDB. Reason: '+r.text)
    current_dir = os.getcwd()
    pic_name = os.path.join(current_dir, 'outputs/'+user.username+model_name+'.jpg')
    with open(pic_name, 'wb') as f:
        pic.raw.decode_content = True
        shutil.copyfileobj(pic.raw, f)    


# def get_name(res):
#     dict_res = ast.literal_eval(res)
#     model_re = dict_res['RModelOutput']
#     models = re.findall(r'\"(.+?)\"',model_re)
#     return models
    
def get_pic_path(res):
    """
    Parse visualization picture path from Dashdb console output.

    Returns:
    ------
    str

    Raises:
    ------
    UnknownDashdbError
        if running R script failed, this error is raised
        with error message from console output
    """
    output = ast.literal_eval(res)['filename']
    if not output:
        #if nothing in 'RModelOutput', then running R script is not successful
        #raise an error for this case
        error = ast.literal_eval(res)['filename']
        raise e.UnknownDashdbError('Running R script failed. Console Output: ' + error)
    #if running R script succeeds, return output as a dict
    path_re = output[0]
    path = path_re.replace("\\","")
    return path
        
def parse(res):
    """
    Parse useful information from Dashdb console output.

    Returns:
    ------
    dict 

    Raises:
    ------
    UnknownDashdbError
        if running R script failed, this error is raised
        with error message from console output
    """
    output = ast.literal_eval(res)['RModelOutput']
    if not output:
        #if nothing in 'RModelOutput', then running R script is not successful
        #raise an error for this case
        error = ast.literal_eval(res)['RModelError']
        raise e.UnknownDashdbError('Running R script failed. Console Output: ' + error)
    #if running R script succeeds, return output as a dict
    output_dict = ast.literal_eval(output)
    return output_dict


def get_table_details(table_name, user):
    """
    Retrieve a table details from user's dashdb instance

    Returns:
    -------
    list:
        each item of the list correspons to a table row

    Raises:
    -------
    UnknownDashdbError
    """
    #firstly try to retrieve the table from user's tables
    #which means the database schema is user's dashdb username
    try:
        sql = 'SELECT * FROM ' + table_name
        res = runSQL(sql, user)
        if not res['items']:
            #if 'items' of the response body is empty,
            #it means can not retrieve this table from current schema
            #then we try to retrieve this table from 'SAMPLES' schema
            sql = 'SELECT * FROM SAMPLES.' + table_name
            res = runSQL(sql, user)
    except e.UnknownDashdbError as error:
        #reraise error if running SQL failed
        raise error
    if not res['items']:
        #if 'items' of the response body is still empty,
        #then it means the table does not exist 
        #in neither user schema or SAMPLES schema
        raise e.UnknownDashdbError(msg='Can not find table '+table_name+'. \
                                        Reason:'+res)
    else:
        #otherwise return table content 
        #and change column name to lowercase
        records = []
        for item in res['items']:
            records.append(dict((k.lower(), v) for k,v in item.iteritems()))
        return records

def get_table_names(is_sample, user):
    """
    Retrieve all table names from user's dashdb instance

    Params:
    -------
    is_sample: boolean
        it indicates to retrieve table names in SAMPLES schema
        or in user's dashdb username schema

    Returns:
    -------
    list:
        each item of the list is a table name

    Raises:
    -------
    UnknownDashdbError
    """
    if is_sample:
        schema = 'SAMPLES'
    else:
        schema = user.dashDB_service_user
    try:
        sql = 'Select TABNAME from syscat.tables where TABSCHEMA=\''+schema.upper()+'\''
        res = runSQL(sql, user)
    except e.UnknownDashdbError as error:
    #reraise error if running SQL failed
        raise e.UnknownDashdbError('Getting table names failed: '+error.msg)
    tables = []
    for table in res['items']:
        tables.append(table['TABNAME'])
    return tables
    
def get_column_names(table_name, user):
    """
    Retrieve all cloumn names of a table from user's dashdb instance

    Returns:
    -------
    list:
        each item of the list is a cloumn name

    Raises:
    -------
    UnknownDashdbError
    """
    sql = 'SELECT COLNAME from SYSCAT.COLUMNS where TABNAME=\''+table_name+'\''
    try:    
        res = runSQL(sql, user)
        columns = []
        for column in res['items']:
            columns.append(column['COLNAME'])
        return columns
    except e.UnknownDashdbError as error:
    #reraise error if running SQL failed
        raise e.UnknownDashdbError('Getting column names failed: '+error.msg)


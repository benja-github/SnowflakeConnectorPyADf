import logging
from datetime import datetime
import azure.functions as func
import json 
import os
import sys
import re
import snowflake.connector

# For Below module see: 
# https://docs.microsoft.com/en-gb/azure/storage/blobs/storage-quickstart-blobs-python
from azure.storage.blob import baseblobservice

__validBlobFolderNameRegex = r'^[A-Za-z0-9_-]+$'
# The parameter name corresponds to a restricted Snowflake unquoted identifier
# https://docs.snowflake.net/manuals/sql-reference/identifiers-syntax.html
__validParameterNameRegex = r'^[A-Za-z_]{1}[A-Za-z0-9_-]*$'
# This is pretty restrictive
__validParameterTypeRegex = r'^VARCHAR|NUMBER$'
__validParameterValueRegex = r'^[A-Za-z0-9./\\ :_-]+$'

def write_to_log(message,severity='INFO'):

    # Rudimentary logging function for development/local debugging
    now = datetime.now()
    now_string = now.strftime('%d-%m-%Y, %H:%M:%S')
    log_message='{0}::{1} (UTC): {2}'.format(severity,now_string,message)
    
    if severity.upper=='CRITICAL':
        logging.log(logging.CRITICAL,log_message)
    elif severity.upper=='ERROR':
        logging.log(logging.ERROR,log_message)
    elif severity.upper=='WARNING':
        logging.log(logging.WARNING,log_message)
    elif severity.upper=='DEBUG':
        logging.log(logging.DEBUG,log_message)
    else: #severity.upper='INFO':
        logging.log(logging.INFO,log_message)
    
def _generate_store_procedure_blob_file_path(*args,**kwargs):

    # Generate path to stored procedure file, validating constituent parts along the way
    blob_file_path=''
    for path_part in args:
        if not re.match(__validBlobFolderNameRegex,path_part):
            write_to_log('invalid object name in blob_file_path: {0} '.format(path_part),'ERROR')
            sys.exit()
        blob_file_path=blob_file_path+'/'+path_part
    
    blob_file_path=blob_file_path[1:]
    return blob_file_path

def read_content_from_blob_async(storage_account_connection_string, blob_container_name, blob_file_name): #, storage_account_container_name, storage_account_blob_file_path):

    # Create the BlobServiceClient object which will be used to create a container client
    blob_service = baseblobservice.BaseBlobService(connection_string=storage_account_connection_string)
    
    #generator = blob_service.list_blob_names('storedprocedures')
    #for blob_container in generator:
    #    write_to_log(blob_container)

    write_to_log('SQL FILE PATH & NAME: {0}::{1}'.format(blob_container_name,blob_file_name))
    sql_blob = blob_service.get_blob_to_text(blob_container_name,blob_file_name)
    
    sql_text = sql_blob.content

    return sql_text

def split_sql_commands(sql_text):
    
    # Takes string of 1+ sql commands, splits by ';' and removes leading/trailing newlines.

    # Split string by ';'
    sql_commands_raw = sql_text.split(';')

    # lambda function to remove leading/trailing new lines 
    clean = lambda x: x.strip('\n').strip(' ')

    # apply lambda function to list of sql strings
    sql_commands = list(map(clean,sql_commands_raw))

    sql_commands = [sql for sql in sql_commands if len(sql)>0]

    #write_to_log(sql_commands)

    return sql_commands


def run_snowflake_commands(snowflake_connection_string, set_variable_command, sql_commands):

    # expects a Snowflake connection string in format "account=<account_name>;host=<hostname>;user=<user_name>;password=<pwd>"
    # N.B c# connector account in format <your_account_name>.<region_id>.<cloud>.snowflakecomputing.com
    # nut python needs <your_account_name>.<region_id>.<cloud> - i.e. w/o .snowflakecomputing.com
    # create list of constituent key=value parts
    sfconn_list = snowflake_connection_string.split(';')
    # convert to list of key,value tuples
    sfconn_working = [x.split('=') for x in sfconn_list]
    # create new empty dict
    sfconn_details = {}
    # populate dict from list of tuples, adjusting hostname for python connector
    for k,v in sfconn_working:
        sfconn_details[k]=sfconn_details.get(k,v)
    
    sf_user=sfconn_details['user']
    sf_password=sfconn_details['password']
    try:
        sf_account=sfconn_details['host'].replace('.snowflakecomputing.com','')
    except:
        write_to_log('error getting sf_account {0}'.format(sfconn_details['host']))

    #write_to_log('this doesn\'t:')
    write_to_log('SF USER: {0}'.format(sf_user))
    write_to_log('SF  PWD: {0}'.format(sf_password))
    write_to_log('SF ACCT: {0}'.format(sf_account))

    ctx = snowflake.connector.connect(
        user=sf_user,
        password=sf_password,
        account=sf_account
        )


    try:
        # can do this as '' and None evaluate to False
        if set_variable_command:
            cs = ctx.cursor()
            cs.execute(set_variable_command)
            one_row = cs.fetchone()
            write_to_log(one_row[0])
            cs.close()

        # Run all save last sql command
        for sql_command in sql_commands[:-1]:
            cs = ctx.cursor()
            cs.execute(sql_command)
            cs.close()

        # Run final sql command & retrieve resultset
        cs = ctx.cursor()
        sql_resultset = cs.execute(sql_commands[-1])

    finally:
        cs.close()
    
    ctx.close()

    return sql_resultset

def generate_set_variables_command(parameters):

    param_names = ''
    param_vals = ''

    for parameter in parameters:
        p_name = parameter['name']
        p_value = parameter['value']
        p_type = parameter['type'].upper()
        if not re.match(__validParameterNameRegex,p_name) and re.match(__validParameterValueRegex,p_value):
            write_to_log('invalid parameter: {0}={1)'.format(p_name, p_value),'ERROR')
            sys.exit()
        else:
            # NOT SURE ABOUT THIS - MIGHT NEED TO DO MORE STUFF RE DATATYPES
            param_names=param_names+'"'+p_name+'", '
            param_vals=param_vals+'\''+p_value+'\', '    
            
    param_names=param_names[:-2]
    param_vals=param_vals[:-2]

    set_variables_command = 'SET ({0})=({1})'.format(param_names,param_vals)

    return set_variables_command

def run(req: func.HttpRequest):
    # Log start time
    write_to_log('Started funcion Run()')
    
    # Read the POST body and convert to JSON object
    req_body=str(req.get_body(),'UTF-8')
    request_json = json.loads(req.get_body())
    
    #try:
    # Get the required inputs and validate them
    config_keys=['snowflakeConnectionString',
                'storageAccountConnectionString',
                'storageAccountContainerName']
    
    expected_inputs=['databaseName',
                    'schemaName',
                    'storedProcedureName']
    
    config = {}
    #  Get app config values
    for i in config_keys:
        config_value=os.getenv(i)
        if not config_value:     
            write_to_log('{0} not found in config'.format(i),'ERROR')
            sys.exit()
        
        config[i]=config_value
    # Get mandatory inputs from POST json 
    for i in expected_inputs:
        input_value=request_json[i]
        if not input_value:     
            write_to_log('{0} not found in config'.format(i),'ERROR')
            sys.exit()
        
        config[i]=input_value
            
    write_to_log('CONFIG {0}'.format(config))

    storage_account_blob_file_path = _generate_store_procedure_blob_file_path(config['storageAccountContainerName'],config['databaseName'],config['schemaName'])
    
    write_to_log(storage_account_blob_file_path)

    sql_text = read_content_from_blob_async(config['storageAccountConnectionString'],storage_account_blob_file_path,config['storedProcedureName']+'.sql')        

    sql_commands = split_sql_commands(sql_text)

    # convert any parameters to SQL variables
    set_variables_command=''
    parameters=request_json.get('parameters')
    if parameters:
        set_variables_command=generate_set_variables_command(parameters)
    # And on THAT bombshell....
    # 2/2/2020 - finished.  
    # START HERE!
    
    result_set = run_snowflake_commands(config['snowflakeConnectionString'],set_variables_command,sql_commands)
    write_to_log(result_set)

    #except Exception as e: 
    #    write_to_log(str(e),'ERROR')
    
    return result_set
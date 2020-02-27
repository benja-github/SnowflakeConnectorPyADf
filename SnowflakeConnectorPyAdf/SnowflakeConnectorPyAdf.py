import logging
from datetime import datetime
import azure.functions as func
import json 
import os
import sys

__validBlobFolderNameRegex = r'^[A-Za-z0-9_-]+$'
# The parameter name corresponds to a restricted Snowflake unquoted identifier
# https://docs.snowflake.net/manuals/sql-reference/identifiers-syntax.html
__validParameterNameRegex = r'^[A-Za-z_]{1}[A-Za-z0-9_-]*$'
# This is pretty restrictive
__validParameterTypeRegex = r'^VARCHAR|NUMBER$'
__validParameterValueRegex = r'^[A-Za-z0-9./\\ :_-]+$'

def write_to_log(message,severity='INFO'):
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
    

def Run(req: func.HttpRequest):
    # Log start time
    write_to_log('Started funcion Run()')
    
    # Read the POST body and convert to JSON object
    req_body=str(req.get_body(),'UTF-8')
    request_json = json.loads(req.get_body())
    
    try:
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
    
    except Exception as e: 
        write_to_log(str(e),'ERROR')
    
    return 'Done'
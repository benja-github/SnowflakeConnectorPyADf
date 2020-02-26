import logging
from datetime import datetime
import azure.functions as func

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
    logging.info(log_message);

def Run(req: func.HttpRequest):
    write_to_log('Started funcion Run()');
    req_body=str(req.get_body(),'UTF-8')
    return req_body
import logging

import azure.functions as func

__validBlobFolderNameRegex = r'^[A-Za-z0-9_-]+$'
# The parameter name corresponds to a restricted Snowflake unquoted identifier
# https://docs.snowflake.net/manuals/sql-reference/identifiers-syntax.html
__validParameterNameRegex = r'^[A-Za-z_]{1}[A-Za-z0-9_-]*$'
# This is pretty restrictive
__validParameterTypeRegex = r'^VARCHAR|NUMBER$'
__validParameterValueRegex = r'^[A-Za-z0-9./\\ :_-]+$'

def Run(req: func.HttpRequest):
    req_body=str(req.get_body(),'UTF-8')
    return req_body
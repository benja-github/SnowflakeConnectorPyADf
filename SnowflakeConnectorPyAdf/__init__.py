import logging

import azure.functions as func

# Following needed, at least locally, to import modules that
# are part of project (i.e. in same location as __inti__.py)
import os
import sys
from sys import path

dir_path = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, dir_path)
# import of project modules must go below here

import SnowflakeConnectorPyAdf

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    ret_val = SnowflakeConnectorPyAdf.run(req)
    
    return func.HttpResponse(ret_val)
    #func.HttpResponse('\n'.join(ret_val))
    #else:
    #    return func.HttpResponse(
    #         "Please pass a name on the query string or in the request body",
    #         status_code=400
    #    )

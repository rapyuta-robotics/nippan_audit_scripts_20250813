# Import functions
from .a_http_helpers import (
    http_get_all,
    http_post
)

# Import configurations
import config

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#       Check if any audit is ongoing
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def ongoing_audit_check():
    # Get all ongoing audit
    params = {
        "status": [
            "RECEIVED","AUDITING1","ALLOCATED1","EXCEPTION1",
            "AUDITING2","ALLOCATED2","EXCEPTION2","COMPLETED2",
            "AUDITING3","ALLOCATED3","EXCEPTION3","COMPLETED3"
        ]
    }
    audits=http_get_all("WMS",config.AUDIT_URL,params)
    if audits is False:
        print("Audit ongoing error: Could not get audits")
        return False

    # Check that no audit is ongoing
    if audits:
        print("Audit ongoing error: Some audits are ongoing, cannot run this script")
        return False
    else:
        return True

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#       Upload a container audit
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def upload_an_audit(audit_name:str,containers):
    # Create the upload payload
    data={
        "name": audit_name,
        "separateEmpty": False,
        "containers": containers,
        "type": "CONTAINER"
    }

    # Upload the audit
    success=http_post("WMS",config.AUDIT_CREATE_URL,data)

    # Return result
    if success is False:
        print("Audit upload error: Audit {audit_name} could not be uploaded, cancel all uploaded audits and re-run the script")
    return success
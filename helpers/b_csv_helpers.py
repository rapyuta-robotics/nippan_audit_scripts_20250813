# Import functions
from .a_http_helpers import (
    http_post,
    http_get,
)

#Import libraries
import requests
import os
import time

# Import configurations
import config

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#       Excecute file download
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def download_csv_file(download_type:str,file_path:str,audit_ids= None):
    #Decode upload type
    if download_type=="Container Inventory":
        type="ASRSExportCSVContainerInventory"
        data={
            "type": type,
            "data": {
                "report_lang": "en"
            }
        }
    elif download_type=="Audit" and audit_ids:
        type="ASRSExportCSVAuditReports"
        data={
            "type": type,
            "data": {
                "report_lang": "en",
                "audits": audit_ids
            }
        }
    else:
        print("Download document error: type unknown")
        return False

    #Create the operation and save the ID
    response=http_post("WMSINT",config.OPERATION_URL,data)
    if response is False:
        print(f"Download document error: Document {file_path} could not be downloaded with {download_type} workflow: Could not POST operation")
        return False
    execution_id=response['id']
    
    #Check the operation status
    while(True):
        #Query the operation
        data={
            "id": execution_id
        }
        response = http_get("WMSINT",config.OPERATION_URL,data)
        if response is False:
            print(f"Download document error: Document {file_path} could not be downloaded with {file_path} workflow: Could not get operation")
            return False

        #Extract the execution status
        try:
            operation_status=response['results'][0]['status']
        except:
            print(f"Download document error: Document {file_path} could not be downloaded with {file_path} workflow: Operation status not found in operation")
            return False

        if operation_status in {"PENDING", "ACCEPTED", "RUNNING"}:
            time.sleep(1)
        elif operation_status=="FAILED":
            print(f"Download document error: Document {file_path} could not be downloaded with {file_path} workflow: Operation status is FAILED")
            return False
        else:
            try:
                # Get operation ID
                operation_file_id=response['results'][0]['result']['document_id']

                # Fetch and save the document
                success=fetch_a_document(operation_file_id,file_path)
                return success
            except:
                print(f"Download document error: Document {file_path} could not be downloaded with {file_path} workflow: Operation file id not found in operation")
                return False

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#       Excecute file upload
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def upload_csv_file(upload_type:str,upload_name:str,file_path:str):
    #Decode upload type
    if upload_type=="Items":
        type="ASRSImportCSVItems"
        upload_size=2000000
    elif upload_type=="Containers":
        type="ASRSImportCSVContainers"
        upload_size=1000000
    elif upload_type=="Inventory":
        type="ASRSImportCSVInventory"
        upload_size=10000
    elif upload_type=="Orders":
        type="ASRSImportCSVOrders"
        upload_size=50000
    else:
        print("Upload document error: type unknown")
        return False

    #TBD
    #print("Do not forget to handle file size")

    #Store the document in Minio
    file_id=store_a_document(upload_name,file_path)

    if file_id is False:
        print(f"Upload document error: Document {upload_name} could not be uploaded with {upload_type} workflow: Could not store document in Minio")
        return False
    
    #Create the operation
    data={
        "type": type,
        "data": {
            "document_id": file_id,
            "report_lang": "en"
        }
    }
    response=http_post("WMSINT",config.OPERATION_URL,data)
    if response is False:
        print(f"Upload document error: Document {upload_name} could not be uploaded with {upload_type} workflow: Could not POST operation")
        return False
    execution_id=response['id']
    
    #Check the operation status
    while(True):
        #Query the operation
        data={
            "id": execution_id
        }
        response = http_get("WMSINT",config.OPERATION_URL,data)
        if response is False:
            print(f"Upload document error: Document {upload_name} could not be uploaded with {upload_type} workflow: Could not get operation")
            return False

        #Extract the execution status
        try:
            operation_status=response['results'][0]['status']
        except:
            print(f"Upload document error: Document {upload_name} could not be uploaded with {upload_type} workflow: Operation status not found in operation")
            return False

        if operation_status in {"PENDING", "ACCEPTED", "RUNNING"}:
            #print(f"{upload_type} upload still running")
            time.sleep(1)
        elif operation_status=="FAILED":
            print(f"Upload document error: Document {upload_name} could not be uploaded with {upload_type} workflow: Operation status is FAILED")
            return False
        else:
            try:
                operation_error_count=response['results'][0]['result']['error_count']
                if operation_error_count !=0:
                    print(f"Upload document error: Document {upload_name} could not be uploaded with {upload_type} workflow: Error happened during file upload")
                    return False
                else:
                    return True
            except:
                print(f"Upload document error: Document {upload_name} could not be uploaded with {upload_type} workflow: Operation error count not found in operation")
                return False

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#       Store a document to Minio
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def store_a_document(upload_name: str, file_path: str):
    try:
        with open(file_path, 'rb') as file:
            files = {'file': (os.path.basename(file_path), file, 'text/csv')}
            data = {'key_prefix': 'Generated CSVs', 'key_name': upload_name}
            
            document_url = config.WMS_INTERFACE_URL + "/" + config.DOCUMENT_URL
            response = requests.post(
                document_url,
                files=files,
                data=data,
                headers={"Authorization": config.ENV_BEARER},
                timeout=10
            )
            response.raise_for_status()
            
            json_data = response.json()
            file_id = json_data.get('id')
            if not file_id:
                raise ValueError("File ID not found in the response")
            
            return file_id
    except Exception as e:
        print(f"Upload document error: {e}")
        return False
    
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#       Fetch a document from Minio
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def fetch_a_document(retrieve_id: str, file_path: str):
    try:
        document_url = config.WMS_INTERFACE_URL + "/" + config.DOCUMENT_URL + retrieve_id + "/file/"

        response = requests.get(
            document_url,
            headers={"Authorization": config.ENV_BEARER},
            timeout=10
        )

        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        with open(file_path, "wb") as f:
            for chunk in response.iter_content(65536):
                if chunk:
                    f.write(chunk)

    except Exception as e:
        print(f"Fetch document error: {e}")
        return False
# Import libraries
import httpx
import json

# Import configurations
import config

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#       Decode the server address
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def url_decode(client:str):
    #"WMS" parameter is used for WMS
    if client=="WMS":
        base_url=config.WMS_URL
    
    #"OWM" parameter is used for OWM
    elif client=="OWM":
        base_url=config.OWM_URL
    
    #"WMSINT" parameter is used for WMSINT
    elif client=="WMSINT":
        base_url=config.WMS_INTERFACE_URL
    
    #Unknow server case handling
    else:
        print(f"http post unknown server: {client}")
        return False
    return base_url

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#       POST request function
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def http_post(client:str,endpoint:str,data:json):
    #Decode the server address
    base_url=url_decode(client)

    #Set a longer timeout (30 seconds)
    timeout = httpx.Timeout(60.0)

    #Make the POST request
    with httpx.Client(base_url=base_url, timeout=timeout, headers={"Authorization": config.ENV_BEARER}) as client:
        #Try to post
        try:
            response=client.post(endpoint,json=data)
            response.raise_for_status()

            # If the status is 204 (No Content), skip JSON parsing.
            if response.status_code == 204:
                return {"status": "success", "code": 204}
        
            json_data=response.json()
            return json_data
        
        #Handle exceptions
        except Exception as exception:
            print(f"http post error: {exception}")
            return False

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#       POST request function
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def http_post_no_error(client:str,endpoint:str,data:json):
    #Decode the server address
    base_url=url_decode(client)

    #Set a longer timeout (30 seconds)
    timeout = httpx.Timeout(30.0)

    #Make the POST request
    with httpx.Client(base_url=base_url, timeout=timeout, headers={"Authorization": config.ENV_BEARER}) as client:
        #Try to post
        try:
            response=client.post(endpoint,json=data)
            response.raise_for_status()

            # If the status is 204 (No Content), skip JSON parsing.
            if response.status_code == 204:
                return {"status": "success", "code": 204}
        
            json_data=response.json()
            return json_data
        
        #Handle exceptions
        except Exception as exception:
            # print(f"http post error: {exception}")
            return False

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#       PATCH request function
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def http_patch(client: str, endpoint: str, data: json):
    # Decode the server address
    base_url = url_decode(client)

    # Set a longer timeout (30 seconds)
    timeout = httpx.Timeout(30.0)

    # Make the PATCH request
    with httpx.Client(base_url=base_url, timeout=timeout, headers={"Authorization": config.ENV_BEARER}) as client:
        # Try to patch"Bearer autobootstrap"
        try:
            response = client.patch(endpoint, json=data)
            response.raise_for_status()
            json_data = response.json()
            return json_data
        
        # Handle exceptions
        except Exception as exception:
            print(f"http patch error: {exception}")
            return False

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#       GET request function
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def http_get(client:str,endpoint:str,params:dict):
    #Decode the server address
    base_url=url_decode(client)

    #Set a longer timeout (30 seconds)
    timeout = httpx.Timeout(30.0)

    #Make the GET request
    with httpx.Client(base_url=base_url, timeout=timeout, headers={"Authorization": config.ENV_BEARER}) as client:
        #Try to get
        try:
            response=client.get(endpoint,params=params)
            response.raise_for_status()
            json_data=response.json()
            return json_data
        
        #Handle exceptions
        except Exception as exception:
            print(f"http get error: {exception}")
            return False

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#       GET request function with pagination
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def http_get_all(client:str,endpoint:str,params:dict):
    # Define the page size
    page_size=20000

    #Make a first get request with maximum page size
    pagination={
        "page": 1,
        "size": page_size
    }
    merged_params=pagination | params
    response=http_get(client,endpoint,merged_params)
    if response is False:
        return False

    #Extract items
    items=response['items']

    #extract page number
    pages=response['pages']

    #Iterate on pages
    for i in range(2,pages+1):
        print(f"long request: fetching {i}/{pages}")

        #Get following pages 
        pagination = {
            "page": i,
            "size": page_size
        }
        merge_params=pagination | params
        response=http_get(client,endpoint,merge_params)
        if response is False:
            return False
    
        #Add items to the previous ones
        items=items + response['items']

    #Return all items
    return items

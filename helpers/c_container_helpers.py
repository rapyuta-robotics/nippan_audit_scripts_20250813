# Import libraries
import os
import pandas as pd

# Import functions
from .a_http_helpers import http_get_all

# Import configurations
import config

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#       Get all ASRS SKU containers from WMS
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def get_all_asrs_containers():
    # Get all containers inside ASRS
    params={
        "parentName":config.ASRS_NAME
    }
    asrs_containers=http_get_all("WMS",config.CONTAINER_URL,params)
    if asrs_containers is False:
        print("Container error: Could not get cotnainers from WMS")
        return False
    elif (len(asrs_containers) == 0):
        print("Container error: There is not container in WMS")
        return False

    # Fattening the format
    asrs_containers_flat = [
        {
            "name": container.get("name"),
            "descriptorName": container.get("descriptor", {}).get("name")
        }
        for container in asrs_containers
    ]

    # Get all the container descriptors
    params={}
    container_descriptors=http_get_all("WMS",config.CONTAINER_DESCRIPTOR_URL,params)

    # Extract order bin descriptors and SKU bin descriptors
    order_container_descriptors = [
        descriptor for descriptor in container_descriptors
        if descriptor.get('isUsableForOrders', True)
    ]
    sku_container_descriptors = [
        d for d in container_descriptors
        if d.get('isItemContainable', False) and not d.get('isUsableForOrders', True)
    ]

    # Extract order descriptor names
    order_descriptor_names = {
        (d.get("name") or "").strip().casefold()
        for d in order_container_descriptors
        if d.get("name")
    }

    # Exclude order bins from bins in ASRS
    asrs_containers_sku=[
        container for container in asrs_containers_flat
        if (container.get("descriptorName") or "").strip().casefold() not in order_descriptor_names
    ]
    if not asrs_containers_sku:
        print("Container error: There is no SKU container in ASRS")
        return False

    # Build lookup: "descriptorName" -> partitions
    partitions_by_desc = {
        d["name"]: int(d.get("subDivisionLength", 1)) * int(d.get("subDivisionWidth", 1))
        for d in sku_container_descriptors
        if d.get("name")
    }

    # Add partitionNumber to each bin (defaults to 1 if descriptor missing)
    asrs_containers_sku = [
        {**b, "partitionNumber": partitions_by_desc.get(b.get("descriptorName"), 1)}
        for b in asrs_containers_sku
    ]

    # Save the containers as a CSV file
    try:
        pd.DataFrame(asrs_containers_sku).to_csv(config.ASRS_BIN_LIST_PATH, index=False)
        return asrs_containers_sku
    except Exception as e:
        print(f"Container error: Could not save containers as CSV: {e}")
        return False

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#       Script user configuration
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
AUDIT_TASK_NUMBER=1 #The number of audit tasks to generate
AUDIT_BIN_NUMBER=8  #The number of bins task to audit at once
UPLOAD_GENERATED_AUDITS=False #Should the script upload automatically to WMS the audit tasks
AUDIT_DESCRIPTOR_GROUP="日販"    #Should be CX or 日販 or CX日販

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#       Script static configuration
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ASRS setting
ASRS_NAME="RR ASRS 001"

# Environment configuration
ENV_URL="http://localhost"
ENV_TOKEN="autobootstrap"

# Container descriptor group settings
AUDIT_DESCRIPTOR_GROUPS=[
    {
        "group_name":"CX",
        "descriptor_names":[
            "CX Bin 1x1",
            "CX Bin 2x1",
            "CX Bin 2x2",
            "CX Bin 4x2"
        ],
        "cycle_number":1
    },
    {
        "group_name":"日販",
        "descriptor_names":[
            "日販 Bin 1x1",
            "日販 Bin 2x1",
            "日販 Bin 2x2",
            "日販 Bin 4x2"
        ],
        "cycle_number":2
    },
    {
        "group_name":"CX日販",
        "descriptor_names":[
            "CX日販 Bin 1x1",
            "CX日販 Bin 2x1",
            "CX日販 Bin 2x2",
            "CX日販 Bin 4x2"
        ],
        "cycle_number":2
    }
]
AUDIT_DESCRIPTOR_LIST = []
AUDIT_CYCLE_NUMBER = None
for group in AUDIT_DESCRIPTOR_GROUPS:
    if group["group_name"] == AUDIT_DESCRIPTOR_GROUP:
        AUDIT_DESCRIPTOR_LIST.extend(group["descriptor_names"])
        AUDIT_CYCLE_NUMBER = group["cycle_number"]

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#       Internal configuration
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# File path configuration
ASRS_BIN_LIST_PATH="./files/asrs_bin_list.csv"
ASRS_CURRENT_INVENTORY_PATH="./files/asrs_current_inventory.csv"
ASRS_INITIAL_INVENTORY_PATH="./files/asrs_initial_inventory_*.csv"
AUDIT_EXPORT_PATH="./files/audit_export.csv"
PER_BIN_AUDIT_REPORT="./results/Cycle1＆２実施状況(Bin別).csv"
PER_SLOT_AUDIT_REPORT="./results/Cycle1＆２実施状況(Slot別).csv"
AUDIT_NEXT_TASK_PATH="./results/次回棚卸し作業.csv"

# Service URL configuration
WMS_URL=ENV_URL+"/wms-server"
OWM_URL=ENV_URL+"/owm"
WMS_INTERFACE_URL = ENV_URL+"/wms-interface"

# Bearer configuration
ENV_BEARER="Bearer "+ENV_TOKEN

# WMS API URL configuration
CONTAINER_URL="/api/v1/containers"
CONTAINER_DESCRIPTOR_URL="/api/v1/containerDescriptors"
CONTAINER_TRANSACTION_URL="/api/v1/containerTransactions"
INVENTORY_TRANSACTION_URL="/api/v1/inventoryTransactions"
AUDIT_URL="/api/v1/audits"
AUDIT_CREATE_URL="/api/v1/audits/create"

# WMS interface API URL configuration
DOCUMENT_URL="databridge/v1/documents/"
OPERATION_URL="compute/v1/workflows/executions/"

# Audit config
DONE_AUDIT_STATUSES=["APPROVED","COMPLETED1"]

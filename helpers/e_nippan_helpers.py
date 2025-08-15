# Import functions
from helpers.a_http_helpers import http_get_all
from helpers.b_csv_helpers import download_csv_file
from helpers.c_container_helpers import get_all_asrs_containers
from helpers.d_audit_helpers import upload_an_audit

#Import libraries
from pathlib import Path
from datetime import datetime, timezone
import pandas as pd
import re
import os
import numpy as np
import random

# Import configurations
import config

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#       Get the initial container inventory CSV
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def save_container_inventory_csv():
    # Find matches for the initial container inventory CSV file
    matches = sorted(Path().glob(config.ASRS_INITIAL_INVENTORY_PATH))

    # Update the initial inventory if new bin stowed or unloaded
    if matches:
        print("Dowloading current container inventory CSV file...")

        # Save the current container inventory
        success=download_csv_file("Container Inventory",config.ASRS_CURRENT_INVENTORY_PATH)
        if success is False:
            return False

        # Read the current container inventory CSV file
        try:
            # Taking out all inventories not inside of ASRS
            df = pd.read_csv(config.ASRS_CURRENT_INVENTORY_PATH)
            df = df[df["Inventory MHE"].astype(str).str.strip() == "RR ASRS 001"]

            # Save the current inventory
            df.to_csv(config.ASRS_CURRENT_INVENTORY_PATH, index=False)
            return True
        except:
            print("Initial inventory CSV error: Could not save the current inventory CSV file")
            return False


    # Download the initial inventory
    else:
        print("Dowloading initial container inventory CSV file...")

        # Take current time
        now = datetime.now()

        # Calculate target file path
        file_path = config.ASRS_INITIAL_INVENTORY_PATH.replace("*", f"{now:%Y%m%d_%H%M%S}")

        # Save the current inventory as initial inventory
        success=download_csv_file("Container Inventory",file_path)
        if success is False:
            return False

        # Saving inventory files
        try:
            # Taking out all inventories not inside of ASRS
            df = pd.read_csv(file_path)
            df = df[df["Inventory MHE"].astype(str).str.strip() == "RR ASRS 001"]
            df["status"] = "Initial"  # add new column with the initial values for all rows. This tells that the bin from the start

            # Save the initial inventory
            df.to_csv(file_path, index=False)

            # Save a copy as current inventory
            df.to_csv(config.ASRS_CURRENT_INVENTORY_PATH, index=False)


            return True
        except:
            print("Initial inventory CSV error: Failed to clean the initial container invenotry CSV")
            return False

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#       Audit report CSV initialization
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def initalize_audit_report_csv():
    print("Initializing audit reports based on container inventory information...")

    # Getting all audit relevant containers from WMS
    containers=get_all_asrs_containers()
    if containers is False:
        return False

    # Create the initial per bin audit report file
    per_bin_audit_report_init = [
        {"Bin": c["name"],"Type":c["descriptorName"],"Slot数": c.get("partitionNumber")}
        for c in containers
    ]

    # Convert to dataframe
    per_bin_audit_report_init = pd.DataFrame(per_bin_audit_report_init)

    # Load the current CSV inventory
    try:
        current_container_inventory = pd.read_csv(config.ASRS_CURRENT_INVENTORY_PATH)
    except:
        print("Audit report initialization error: Could not load the current CSV inventory file")
        return False
    
    # Update the per bin lot audit report based on the initial inventory
    try:
        # Aggregate current inventory per Bin
        agg = (current_container_inventory.groupby(["Inventory container"])
                .agg(
                    商品数=("Inventory container", "size"),         # number of lines (SKUs) in the bin
                    総Pcs=("Inventory quantity", "sum"),         # total pieces in the bin
                )
                .reset_index())

        # Rename columns to match per_bin_audit_report_init keys
        agg = agg.rename(columns={
            "Inventory container": "Bin"
        })

        # Merge onto the per-bin template; fill missing with 0
        per_bin_audit_report_init = (
            per_bin_audit_report_init
                .merge(agg, on='Bin', how='left')
                .fillna({'商品数': 0, '総Pcs': 0, 'Slot数': 0})
        )

        # Cast to int
        per_bin_audit_report_init[["Slot数", "商品数", "総Pcs"]] = \
            per_bin_audit_report_init[["Slot数","商品数", "総Pcs"]].astype(int)
    except Exception as e:
        print(f"Audit report initialization error: Initial container inventory and per bin slot audit merger could not happen: {e}")
        return False

    # Save the initial reports as CSV files
    try:
        pd.DataFrame(per_bin_audit_report_init).to_csv(config.PER_BIN_AUDIT_REPORT, index=False)
        return True
    except Exception as e:
        print(f"Audit report initialization error: Could not save the reports as CSVs: {e}")
        return False

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#       Update the per bin audit report with the bin stowing date
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def update_per_bin_report_with_stowing():
    print("Updating the per bin audit report with the bin stowing date...")

    # Get all move transactions to ASRS
    params={
        "type":"MOVE",
        "parentContainer":config.ASRS_NAME
    }
    container_transactions=http_get_all("WMS",config.CONTAINER_TRANSACTION_URL,params)
    if container_transactions is False:
        print("Audit report stowing update error: Could not get container transactions from WMS")
        return False

    # Load the current bin file
    try:
        bins = pd.read_csv(config.ASRS_BIN_LIST_PATH)
    except:
        print("Audit report stowing update error: Could not load the bin file")
        return False

    # Transactions list -> DataFrame
    container_transactions_df = pd.DataFrame(container_transactions)

    # Save laptop timezone
    local_tz = datetime.now().astimezone().tzinfo

    # Find latest insertTime per containerName
    latest_times = (
        container_transactions_df
        .assign(
            insertTime=pd.to_datetime(container_transactions_df["insertTime"], utc=True)
                            .dt.tz_convert(local_tz)      # to local tz
                            .dt.tz_localize(None)         # drop tz info (optional)
        )
        .groupby("containerName", as_index=False)["insertTime"]
        .max()
        .rename(columns={"containerName": "name", "insertTime": "stowDateTime"})
    )

    # Merge into bins
    bins = bins.merge(latest_times, on="name", how="left")

    # Overwrite the bin file with new info
    try:
        bins.to_csv(config.ASRS_BIN_LIST_PATH, index=False)
        return True
    except:
        print("Audit report stowing update error: Could not save the updated bin file")
        return False
    
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#       Update the per bin audit report with last transaction
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def update_per_bin_report_with_last_transaction():
    print("Updating the per bin audit report with last transaction...")

    # Get all the relevant Inventory transactions
    params = {
        "type": [
            "RECEIVE_USABLE","RECEIVE_DAMAGED","RECEIVE_EXPIRED",
            "SHORTAGE","DAMAGE","UNDAMAGE",
            "TRANSFER_USABLE","TRANSFER_DAMAGED","TRANSFER_EXPIRED",
            "DISPOSE_DAMAGED","DISPOSE_EXPIRED",
            "PICK_TRANSFER","PICK_SHORTAGE","PICK_DAMAGE",
            "EXPIRE","UNEXPIRE",
            "SHIPPING","EXTERNAL_SHIPPING",
        ],
        "operationalSortOverride": True,
        "orderBy": "-created_at",
    }
    inventory_transactions=http_get_all("WMS",config.INVENTORY_TRANSACTION_URL,params)
    if inventory_transactions is False:
        print("Audit report transaction update error: Could not get inventory transactions from WMS")
        return False
    
    # Load the current per bin report
    try:
        audit_per_bin_report = pd.read_csv(config.PER_BIN_AUDIT_REPORT)
    except:
        print("Audit report transaction update error: Could not load the per bin audit report file")
        return False

    # Transactions list -> DataFrame
    inventory_transactions_df = pd.DataFrame(inventory_transactions)
    if (len(inventory_transactions_df)==0):
        print("Audit report audits update error: No inventory transaction in the system, no point to audit")
        return False

    # Localize insertTime to the laptop timezone
    local_tz = datetime.now().astimezone().tzinfo
    inventory_transactions_df["insertTime"] = pd.to_datetime(inventory_transactions_df["insertTime"], utc=True).dt.tz_convert(local_tz).dt.tz_localize(None)

    # Build (Bin, insertTime) from source and destination
    src = inventory_transactions_df[["sourceContainerName", "insertTime"]].rename(
        columns={"sourceContainerName": "Bin"}
    )
    dst = inventory_transactions_df[["destinationContainerName", "insertTime"]].rename(
        columns={"destinationContainerName": "Bin"}
    )

    both = pd.concat([src, dst], ignore_index=True).dropna(subset=["Bin"])

    # Latest time per Bin
    latest = both.groupby(["Bin"], as_index=False)["insertTime"].max().rename(
        columns={"insertTime": "入出庫日"}
    )

    # Merge into the audit report
    audit_per_bin_report = audit_per_bin_report.merge(latest, on=["Bin"], how="left")

    # Load the current bin file
    try:
        bins = pd.read_csv(config.ASRS_BIN_LIST_PATH)
    except:
        print("Audit report transaction update error: Could not load the bin file")
        return False

    # Ensure the DF timestamp formats are correct
    bins["stowDateTime"] = pd.to_datetime(bins["stowDateTime"], errors="coerce")
    audit_per_bin_report["入出庫日"] = pd.to_datetime(audit_per_bin_report["入出庫日"])

    # Merge stow time onto every row of the same Bin
    m = audit_per_bin_report.merge(
        bins[["name", "stowDateTime"]],
        left_on="Bin", right_on="name", how="left"
    )

    # Replace 入出庫日 with the later of (入出庫日, stowDateTime); NaT will be replaced
    m["入出庫日"] = m[["入出庫日", "stowDateTime"]].max(axis=1)

    # Clean up the unused columns
    audit_per_bin_report = m.drop(columns=["name", "stowDateTime"])

    # Convert to date (NaT-friendly)
    audit_per_bin_report["入出庫日"] = pd.to_datetime(audit_per_bin_report["入出庫日"], errors="coerce").dt.date

    # Check all timestamps exist
    success = audit_per_bin_report["入出庫日"].notna().all()
    if success is False:
        print("Audit report transaction update error: Some bins do not have a valid 入出庫日")
        return False
    
    # Overwrite the audit report file with new info
    try:
        audit_per_bin_report.to_csv(config.PER_BIN_AUDIT_REPORT, index=False)
        return True
    except:
        print("Audit report transaction update error: Could not save the updated audit report file")
        return False

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#       Update the per bin audit report with audits
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def update_per_bin_report_with_audits():
    print("Updating the audit report with audit results...")
    # Find the initial inventory file and extract the name
    matches = sorted(Path().glob(config.ASRS_INITIAL_INVENTORY_PATH))
    if matches:
        file_name = matches[-1].name
    else:
        print("Audit report audits update error: Could not find the inital inventory container CSV file")
        return False

    # Find the date time at which the audit started from the file name
    regex = re.escape(os.path.basename(config.ASRS_INITIAL_INVENTORY_PATH)).replace(r"\*", r"(?P<ts>\d{8}_\d{6})")
    name_match=re.match(regex,file_name)
    if not name_match:
        print("Audit report audits update error: Inital inventory container CSV file name does not match the expected format")
        return False
    
    # Save and convert to time the audit start time
    audit_start_time=name_match.group("ts")
    local_tz = datetime.now().astimezone().tzinfo
    audit_start_time=datetime.strptime(audit_start_time, "%Y%m%d_%H%M%S").replace(tzinfo=local_tz)
    audit_start_time=audit_start_time.astimezone(timezone.utc)

    # Get all the container audits done after the audit 
    params = {
        "createTimeAfter":audit_start_time,
        "type":"CONTAINER"
    }
    audits=http_get_all("WMS",config.AUDIT_URL,params)
    if audits is False:
        print("Audit report audits update error: Could not get audits from WMS")
        return False

    # Filter all audits which are or ongoing
    completed_audits=[audit for audit in audits if audit['status'] not in config.NOT_PROCESSED_AUDIT_STATUSES]

    # Keep just the UUIDs
    audit_ids=[{"id": audit.get("id")} for audit in completed_audits]

    # Download all the Audits at once
    if audit_ids:
        success=download_csv_file("Audit",config.AUDIT_EXPORT_PATH,audit_ids=audit_ids)
        if success is False:
            print("Audit report audits update error: Could not export Audit CSV file")
            return False
    else:
        # If no audit to download, same an empty file
        cols = [
            "Audit MHE","Audit name","Audit insert time","Audit container name",
            "Audit container index","Audit item code","Audit owner code","Audit lot number",
            "Audit expiration date","Audit sortkey","Audit quantity",
            "Audit observed quantity 1","Audit observed quantity 2","Audit observed quantity 3",
            "Audit adjusted quantity","Audit damaged quantity","Audit expired quantity"
        ]

        pd.DataFrame(columns=cols).to_csv(config.AUDIT_EXPORT_PATH, index=False)
    
    # Load the audit file
    try:
        audit_export = pd.read_csv(config.AUDIT_EXPORT_PATH)
    except:
        print("Audit report audits update error: Could not load the audit export CSV file")
        return False
    
    # Keep only the columns needed for the report
    audit_export_per_bin = audit_export[["Audit name", "Audit container name", "Audit insert time"]].drop_duplicates(subset=["Audit name", "Audit container name"])
    
    # Import the per bin audit report
    try:
        per_bin_audit_report = pd.read_csv(config.PER_BIN_AUDIT_REPORT)
    except:
        print("Audit report audits update error: Could not load the per bin audit report CSV file")
        return False
    
    # Ensure datetime for correct ordering# ensure datetime for correct ordering
    audit_export_per_bin["Audit insert time"] = pd.to_datetime(audit_export_per_bin["Audit insert time"], errors="coerce", utc=True).dt.tz_convert(local_tz).dt.tz_localize(None)

    # Order audits per bin and rank them
    audit_export_per_bin = audit_export_per_bin.sort_values(["Audit container name", "Audit insert time"])
    audit_export_per_bin["order"] = audit_export_per_bin.groupby("Audit container name").cumcount() + 1

    # First audit (cycle 1)
    cycle1 = audit_export_per_bin[audit_export_per_bin["order"] == 1][["Audit container name", "Audit insert time", "Audit name"]].rename(columns={
        "Audit container name": "Bin",
        "Audit insert time": "Cycle1実施日",
        "Audit name": "Cycle1棚卸し名",
    })

    # second audit (cycle 2)
    cycle2 = audit_export_per_bin[audit_export_per_bin["order"] == 2][["Audit container name", "Audit insert time", "Audit name"]].rename(columns={
        "Audit container name": "Bin",
        "Audit insert time": "Cycle2実施日",
        "Audit name": "Cycle2棚卸し名",
    })

    # merge onto per_bin_audit_report
    per_bin_audit_report = (
        per_bin_audit_report
        .merge(cycle1, on="Bin", how="left")
        .merge(cycle2, on="Bin", how="left")
    )

    # Convert all reports date time to dates
    bin_cols  = ["Cycle1実施日", "Cycle2実施日"]
    per_bin_audit_report[bin_cols] = per_bin_audit_report[bin_cols].apply(
        lambda s: pd.to_datetime(s, errors="coerce").dt.date
    )
    
    # Save the audit reports as CSV file
    try:
        pd.DataFrame(per_bin_audit_report).to_csv(config.PER_BIN_AUDIT_REPORT, index=False)
        return True
    except Exception as e:
        print(f"Audit report audits update error: Could not save the reports as CSVs: {e}")
        return False

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#       Generate the next audit tasks
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def generate_next_audits():
    print("Generating next audits...")
    # Import the per bin audit report
    try:
        per_bin_audit_report = pd.read_csv(config.PER_BIN_AUDIT_REPORT)
    except:
        print("Audit generation error: Could not load the per bin audit report CSV file")
        return False

    # Make sure the date format is correct
    per_bin_audit_report["入出庫日"] = pd.to_datetime(per_bin_audit_report["入出庫日"], errors="coerce")
    per_bin_audit_report["Cycle1実施日"] = pd.to_datetime(per_bin_audit_report["Cycle1実施日"], errors="coerce")
    per_bin_audit_report["Cycle2実施日"] = pd.to_datetime(per_bin_audit_report["Cycle2実施日"], errors="coerce")

    # Make algo robust even if some 入出庫日 are NaT
    per_bin_audit_report = (
        per_bin_audit_report.assign(_t=per_bin_audit_report["入出庫日"].fillna(pd.Timestamp.min))
    )

    # Filter the bins eligeable for audit by the remaining bins in ASRS bins
    eligeable_bins = per_bin_audit_report[per_bin_audit_report["Type"].isin(config.AUDIT_DESCRIPTOR_LIST)].reset_index(drop=True)

    if (config.AUDIT_CYCLE_NUMBER==2):
        # Keep only the following cases:
        #  - group 0: Cycle1 missing
        #  - group 1: Cycle1 present & Cycle2 missing
        mask0 = eligeable_bins["Cycle1実施日"].isna()
        mask1 = eligeable_bins["Cycle1実施日"].notna() & eligeable_bins["Cycle2実施日"].isna()
        eligeable_bins = eligeable_bins[mask0 | mask1].copy()

        # add group key: 0 -> no Cycle1, 1 -> has Cycle1 but no Cycle2
        mask0 = eligeable_bins["Cycle1実施日"].isna()
        eligeable_bins["_grp"] = np.where(mask0, 0, 1)
    else:
        # Keep only the following cases:
        #  - group 0: Cycle1 missing
        mask0 = eligeable_bins["Cycle1実施日"].isna()
        eligeable_bins = eligeable_bins[mask0].copy()

        # add group key: 0 -> no Cycle1
        mask0 = eligeable_bins["Cycle1実施日"].isna()
        eligeable_bins["_grp"] = 0

    # Sort by group and date, then shuffle rows within each (group, 入出庫日)
    sorted_bins = (
        eligeable_bins
        .sort_values(["_grp", "入出庫日", "Bin"], ascending=[True, True, True])
        .drop(columns="_grp")
        .reset_index(drop=True)
    )

    # Take only the number of required bins to do the audit
    n = int(config.AUDIT_BIN_NUMBER)
    selected_bin_names = sorted_bins["Bin"].head(config.AUDIT_BIN_NUMBER).tolist()
    if len(sorted_bins) < n:
        print(f"⚠️ Requested {config.AUDIT_BIN_NUMBER} bins, only {len(sorted_bins)} available. Returning {len(selected_bin_names)}.")

    # Suffle randomly the selected bins for more uniform audit
    random.shuffle(selected_bin_names)

    # Split the bins in the required task number
    selected_bin_nbr=len(selected_bin_names)
    q, r = divmod(selected_bin_nbr, config.AUDIT_TASK_NUMBER)
    audit_tasks, start = [], 0
    for i in range(config.AUDIT_TASK_NUMBER):
        size = q + (1 if i < r else 0)
        audit_tasks.append(selected_bin_names[start:start+size])
        start += size

    # Saving the current time
    now=datetime.now().strftime("%Y%m%d_%H%M%S")

    # Creating the CSV file rows
    audit_next_task_rows = []
    for i, group in enumerate(audit_tasks, start=1):
        task_name = f"Audit_{now}_{i:02d}"
        for bin_name in group:
            audit_next_task_rows.append({
                "Audit name": task_name,
                "Container name": bin_name,
                "Audit type": "CONTAINER"
            })

    # Saving the audit result in a CSV file
    try:
        pd.DataFrame(audit_next_task_rows).to_csv(config.AUDIT_NEXT_TASK_PATH, index=False)
        return True
    except:
        print("Audit generation error: Could not save the next audit task CSV file")
        return False

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#       Upload next audit tasks
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def upload_next_audits():
    print("Uploading next audits...")
    # Import the next audit task csv
    try:
        next_audit_tasks = pd.read_csv(config.AUDIT_NEXT_TASK_PATH)
    except:
        print("Audit upload error: Could not load the next audit task CSV file")
        return False

    # Format audit tasks for upload
    formatted_audit_tasks= [
        {
            "taskName": task,
            "bins": [{"name": b} for b in group["Container name"].tolist()]
        }
        for task, group in next_audit_tasks.groupby("Audit name", sort=False)
    ]

    # Upload the audit tasks to the WMS 
    for audit_task in formatted_audit_tasks:
        success=upload_an_audit(audit_task['taskName'],audit_task['bins'])
        if success is False:
            return success
    
    return True


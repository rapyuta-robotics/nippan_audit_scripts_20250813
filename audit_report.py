# Import funcions
from helpers.d_audit_helpers import ongoing_audit_check
from helpers.e_nippan_helpers import (
    save_container_inventory_csv,
    initalize_audit_report_csv,
    update_per_bin_report_with_stowing,
    update_per_bin_report_with_last_transaction,
    update_per_bin_report_with_audits,
    generate_next_audits,
    upload_next_audits,
)

# Import libraries
import sys

# Import configurations
import config

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#       Main function
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# # Check that no audit is ongoing
# success=ongoing_audit_check()
# if success is False:
#     print("Audit ongoing error: Stopping script")
#     sys.exit(1)

# Save the container inventory CSV file
success=save_container_inventory_csv()
if success is False:
    print("Initial inventory CSV creation error: Stopping script")
    sys.exit(1)

# Initialize audit report files
success=initalize_audit_report_csv()
if success is False:
    print("Audit report initialization error: Stopping script")
    sys.exit(1)

# Update bin file with stowing date and time
success=update_per_bin_report_with_stowing()
if success is False:
    print("Update bin file with stowing error: Stopping script")
    sys.exit(1)

# Update bin file with last transactions
success=update_per_bin_report_with_last_transaction()
if success is False:
    print("Update bin file with transactions error: Stopping script")
    sys.exit(1)

# Update the Audit report with audit
success=update_per_bin_report_with_audits()
if success is False:
    print("Update bin file with audits error: Stopping script")
    sys.exit(1)

# Generate the next audit files
success=generate_next_audits()
if success is False:
    print("Audit generation error: Stopping script")
    sys.exit(1)

# Upload the generated audits
if config.UPLOAD_GENERATED_AUDITS:
    success=upload_next_audits()
    if success is False:
        print("Audit upload error: Stopping script")
        sys.exit(1)

# Script end with success message
print("Script execution terminated with success")
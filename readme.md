## Purpose
The provided scripts are used to create the audit tasks to perform cyclic audit over a period of time instead of performing full audit

## Configuration Parameters

### User Configuration Parameters
These parameters can be modified by the user to customize the audit behavior:

| Parameter | Default Value | Description |
|-----------|---------------|-------------|
| `AUDIT_TASK_NUMBER` | `1` | The number of audit tasks to generate |
| `AUDIT_BIN_NUMBER` | `8` | The number of bins task to audit at once |
| `UPLOAD_GENERATED_AUDITS` | `False` | Should the script upload automatically to WMS the audit tasks |
| `AUDIT_DESCRIPTOR_GROUP` | `"日販"` | Should be CX or 日販 or CX日販 |

### Environment Configuration Parameters
These parameters configure the environment and connection settings:

| Parameter | Default Value | Description |
|-----------|---------------|-------------|
| `ASRS_NAME` | `"RR ASRS 001"` | ASRS setting name |
| `ENV_URL` | `"http://localhost"` | Environment URL (can be set to production URL) |
| `ENV_TOKEN` | `"autobootstrap"` | Environment token for authentication |

### Container Descriptor Groups
The script supports three predefined descriptor groups:

| Group Name | Descriptor Names | Cycle Number |
|------------|------------------|--------------|
| `CX` | CX Bin 1x1, CX Bin 2x1, CX Bin 2x2, CX Bin 4x2 | 1 |
| `日販` | 日販 Bin 1x1, 日販 Bin 2x1, 日販 Bin 2x2, 日販 Bin 4x2 | 2 |
| `CX日販` | CX日販 Bin 1x1, CX日販 Bin 2x1, CX日販 Bin 2x2, CX日販 Bin 4x2 | 2 |

### File Path Configuration
These paths define where input and output files are located:

| Parameter | Default Path | Description |
|-----------|-------------|-------------|
| `PER_BIN_AUDIT_REPORT` | `./results/Cycle1＆２実施状況(Bin別).csv` | Per-bin audit report output path |
| `AUDIT_NEXT_TASK_PATH` | `./results/次回棚卸し作業.csv` | Next audit task output path |

## Procedure

### Prerequisites
- Python 3.8 or later
- pip3 (Python package installer)

### Environment Setup

#### Automated Setup (Recommended)
1. Clone this repo to a PC where the audit tasks are generated and provided to customers throughout the Cyclic audit period (eg. Edge server)
2. Run the setup script to automatically configure your Python environment:
   ```bash
   ./setup.sh
   ```
   This script will:
   - Check Python and pip installation
   - Optionally create a virtual environment (recommended)
   - Install required Python packages from `requirements.txt`
   - Create necessary directories (`files` and `results`)

#### Manual Setup
If you prefer to set up the environment manually:

1. Clone this repository
2. Create a virtual environment (optional but recommended):
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install required packages:
   ```bash
   pip3 install -r requirements.txt
   ```
4. Create necessary directories:
   ```bash
   mkdir -p files results
   ```

#### Required Python Packages
The script depends on the following external packages (automatically installed via `requirements.txt`):
- `httpx>=0.24.0` - HTTP client for API requests
- `requests>=2.28.0` - HTTP library for file downloads
- `pandas>=1.5.0` - Data manipulation and analysis
- `numpy>=1.21.0` - Numerical computing support

### Configuration Setup

1. Configure the ENV_URL and ENV_TOKEN in `config.py` aligned with the production environment

### Generation of Audit tasks and audit reports (this is to check the file audit output)

1. Open the config.py
2. Set the UPLOAD_GENERATED_AUDITS to True
3. Set AUDIT_TASK_NUMBER param to number of audit tasks to be generated
4. Set the AUDIT_BIN_NUMBER of bins to be audited
5. Set the AUDIT_DESCRIPTOR_GROUP to the container groups one among (CX, 日販, CX日販)
6. Open a terminal and execute the audit_report.py 
    ```
    > python3 audit_report.py
    ```
7. The generated files can be inspected in the **results** folder
8. THe uploaded Audit tasks can be inspected in the System UI (WMS management screen - Audit tab)

Note: In **files** folder, initial inventory configuration is captured. Please backup the contents of this folder


## Logic
THe bins are selected for audit based on the following logic

1. Bins selected in the descriptor group
2. Bins for which Cycle 1 audit is not performed and that have the oldest inventory movement
3. Bins for which Cycle 1 is performed but Cycle 2 audit is not performed and that have the oldest inventory movement
4. Randomize the bins for which inventory movement happened
5. Select the first **AUDIT_BIN_NUMBER** bins
6. Randomize the bins (to distribute across in a fuzzy manner to the auditing personnel)
7. Split the randomized bins into **AUDIT_TASK_NUMBER** tasks

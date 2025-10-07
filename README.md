# Harness FME Feature Flag Report Generator

A Python script to generate comprehensive reports on feature flags from Harness FME.

## Requirements

- Python 3.7+
- `requests` library (version 2.31.0 or higher)

## Setup

### 1. Create and Activate Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install requests>=2.31.0
```

### 3. Set Environment Variables

Before running the script, you must set two environment variables:

1. **HARNESS_API_TOKEN**: Your Harness FME API token
2. **HARNESS_ACCOUNT_ID**: Your Harness account identifier

```bash
export HARNESS_API_TOKEN="your_token_here"
export HARNESS_ACCOUNT_ID="your_account_id_here"
```

## Usage

Run the script:
```bash
python fme_report.py
```

Save the report to a file:
```bash
python fme_report.py > report_$(date +%Y%m%d).txt
```

## Report Contents

The report includes:

### Detailed Workspace Information
- Feature flag name and rollout status
- Owner (email or group ID)
- Description
- Tags
- Creation timestamp (in EDT)

### Summary Statistics
- **Overall Metrics**: Total workspaces, total flags, average flags per workspace
- **Flags by Workspace**: Count of flags in each workspace
- **Top Flag Owners**: Top 10 users/groups by flag count
- **Flags by Rollout Status**: Distribution of flags across different statuses
- **Flags by Tag**: Count of flags per tag
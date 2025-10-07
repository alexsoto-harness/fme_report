#!/usr/bin/env python3
"""
Harness FME Feature Flag Report Generator

Requirements: requests>=2.31.0

Usage:
    export HARNESS_API_TOKEN="your_api_token_here"
    export HARNESS_ACCOUNT_ID="your_account_id_here"
    python fme_report.py
"""

import os
import sys
from datetime import datetime, timezone

try:
    import requests
except ImportError:
    print("Error: 'requests' module is required. Install it with: pip install requests>=2.31.0")
    sys.exit(1)


def get_workspaces(api_token):
    url = "https://api.split.io/internal/api/v2/workspaces"
    headers = {"Authorization": f"Bearer {api_token}"}
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching workspaces: {e}", file=sys.stderr)
        sys.exit(1)


def get_feature_flags(api_token, workspace_id):
    url = f"https://api.split.io/internal/api/v2/splits/ws/{workspace_id}"
    headers = {"Authorization": f"Bearer {api_token}"}
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching feature flags: {e}", file=sys.stderr)
        return []


def get_user_email(api_token, user_id, account_id, user_cache):
    if user_id in user_cache:
        return user_cache[user_id]
    
    url = f"https://app.harness.io/ng/api/user/aggregate/{user_id}"
    params = {"accountIdentifier": account_id}
    headers = {
        "x-api-key": api_token,
        "Harness-Account": account_id
    }
    
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        user_data = response.json()
        
        email = None
        if 'data' in user_data and user_data['data']:
            if isinstance(user_data['data'], dict) and 'user' in user_data['data']:
                email = user_data['data']['user'].get('email')
            elif isinstance(user_data['data'], dict) and 'email' in user_data['data']:
                email = user_data['data'].get('email')
        
        if not email and 'user' in user_data:
            email = user_data['user'].get('email')
        
        if not email and 'email' in user_data:
            email = user_data.get('email')
        
        if not email:
            email = f"ID: {user_id}"
        
        user_cache[user_id] = email
        return email
    except requests.exceptions.RequestException:
        result = f"ID: {user_id}"
        user_cache[user_id] = result
        return result


def format_timestamp_edt(timestamp_ms):
    if not timestamp_ms:
        return "N/A"
    
    timestamp_sec = timestamp_ms / 1000
    utc_dt = datetime.fromtimestamp(timestamp_sec, tz=timezone.utc)
    edt_offset = -4 * 3600
    edt_dt = datetime.fromtimestamp(timestamp_sec + edt_offset, tz=timezone.utc)
    
    return edt_dt.strftime("%Y-%m-%d %H:%M:%S EDT")


def main():
    api_token = os.environ.get('HARNESS_API_TOKEN')
    account_id = os.environ.get('HARNESS_ACCOUNT_ID')
    
    if not api_token:
        print("Error: HARNESS_API_TOKEN environment variable is not set.", file=sys.stderr)
        print("Please set it with: export HARNESS_API_TOKEN='your_token_here'", file=sys.stderr)
        sys.exit(1)
    
    if not account_id:
        print("Error: HARNESS_ACCOUNT_ID environment variable is not set.", file=sys.stderr)
        print("Please set it with: export HARNESS_ACCOUNT_ID='your_account_id_here'", file=sys.stderr)
        sys.exit(1)
    
    user_cache = {}
    total_flags = 0
    flags_by_owner = {}
    flags_by_workspace = {}
    flags_by_status = {}
    flags_by_tag = {}
    
    print("=" * 80)
    print("FEATURE FLAG MANAGEMENT REPORT")
    print("Harness FME")
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S EDT')}")
    print("=" * 80)
    print("\nFetching workspaces from FME API...")
    
    workspaces = get_workspaces(api_token)
    
    if isinstance(workspaces, dict):
        workspace_list = workspaces.get('objects', workspaces.get('data', []))
    else:
        workspace_list = workspaces
    
    if not workspace_list:
        print("No workspaces found.")
        return
    
    print(f"Found {len(workspace_list)} workspace(s)\n")
    print("=" * 80)
    
    for workspace in workspace_list:
        name = workspace.get('name', 'N/A')
        workspace_id = workspace.get('id', None)
        
        print(f"\n{'─' * 80}")
        print(f"WORKSPACE: {name}")
        print(f"{'─' * 80}")
        
        if not workspace_id:
            print("⚠️  No workspace ID found, skipping feature flags\n")
            continue
        
        feature_flags = get_feature_flags(api_token, workspace_id)
        
        if isinstance(feature_flags, dict):
            ff_list = feature_flags.get('objects', feature_flags.get('data', []))
        else:
            ff_list = feature_flags
        
        if not ff_list:
            print("  No feature flags found")
            continue
        
        flags_by_workspace[name] = len(ff_list)
        print(f"\nFeature Flags: {len(ff_list)}\n")
        
        for ff in ff_list:
            total_flags += 1
            ff_name = ff.get('name', 'N/A')
            ff_description = ff.get('description', 'No description')
            creation_time = ff.get('creationTime', None)
            rollout_status = ff.get('rolloutStatus', {}).get('name', 'Unknown')
            tags = ff.get('tags', [])
            
            owners = ff.get('owners', [])
            if owners and len(owners) > 0:
                owner = owners[0]
                owner_id = owner.get('id', '')
                owner_type = owner.get('type', '')
                
                if owner_id and owner_type == 'user':
                    owner_str = get_user_email(api_token, owner_id, account_id, user_cache)
                elif owner_id:
                    owner_str = f"ID: {owner_id} (type: {owner_type})"
                else:
                    owner_str = 'Unknown'
            else:
                owner_str = 'No owner assigned'
            
            creation_time_str = format_timestamp_edt(creation_time)
            
            if tags:
                tag_names = [tag.get('name', '') for tag in tags if isinstance(tag, dict)]
                tags_str = ', '.join(tag_names) if tag_names else 'None'
                for tag_name in tag_names:
                    if tag_name:
                        flags_by_tag[tag_name] = flags_by_tag.get(tag_name, 0) + 1
            else:
                tags_str = 'None'
            
            flags_by_owner[owner_str] = flags_by_owner.get(owner_str, 0) + 1
            flags_by_status[rollout_status] = flags_by_status.get(rollout_status, 0) + 1
            
            print(f"  [{rollout_status}] {ff_name}")
            print(f"    Owner: {owner_str}")
            if ff_description and ff_description != 'No description':
                print(f"    Description: {ff_description}")
            if tags_str != 'None':
                print(f"    Tags: {tags_str}")
            print(f"    Created: {creation_time_str}")
            print()
    
    print("\n" + "=" * 80)
    print("SUMMARY STATISTICS")
    print("=" * 80)
    
    print(f"\n📊 OVERALL METRICS")
    print(f"  • Total Workspaces: {len(workspace_list)}")
    print(f"  • Total Feature Flags: {total_flags}")
    if flags_by_workspace:
        avg_flags = total_flags / len([w for w in workspace_list if flags_by_workspace.get(w.get('name', 'N/A'), 0) > 0])
        print(f"  • Average Flags per Workspace: {avg_flags:.1f}")
    
    print(f"\n📁 FLAGS BY WORKSPACE")
    for ws_name, count in sorted(flags_by_workspace.items(), key=lambda x: x[1], reverse=True):
        print(f"  • {ws_name}: {count} flags")
    
    print(f"\n👤 TOP FLAG OWNERS")
    sorted_owners = sorted(flags_by_owner.items(), key=lambda x: x[1], reverse=True)
    for owner, count in sorted_owners[:10]:
        print(f"  • {owner}: {count} flags")
    
    print(f"\n🚦 FLAGS BY ROLLOUT STATUS")
    for status, count in sorted(flags_by_status.items(), key=lambda x: x[1], reverse=True):
        print(f"  • {status}: {count} flags ({count/total_flags*100:.1f}%)")
    
    if flags_by_tag:
        print(f"\n🏷️  FLAGS BY TAG")
        for tag, count in sorted(flags_by_tag.items(), key=lambda x: x[1], reverse=True):
            print(f"  • {tag}: {count} flags")
    
    print("\n" + "=" * 80)
    print("END OF REPORT")
    print("=" * 80)


if __name__ == "__main__":
    main()

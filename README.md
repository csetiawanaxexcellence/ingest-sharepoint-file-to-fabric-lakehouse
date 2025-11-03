# SharePoint to Microsoft Fabric Lakehouse Integration

This repository contains Python scripts for transferring files from SharePoint to Microsoft Fabric Lakehouse using Microsoft Graph API with Azure AD App Registration authentication.

## Overview

This solution enables automated file transfer from SharePoint document libraries to Microsoft Fabric Lakehouse, with support for archiving and cleanup operations.

## Files

- **config.py** - Configuration file containing all connection details and settings
- **sharepoint_to_bronze_delta.py** - Main script for transferring files from SharePoint to Lakehouse
- **utility_sp_grant_siteselected.py** - Utility script for granting site-selected permissions to App Registrations

## Prerequisites

1. **Microsoft Fabric Workspace** with Lakehouse created
2. **Azure AD App Registrations** (2 required):
   - 1st App Registration: PnP Management App (for granting permissions)
   - 2nd App Registration: Site Access App (for accessing SharePoint files)
3. **SharePoint Site** with appropriate permissions
4. **Python packages**: `msal`, `requests`, `pandas`, `pytz`, `notebookutils` (Fabric notebooks)

## Setup Instructions

### Step 1: Configure Azure AD App Registrations

#### 1st App Registration (PnP Management App)
- Create an App Registration in Azure AD
- Grant **Sites.FullControl.All** API permissions (Application)
- Create a client secret
- Note down: `client_id`, `client_secret`, `tenant_id`

#### 2nd App Registration (Site Access App)
- Create another App Registration in Azure AD
- This will be granted site-selected permissions via the utility script
- Create a client secret
- Note down: `client_id`, `client_secret`, `tenant_id`

### Step 2: Configure config.py

Replace the placeholder values in `config.py`:

```python
config = {
  "workspace": {
    "workspace_name": "Your Workspace Name",  # Your Fabric workspace name
    "workspace_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"  # Your workspace ID
  },
  "bronze": {
    "lakehouse_id": "yyyyyyyy-yyyy-yyyy-yyyy-yyyyyyyyyyyy",  # Your lakehouse ID
    "lakehouse_name": "bronze",  # Your lakehouse name
    "lakehouse_root": "abfss://...",  # Your lakehouse root path
    ...
  },
  "sharepoint": {
    "hostname": "yourcompany.sharepoint.com",  # Your SharePoint hostname
    "site_path": "YourSiteName",  # Your SharePoint site path
    ...
  },
  "azure-authentication": {
    "tenant_id": "zzzzzzzz-zzzz-zzzz-zzzz-zzzzzzzzzzzz",
    "appreg_siteselect_client_id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",  # 2nd App Reg
    "appreg_siteselect_client_secret": "your_client_secret_here"
  }
}
```

**How to find your IDs:**
- **Workspace ID**: In Fabric, go to your workspace settings
- **Lakehouse ID**: In Fabric, go to your lakehouse settings
- **Lakehouse Root**: Format is `abfss://[workspace_id]@onelake.dfs.fabric.microsoft.com/[lakehouse_id]`
- **Tenant ID**: Azure Portal > Azure Active Directory > Properties
- **Client IDs**: Azure Portal > App Registrations > Your App > Overview

### Step 3: Grant Site-Selected Permissions

Run `utility_sp_grant_siteselected.py` to grant the 2nd App Registration access to your SharePoint site:

1. Update the credentials for the 1st App Registration (Management App)
2. Update the SharePoint site details
3. Update the 2nd App Registration client ID (`app_id_to_grant`)
4. Run the script to grant permissions

### Step 4: Run the Main Transfer Script

Execute `sharepoint_to_bronze_delta.py` in your Fabric notebook to:
1. Authenticate with Azure AD
2. Connect to SharePoint
3. Discover files in configured folders
4. Download files from SharePoint
5. Upload files to Lakehouse
6. Archive files in SharePoint (optional)
7. Delete original files from SharePoint (optional)

## Configuration Options

### Source Folder Configuration

In `config.py`, configure your source folders:

```python
"source_folder_list": [
  {
    "folder_name": "Your Source Folder",  # SharePoint folder name
    "copy_to_archive": "True",  # Archive files after transfer
    "delete_original": "True",  # Delete originals after archiving
    "lakehouse_folder": "sales_usa"  # Target folder in Lakehouse
  }
]
```

### Lakehouse Configuration

Configure your data destinations:

```python
"bronze": {
  "sales_usa": {
    "source_folder": "/Files/sales_usa/",
    "archive_folder": "/Files/sales_usa/archives",
    "sink_table": "/Tables/dbo/usa_sales_transaction"
  }
}
```

## Architecture

```
SharePoint Document Library
    ↓ (Microsoft Graph API)
Temporary Local Storage (/tmp)
    ↓ (mssparkutils.fs.cp)
Microsoft Fabric Lakehouse
    ↓
[Optional] Archive in SharePoint
[Optional] Delete Original from SharePoint
```

## Classes and Components

### AzureAuthenticator
Handles Azure AD authentication using MSAL (Microsoft Authentication Library).

### SharePointService
Manages all SharePoint operations via Microsoft Graph API:
- Get site ID and drive ID
- List folder contents
- Create archive folders
- Copy files to archive
- Delete files

### FileDiscovery
Discovers and catalogs files from SharePoint folders.

### LakehouseService
Handles file operations for Lakehouse:
- Download files to local storage
- Upload files to Lakehouse

### SharePointToLakehouseOrchestrator
Orchestrates the entire transfer process.

### TransferFromSharepoint
Main facade class that initializes all components and runs the process.

## Security Considerations

⚠️ **Important Security Notes:**
- Never commit real credentials to source control
- Use Azure Key Vault or Fabric secrets for storing credentials in production
- Implement proper access controls on App Registrations
- Use site-selected permissions (least privilege principle)
- Regularly rotate client secrets
- Monitor API usage and access logs

## Troubleshooting

### Common Issues

1. **Authentication Failed**
   - Verify tenant_id, client_id, and client_secret
   - Ensure App Registration has required permissions
   - Check if admin consent has been granted

2. **SharePoint Access Denied**
   - Run `utility_sp_grant_siteselected.py` to grant permissions
   - Verify site path and hostname are correct
   - Check if site-selected permissions are properly configured

3. **Lakehouse Upload Failed**
   - Verify lakehouse_id and workspace_id
   - Ensure lakehouse_root path is correct
   - Check if the Fabric workspace is accessible

4. **Files Not Found**
   - Verify folder_name in configuration
   - Check SharePoint folder structure
   - Ensure files exist in the specified location

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

This is a template/tutorial project. Feel free to customize according to your organization's requirements.

## Support

For issues related to:
- **Microsoft Graph API**: [Microsoft Graph Documentation](https://docs.microsoft.com/en-us/graph/)
- **Microsoft Fabric**: [Microsoft Fabric Documentation](https://learn.microsoft.com/en-us/fabric/)
- **MSAL Python**: [MSAL Python Documentation](https://msal-python.readthedocs.io/)


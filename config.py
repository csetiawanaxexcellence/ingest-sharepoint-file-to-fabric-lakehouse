


config ={
  "workspace": {
    "workspace_name": "Your Workspace Name",  # Replace with your Fabric workspace name
    "workspace_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"  # Replace with your workspace ID
  },
  "bronze": {
    "lakehouse_id": "yyyyyyyy-yyyy-yyyy-yyyy-yyyyyyyyyyyy",  # Replace with your lakehouse ID
    "lakehouse_name": "bronze",  # Replace with your lakehouse name
    "lakehouse_root": "abfss://xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx@onelake.dfs.fabric.microsoft.com/yyyyyyyy-yyyy-yyyy-yyyy-yyyyyyyyyyyy",  # Replace with your lakehouse root path
    "sales_usa": {
      "source_folder": "/Files/sales_usa/",  # Customize your source folder path
      "archive_folder": "/Files/sales_usa/archives",  # Customize your archive folder path
      "sink_table": "/Tables/dbo/sales_transaction"  # Customize your table path
    }
  },
  "sharepoint": {
    "hostname": "yourcompany.sharepoint.com",  # Replace with your SharePoint hostname
    "site_path": "YourSiteName",  # Replace with your SharePoint site path
    "source_folder_list": [
      {
        "folder_name": "Your Source Folder",  # Replace with your SharePoint folder name
        "copy_to_archive": "True",  # Set to "True" to archive files
        "delete_original": "True",  # Set to "True" to delete originals after archiving
        "lakehouse_folder": "sales_usa"  # Replace with your target lakehouse folder
      }
    ]
  },
  "azure-authentication": {
    "tenant_id": "zzzzzzzz-zzzz-zzzz-zzzz-zzzzzzzzzzzz",  # Replace with your Azure AD tenant ID
    "appreg_siteselect_client_id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",  # Replace with your App Registration client ID
    "appreg_siteselect_client_secret": "your_client_secret_here"  # Replace with your App Registration client secret
  }
}


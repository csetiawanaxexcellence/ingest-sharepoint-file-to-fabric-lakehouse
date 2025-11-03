

from msal import ConfidentialClientApplication

# Azure AD App credentials for the 1st AppReg (PnP Management App)
client_id = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"  # Replace with your 1st App Registration client ID (Management App)
client_secret = "your_management_app_secret_here"  # Replace with your 1st App Registration client secret
tenant_id = "zzzzzzzz-zzzz-zzzz-zzzz-zzzzzzzzzzzz"  # Replace with your Azure AD tenant ID
authority = f"https://login.microsoftonline.com/{tenant_id}"

# Create an MSAL client
app = ConfidentialClientApplication(client_id, authority=authority, client_credential=client_secret)

# Acquire a token for Microsoft Graph
scopes = ["https://graph.microsoft.com/.default"]
result = app.acquire_token_for_client(scopes=scopes)

# Extract the access token
access_token = result['access_token']
print("Access token acquired!")
print(access_token)


# #### Step 2: Grant Permissions to the 2nd AppReg

# In[3]:


import requests

# Variables
hostname = "yourcompany.sharepoint.com"  # Replace with your SharePoint hostname
site_path = "YourSiteName"  # Replace with your SharePoint site path
site_display_name = "Your Site Display Name"  # Replace with your site display name
app_id_to_grant = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"  # Replace with your 2nd App Registration client ID (Site Access App)

# Step 1: Retrieve the Site ID
print("Retrieving Site ID...")
graph_api_url = f"https://graph.microsoft.com/v1.0/sites/{hostname}:/sites/{site_path}"

headers = {
    "Authorization": f"Bearer {access_token}",
    "Accept": "application/json"
}

response = requests.get(graph_api_url, headers=headers)
if response.status_code == 200:
    site_data = response.json()
    site_id = site_data['id']
    print(f"Site ID: {site_id}")
else:
    print(f"Failed to retrieve site ID. Status Code: {response.status_code}")
    print(response.json())
    exit()

# Step 2: Check existing permissions
print("Checking existing permissions...")
grant_url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/permissions"
response = requests.get(grant_url, headers=headers)

if response.status_code == 200:
    existing_permissions = response.json().get('value', [])
    app_permission_exists = False

    #print("Existing Permissions:", existing_permissions)  # Debug entire response

    for permission in existing_permissions:
        #print("Permission Object:", permission)  # Debug individual permission object
        if 'grantedToIdentitiesV2' in permission:
            for grantee in permission['grantedToIdentitiesV2']:
                print("Grantee Application:", grantee)  # Debug grantee info
                if grantee['application'].get('id') == app_id_to_grant:
                    app_permission_exists = True
                    roles = permission.get('roles', [])  # Safely fetch 'roles'
                    #print(f"App {app_id_to_grant} already has the following roles: {roles}")

    if app_permission_exists:
        print("Permissions already exist. No action needed.")
    else:
        # Step 3: Grant permissions if not already present
        print("Granting new permissions...")
        grant_payload = {
            "roles": ["write"],
            "grantedToIdentities": [
            {
                "application": {
                    "id": app_id_to_grant,
                    "displayName": site_display_name
                        }
                }   
            ]
        }

        response = requests.post(grant_url, headers=headers, json=grant_payload)

        if response.status_code == 201:
            print("Permissions granted successfully!")
        else:
            print(f"Failed to grant permissions. Status Code: {response.status_code}")
            print(response.json())
else:
    print(f"Failed to retrieve existing permissions. Status Code: {response.status_code}")
    print(response.json())


# ### Step 3: Test access to the SharePoint site

# In[4]:


print(site_id)
response = requests.get(f"https://graph.microsoft.com/v1.0/sites/{site_id}", headers=headers)

if response.status_code == 200:
    print("PnP Management App has access to the SharePoint site!")
else:
    print(f"Access to the SharePoint site failed: {response.status_code}")
    print(response.json())


# ### Step 4: Test accessible sharepoint sites for 2nd AppReg

# In[5]:


import requests
import pandas as pd
from IPython.display import display, HTML

# Step 1: Retrieve the list of SharePoint sites
print("Retrieving list of SharePoint sites...")
graph_api_url = "https://graph.microsoft.com/v1.0/sites?search=*"

headers = {
    "Authorization": f"Bearer {access_token}",
    "Accept": "application/json"
}

response = requests.get(graph_api_url, headers=headers)
if response.status_code == 200:
    sites_data = response.json().get('value', [])
    print(f"Retrieved {len(sites_data)} sites.")
else:
    print(f"Failed to retrieve sites. Status Code: {response.status_code}")
    print(response.json())

# Step 2: Put the data in a DataFrame
df = pd.DataFrame(sites_data)
df_display = df[['name', 'lastModifiedDateTime', 'webUrl']]

# Step 3: Check which sites are accessible for the 2nd AppReg and add a new column "accessible"
df['accessible'] = 'No'  # Initialize the column with 'No'
app_id_to_check = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"  # Replace with your 2nd App Registration client ID (Site Access App)

for index, site in df.iterrows():
    site_id = site['id']
    permissions_url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/permissions"
    
    response = requests.get(permissions_url, headers=headers)
    if response.status_code == 200:
        permissions_data = response.json().get('value', [])
        for permission in permissions_data:
            if 'grantedToIdentitiesV2' in permission:
                for grantee in permission['grantedToIdentitiesV2']:
                    if grantee['application'].get('id') == app_id_to_check:
                        df.at[index, 'accessible'] = 'Yes'
                        print(permissions_data)
                        break

# Step 4: Create a new DataFrame for display with specific columns
df_display = df[['name', 'lastModifiedDateTime', 'webUrl', 'accessible']]

# Step 5: Define the highlight function
def highlight_accessible(s):
    if s['accessible'] == 'Yes':
        return ['background-color: yellow; font-weight: bold'] * len(s)
    else:
        return [''] * len(s)

# Step 6: Display the sites in a tabular format with grid and highlight accessible sites
styled_df = df_display.style.apply(highlight_accessible, axis=1)
display(HTML(styled_df.to_html()))


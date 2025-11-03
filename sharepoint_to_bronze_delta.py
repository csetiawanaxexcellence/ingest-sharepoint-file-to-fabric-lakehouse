


import requests
import pandas as pd

from msal import ConfidentialClientApplication
from notebookutils import mssparkutils

from datetime import datetime
import os
import pytz



class AzureAuthenticator:
    def __init__(self, tenant_id: str, client_id: str, client_secret: str):
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.client_secret = client_secret
        self.app = ConfidentialClientApplication(
            client_id=self.client_id,
            authority=f"https://login.microsoftonline.com/{self.tenant_id}",
            client_credential=self.client_secret
        )

    def get_access_token(self) -> str:
        scopes = ["https://graph.microsoft.com/.default"]
        result = self.app.acquire_token_for_client(scopes=scopes)
        if "access_token" in result:
            print("Access token acquired successfully!")
            return result["access_token"]
        raise RuntimeError(f"Failed to acquire access token: {result}")


# In[12]:


class SharePointService:
    def __init__(self, access_token: str, hostname: str, site_path: str, timeout_sec: int = 120):
        self.access_token = access_token
        self.hostname = hostname
        self.site_path = site_path
        self.timeout_sec = timeout_sec

    # ------------- helpers -------------
    def _headers(self):
        return {"Authorization": f"Bearer {self.access_token}", "Accept": "application/json"}

    # ------------- site / drive -------------
    def get_site_id(self) -> str:
        url = f"https://graph.microsoft.com/v1.0/sites/{self.hostname}:/sites/{self.site_path}"
        resp = requests.get(url, headers=self._headers(), timeout=self.timeout_sec)
        if resp.status_code == 200:
            site_id = resp.json().get("id", "")
            print(f"Site ID: {site_id}")
            return site_id
        raise RuntimeError(f"Failed to retrieve site ID. Status: {resp.status_code} | {resp.text}")

    def get_document_drive_id(self, site_id: str) -> str:
        url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives"
        resp = requests.get(url, headers=self._headers(), timeout=self.timeout_sec)
        if resp.status_code != 200:
            raise RuntimeError(f"Failed to retrieve drive list. Status: {resp.status_code} | {resp.text}")
        drives = resp.json().get("value", [])
        doc_drive = next((d for d in drives if d.get("name") != "Teams Wiki Data"), None)
        if not doc_drive:
            raise RuntimeError("No suitable document library found.")
        return doc_drive["id"]

    # ------------- folders / files -------------
    def list_folder_children(self, drive_id: str, folder_name: str):
        url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/root:/{folder_name}:/children"
        resp = requests.get(url, headers=self._headers(), timeout=self.timeout_sec)
        if resp.status_code == 200:
            return resp.json().get("value", [])
        raise RuntimeError(f"Failed to list children for '{folder_name}'. Status: {resp.status_code} | {resp.text}")

    # ------------- archive / delete -------------
    def ensure_archive_folder(self, drive_id: str, archive_folder_path: str):
        check_url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/root:/{archive_folder_path}"
        resp = requests.get(check_url, headers=self._headers(), timeout=self.timeout_sec)
        if resp.status_code == 200:
            return  # exists

        parent, sub = archive_folder_path.rsplit("/", 1) if "/" in archive_folder_path else ("", archive_folder_path)
        create_url = (
            f"https://graph.microsoft.com/v1.0/drives/{drive_id}/root:/{parent}:/children"
            if parent else f"https://graph.microsoft.com/v1.0/drives/{drive_id}/root/children"
        )
        payload = {"name": sub, "folder": {}}
        cr = requests.post(create_url, json=payload, headers=self._headers(), timeout=self.timeout_sec)
        if cr.status_code not in (200, 201):
            raise RuntimeError(f"Failed to create archive folder '{archive_folder_path}': {cr.status_code} | {cr.text}")

    def copy_to_archive(self, drive_id: str, folder_name: str, original_file_name: str,
                        archive_folder_path: str, archive_file_name: str):
        copy_url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/root:/{folder_name}/{original_file_name}:/copy"
        payload = {"parentReference": {"driveId": drive_id, "path": f"/drive/root:/{archive_folder_path}"},
                   "name": archive_file_name}
        resp = requests.post(copy_url, json=payload, headers=self._headers(), timeout=self.timeout_sec)
        if resp.status_code not in (200, 202):
            raise RuntimeError(f"Failed to copy to archive. Status: {resp.status_code} | {resp.text}")

    def delete_original(self, drive_id: str, folder_name: str, original_file_name: str):
        del_url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/root:/{folder_name}/{original_file_name}"
        resp = requests.delete(del_url, headers=self._headers(), timeout=self.timeout_sec)
        if resp.status_code != 204:
            raise RuntimeError(f"Failed to delete original file. Status: {resp.status_code} | {resp.text}")


# In[13]:


class FileDiscovery:
    def __init__(self, sp: SharePointService, site_path: str, tz: str = "Asia/Kuala_Lumpur"):
        self.sp = sp
        self.site_path = site_path
        self.tz = tz

    def _log(self, msg: str):
        now = datetime.now(pytz.timezone(self.tz)).strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{now}] {msg}")

    def collect(self, drive_id: str, folder_list: list) -> pd.DataFrame:
        if not folder_list:
            raise ValueError("No folders specified in config.json under 'source_folder_list'.")
        rows, total = [], 0
        for folder_info in folder_list:
            folder_name = folder_info.get("folder_name")
            if not folder_name:
                continue
            copy_to_archive = folder_info.get("copy_to_archive", "False")
            delete_original = folder_info.get("delete_original", "False")
            lakehouse_folder = folder_info.get("lakehouse_folder")

            items = self.sp.list_folder_children(drive_id, folder_name)
            count = 0
            for it in items:
                if "file" in it:
                    rows.append({
                        "file_name": it["name"],
                        "folder_name": folder_name,
                        "site_name": self.site_path,
                        "file_url": it["@microsoft.graph.downloadUrl"],
                        "lakehouse_folder": lakehouse_folder,
                        "copy_to_archive": copy_to_archive,
                        "delete_original": delete_original
                    })
                    count += 1; total += 1
            self._log(f"Retrieved {count} files from '{folder_name}'.")
        print(f"Total files discovered: {total}")
        return pd.DataFrame(rows)


# In[14]:


class LakehouseService:
    def __init__(self, lakehouse_root: str):
        self.lakehouse_root = lakehouse_root

    def download_to_local(self, file_url: str, file_name: str, local_dir: str = "/tmp") -> str:
        os.makedirs(local_dir, exist_ok=True)
        local_path = os.path.join(local_dir, file_name)
        resp = requests.get(file_url)
        if resp.status_code != 200:
            raise RuntimeError(f"Failed to download '{file_name}'. Status: {resp.status_code}")
        with open(local_path, "wb") as f:
            f.write(resp.content)
        return local_path

    def upload(self, local_path: str, lakehouse_folder: str, file_name: str) -> str:
        lakehouse_path = f"{self.lakehouse_root}/Files/{lakehouse_folder}/{file_name}"
        mssparkutils.fs.cp(f"file://{local_path}", lakehouse_path)
        return lakehouse_path


# In[15]:


class SharePointToLakehouseOrchestrator:
    def __init__(self, sp: SharePointService, discovery: FileDiscovery, lakehouse: LakehouseService, tz: str = "Asia/Kuala_Lumpur"):
        self.sp = sp
        self.discovery = discovery
        self.lakehouse = lakehouse
        self.tz = tz

    def _timestamped(self, base_name: str) -> str:
        ts = datetime.now(pytz.timezone(self.tz)).strftime("%d%m%y%H%M%S")
        return f"{ts}_{base_name}"

    def run(self, source_folder_list: list):
        print(f"Processing files from SharePoint Site: {self.discovery.site_path}")

        site_id = self.sp.get_site_id()
        drive_id = self.sp.get_document_drive_id(site_id)

        df_files = self.discovery.collect(drive_id, source_folder_list)
        if df_files.empty:
            print("No files found. Process completed.")
            return

        display(df_files)  # keep your preview

        for _, row in df_files.iterrows():
            original_file_name = row["file_name"]
            safe_name = original_file_name.replace("'", "_")
            folder_name = row["folder_name"]
            file_url = row["file_url"]
            lakehouse_folder = row["lakehouse_folder"]

            try:
                local_path = self.lakehouse.download_to_local(file_url, safe_name)
                lakehouse_path = self.lakehouse.upload(local_path, lakehouse_folder, safe_name)
                print(f"✅ Uploaded to Lakehouse: {lakehouse_path}")
            except Exception as e:
                print(f"⚠️ Skipped '{original_file_name}' due to error: {e}")
                continue

            # archive + optional delete
            if str(row.get("copy_to_archive", "False")).lower() == "true":
                archive_folder_path = f"{folder_name}/archive"
                try:
                    self.sp.ensure_archive_folder(drive_id, archive_folder_path)
                    archive_file_name = self._timestamped(safe_name)
                    self.sp.copy_to_archive(drive_id, folder_name, original_file_name, archive_folder_path, archive_file_name)
                    print(f"📦 Copied to archive: /{archive_folder_path}/{archive_file_name}")
                    if str(row.get("delete_original", "False")).lower() == "true":
                        self.sp.delete_original(drive_id, folder_name, original_file_name)
                        print(f"🧹 Deleted original: {original_file_name}")
                except Exception as e:
                    print(f"⚠️ Archive/Cleanup failed for '{original_file_name}': {e}")


# ---- Backwards-compatible thin facade ----
class TransferFromSharepoint:
    
    def __init__(self, config, spark):
        self.config = config
        self.spark = spark

        azure_auth = self.config.get("azure-authentication", {})
        client_id = azure_auth.get("appreg_siteselect_client_id")
        client_secret = azure_auth.get("appreg_siteselect_client_secret")
        tenant_id = azure_auth.get("tenant_id")
        if not all([client_id, client_secret, tenant_id]):
            raise ValueError("Missing Azure authentication credentials in config.json")

        # print(config.get("workspace", {}))
        # print(config.get("bronze", {}))
        # print(config.get("sharepoint", {}))

        sp_cfg = self.config.get("sharepoint", {})
        hostname = sp_cfg.get("hostname")
        site_path = sp_cfg.get("site_path")
        
        if not all([hostname, site_path]):
            raise ValueError("Missing SharePoint configuration in config.json")

        token = AzureAuthenticator(tenant_id, client_id, client_secret).get_access_token()
        self.sp = SharePointService(token, hostname, site_path)
        self.discovery = FileDiscovery(self.sp, site_path, tz="Asia/Kuala_Lumpur")
        lakehouse_root = self.config["bronze"]["lakehouse_root"]
        self.lakehouse = LakehouseService(lakehouse_root)
        self.orchestrator = SharePointToLakehouseOrchestrator(self.sp, self.discovery, self.lakehouse, tz="Asia/Kuala_Lumpur")

    def process_files(self):
        source_folder_list = self.config.get("sharepoint", {}).get("source_folder_list", [])
        self.orchestrator.run(source_folder_list)


# In[16]:


processor = TransferFromSharepoint(config, spark)
processor.process_files()


import os
import requests
import pandas as pd
from dotenv import load_dotenv
from bs4 import BeautifulSoup

load_dotenv()  # loads .env file

TENANT_ID = os.getenv("TENANT_ID")
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")

# Microsoft OAuth2 token endpoint for client credential flow
TOKEN_URL = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"

# Microsoft Graph API endpoint to get messages from folder 'Smoke-setup1'
# Adjust mailbox and folder id as needed
GRAPH_API_BASE = "https://graph.microsoft.com/v1.0"

def get_access_token():
    payload = {
        "client_id": CLIENT_ID,
        "scope": "https://graph.microsoft.com/.default",
        "client_secret": CLIENT_SECRET,
        "grant_type": "client_credentials",
    }
    r = requests.post(TOKEN_URL, data=payload)
    r.raise_for_status()
    token = r.json().get("access_token")
    return token

def get_folder_id(access_token, folder_name="Smoke-setup1"):
    # Get the folder ID of the specified folder in mailbox Inbox
    headers = {"Authorization": f"Bearer {access_token}"}
    url = f"{GRAPH_API_BASE}/me/mailFolders/inbox/childFolders"
    r = requests.get(url, headers=headers)
    r.raise_for_status()
    folders = r.json().get("value", [])
    for f in folders:
        if f.get("displayName") == folder_name:
            return f.get("id")
    return None

def get_messages(access_token, folder_id, top=10):
    # Get messages from folder_id
    headers = {"Authorization": f"Bearer {access_token}"}
    url = f"{GRAPH_API_BASE}/me/mailFolders/{folder_id}/messages?$top={top}"
    r = requests.get(url, headers=headers)
    r.raise_for_status()
    messages = r.json().get("value", [])
    return messages

def extract_table_from_html(html):
    # Parse the Selenium report table from email HTML content
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table")
    if not table:
        return None

    # Extract table headers
    headers = [th.text.strip() for th in table.find_all("th")]
    rows = []
    for tr in table.find_all("tr")[1:]:  # skip header row
        cells = [td.text.strip() for td in tr.find_all("td")]
        if cells:
            rows.append(cells)

    # Create DataFrame
    df = pd.DataFrame(rows, columns=headers)
    
    # Convert numeric columns to int if possible
    for col in ["TOTAL", "PASSED", "FAILED", "SKIPPED"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)
    return df

def fetch_reports():
    access_token = get_access_token()
    folder_id = get_folder_id(access_token, folder_name="Smoke-setup1")
    if not folder_id:
        print("Folder 'Smoke-setup1' not found.")
        return None

    messages = get_messages(access_token, folder_id, top=5)  # get last 5 emails
    all_reports = []

    for msg in messages:
        body = msg.get("body", {}).get("content", "")
        df = extract_table_from_html(body)
        if df is not None:
            all_reports.append(df)

    if all_reports:
        # Concatenate all reports into one DataFrame with a new column for timestamp
        combined = pd.concat(all_reports, ignore_index=True)
        return combined
    else:
        print("No valid report tables found in emails.")
        return None

if __name__ == "__main__":
    df = fetch_reports()
    if df is not None:
        print(df)
    else:
        print("No report data found.")

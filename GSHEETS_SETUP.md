# Google Sheets Setup Guide

To enable cloud persistence for the 12-Week Execution Engine, follow these steps:

## 1. Enable the API
1.  Go to the [Google Cloud Console](https://console.cloud.google.com/).
2.  Create a new project (e.g., "Twelve-Week-Year").
3.  Search for **"Google Sheets API"** and enable it.
4.  Search for **"Google Drive API"** and enable it (optional, but often helpful).

## 2. Create Service Account
1.  Go to **APIs & Services > Credentials**.
2.  Click **Create Credentials > Service Account**.
3.  Name it (e.g., "streamlit-bot") and click **Create**.
4.  (Optional) Skip role assignment for now (or give "Editor" if needed).
5.  Click on the newly created Service Account email.
6.  Go to the **Keys** tab > **Add Key** > **Create new key** > **JSON**.
7.  Save this file! You will copy its contents into `.streamlit/secrets.toml`.

## 3. Share the Sheet
1.  Create a new Google Sheet.
2.  Name one tab **"Tactics"**.
3.  Click **Share** in the top right.
4.  Paste the **client_email** from your JSON key file (e.g., `streamlit-bot@...iam.gserviceaccount.com`).
5.  Give it **Editor** access.
6.  Copy the URL of the sheet.

## 4. Configure Streamlit
1.  Create a file `.streamlit/secrets.toml` in your project folder.
2.  Copy the content from `secrets.toml.example`.
3.  Replace `YOUR_SHEET_ID_HERE` with the ID from your Sheet URL.
4.  Paste the contents of your JSON key file into the `[connections.gsheets.service_account]` section.

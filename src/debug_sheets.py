import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import sys
import os

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

st.title("Debug Google Sheets (Direct Mode)")

# Define Scopes explicitly
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

st.header("Direct Connection Test")

try:
    # 1. Load Credentials from Secrets
    if "connections" not in st.secrets or "gsheets" not in st.secrets["connections"]:
        st.error("Secrets missing!")
        st.stop()
        
    creds_dict = st.secrets["connections"]["gsheets"]["service_account"]
    
    # 2. Create Credentials Object
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    st.write("✅ Credentials Object Created")
    
    # 3. Authorize Client
    client = gspread.authorize(creds)
    st.write("✅ Client Authorized")
    
    # 4. Open Spreadsheet
    url = st.secrets["connections"]["gsheets"]["spreadsheet"]
    st.write(f"Opening URL: `{url}`")
    
    sh = client.open_by_url(url)
    st.write(f"✅ Spreadsheet Found: **{sh.title}**")
    
    # 5. Read Worksheet
    worksheet = sh.worksheet("Tactics")
    st.write(f"✅ Worksheet Found: **{worksheet.title}**")
    
    data = worksheet.get_all_records()
    st.write(f"✅ Data Read: {len(data)} rows")
    st.write(data)

except Exception as e:
    st.error("❌ FAILED")
    st.markdown(f"**Error Type:** `{type(e).__name__}`")
    st.markdown(f"**Error Message:** `{str(e)}`")
    
    if "401" in str(e):
        st.warning("Still 401. This usually means the API is not enabled in the project associated with this Service Account.")
    if "403" in str(e):
        st.warning("403 Error. This means the Service Account does not have permission to access this specific sheet.")

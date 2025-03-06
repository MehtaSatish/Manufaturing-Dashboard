import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(layout="wide")

st.title("📊 Device Manufacturing and Assembly Dashboard")

# ✅ Define the correct OAuth Scopes
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/drive"
]

# ✅ Load credentials from secrets.toml
credentials_dict = st.secrets["GOOGLE_SHEETS_CREDENTIALS"]

# ✅ Authenticate using correct scopes
creds = Credentials.from_service_account_info(credentials_dict, scopes=SCOPES)
client = gspread.authorize(creds)

# ✅ Open Google Sheet
sheet_url = "https://docs.google.com/spreadsheets/d/1iWmEDXzfoqRPenAePMBOPSR-NCwelPCU-yZcQOyTltA/edit#gid=451421278"
spreadsheet = client.open_by_url(sheet_url)
worksheet = spreadsheet.worksheet("Sheet2")
dashboard_worksheet = spreadsheet.worksheet("DashBoard")

# ✅ Read data from Google Sheets
data = worksheet.get_all_records()
df = pd.DataFrame(data)

# ✅ Trim spaces from column names
df.columns = df.columns.str.strip()

st.write("### Inventory Overview")
st.dataframe(df)

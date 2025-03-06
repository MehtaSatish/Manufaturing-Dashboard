import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import datetime
import gspread
import toml  # Import for reading secrets locally
from google.oauth2.service_account import Credentials

st.set_page_config(layout="wide")

st.title("📊 Device Manufacturing and Assembly Dashboard")

# 1️⃣ Load credentials from `secrets.toml` locally
with open(".streamlit/secrets.toml", "r") as f:
    secrets = toml.load(f)

credentials_dict = {
    "type": secrets["connections.gsheets"]["type"],
    "project_id": secrets["connections.gsheets"]["project_id"],
    "private_key_id": secrets["connections.gsheets"]["private_key_id"],
    "private_key": secrets["connections.gsheets"]["private_key"].replace('\\n', '\n'),  # Handle newline issue
    "client_email": secrets["connections.gsheets"]["client_email"],
    "client_id": secrets["connections.gsheets"]["client_id"],
    "auth_uri": secrets["connections.gsheets"]["auth_uri"],
    "token_uri": secrets["connections.gsheets"]["token_uri"],
    "auth_provider_x509_cert_url": secrets["connections.gsheets"]["auth_provider_x509_cert_url"],
    "client_x509_cert_url": secrets["connections.gsheets"]["client_x509_cert_url"]
}

# 2️⃣ Authenticate with Google Sheets using `gspread`
SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_info(credentials_dict, scopes=SCOPES)
client = gspread.authorize(creds)

# 3️⃣ Open Google Sheet
sheet_url = secrets["connections.gsheets"]["spreadsheet"]
spreadsheet = client.open_by_url(sheet_url)

# Read the "Sheet2" worksheet
worksheet = spreadsheet.worksheet("Sheet2")
data = worksheet.get_all_records()
df = pd.DataFrame(data)

# Trim spaces from column names
df.columns = df.columns.str.strip()

st.write("### Data Preview")
st.dataframe(df)

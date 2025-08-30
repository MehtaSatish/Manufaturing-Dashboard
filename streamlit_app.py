import streamlit as st
import pandas as pd
import gspread
import plotly.express as px
import plotly.graph_objects as go
import datetime
from google.oauth2.service_account import Credentials


# Set Page Config
st.set_page_config(layout="wide", page_title="📊 Device Manufacturing Dashboard")

# Toggle this to True or False to enable/disable login requirement
ENABLE_LOGIN = True  # Set False to skip login during development

# Load user credentials from secrets
USER_CREDENTIALS = st.secrets["USER_CREDENTIALS"]

# Initialize required session state variables if not present
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = None

def login():
    """Login function to authenticate user"""
    st.title("🔐 Login Page")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if username in USER_CREDENTIALS and USER_CREDENTIALS[username] == password:
            st.session_state.logged_in = True
            st.session_state.username = username
            st.success("✅ Login Successful!")
            st.rerun()
        else:
            st.error("❌ Invalid Username or Password!")

def logout():
    """Logout function"""
    st.session_state.logged_in = False
    st.session_state.username = None
    st.success("🔒 Logged out successfully!")
    st.rerun()

if ENABLE_LOGIN:
    if not st.session_state.logged_in:
        login()
        st.stop()
else:
    # Auto-login a default user (optional) during development
    if not st.session_state.logged_in:
        st.session_state.logged_in = True
        st.session_state.username = "dev_user"

# ---- MAIN APP ----
st.sidebar.button("Logout", on_click=logout)
st.sidebar.write(f"👤 Logged in as: `{st.session_state.username}`")

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

# ✅ Fetch data for PWA Inventory scorecards
scorecard_data = dashboard_worksheet.get_values("X8:Y8")
additional_scorecards = dashboard_worksheet.get_values("AA2:AB4")

# 🔹 Create four columns for scorecards
col1, col2, col3, col4 = st.columns(4)

# 🔹 Display PWA Inventory scorecard in the first column
if scorecard_data:
    with col1:
        label, value = scorecard_data[0][0], int(scorecard_data[0][1])
        fig_scorecard = go.Figure(go.Indicator(
            mode="number",
            value=value,
            title={"text": label, "font": {"size": 18}},  # Reduce title size
            number={"font": {"size": 48, "color": "#636EFA"}},  # Adjusted number size
        ))
        # Reduce margins and set a fixed height
        fig_scorecard.update_layout(
            margin=dict(l=0, r=0, t=0, b=0),  # Remove all margins
            height=150  # Force smaller height to reduce spacing
        )
        st.plotly_chart(fig_scorecard, use_container_width=True, config={"displayModeBar": False})

# 🔹 Display additional inventory scorecards in the remaining three columns
if additional_scorecards:
    cols = [col2, col3, col4]
    
    for i, row in enumerate(additional_scorecards):
        if i < len(cols):
            with cols[i]:
                label, value = row[0], int(row[1])
                fig_scorecard = go.Figure(go.Indicator(
                    mode="number",
                    value=value,
                    title={"text": label, "font": {"size": 18}},  # Reduce title size
                    number={"font": {"size": 48, "color": "#FFA600"}},  # Adjusted number size
                ))
                # Reduce margins and set a fixed height
                fig_scorecard.update_layout(
                    margin=dict(l=0, r=0, t=0, b=0),  # Remove all margins
                    height=150  # Force smaller height to reduce spacing
                )
                st.plotly_chart(fig_scorecard, use_container_width=True, config={"displayModeBar": False})
# Fetch header row for both batches (W1:Z1)
progress_labels = dashboard_worksheet.get_values("W1:Z1")
if progress_labels:
    labels = progress_labels[0]


# ---- Fetch Data from Dashboard Sheet ----
progress_data = dashboard_worksheet.get_values("W1:Z2")
if progress_data:
    labels = progress_data[0]
    values = list(map(int, progress_data[1]))

    used_pwa = values[labels.index('Used')]
    failed_pwa = values[labels.index('Failed')] + used_pwa
    total_pwa = values[labels.index('Total PWA')]
    gauge_start = 0

# Define columns with equal widths
col1, col2, col3 = st.columns([1, 1, 1])


def draw_gauge(col, title, used_pwa, failed_pwa, total_pwa):
    with col:
        percentage = (used_pwa / total_pwa) * 100 if total_pwa else 0

        fig = go.Figure()
        fig.add_trace(go.Indicator(
            mode="gauge+number",
            value=used_pwa,
            number={'font': {'size': 24}},  # Smaller font
            gauge={
                'shape': "angular",
                'axis': {
                    'range': [0, total_pwa],
                    'tickmode': "array",
                    'tickvals': [0, used_pwa, failed_pwa, total_pwa],
                    'tickfont': {'size': 16}  # Smaller ticks
                },
                'bar': {'color': "rgba(0,0,0,0)"},
                'bgcolor': "rgba(0,0,0,0)",
                'steps': [
                    {'range': [0, used_pwa], 'color': "#66cdfb"},
                    {'range': [used_pwa, failed_pwa], 'color': "#FF5733"},
                    {'range': [failed_pwa, total_pwa], 'color': "#D3D3D3"},
                ],
                'threshold': {
                    'line': {'color': "#D3D3D3", 'width': 0},
                    'thickness': 0
                }
            },
            domain={'x': [0.1, 0.9], 'y': [0, 0.7]}  # Tighter bounds
        ))

        fig.update_layout(
            margin=dict(t=10, b=10, l=10, r=10),
            height=260,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )

        st.caption(title)
        st.plotly_chart(fig, use_container_width=True)

        # Add percentage line below
        st.markdown(
            f"<div style='text-align:center; margin-top:-10px;'>"
            f"<hr style='border-top: 1px solid #bbb; width: 60%; margin: 2px auto;'/>"
            f"<span style='font-size: 24px; color: #ddd;'>{percentage:.1f}% used</span>"
            f"</div>",
            unsafe_allow_html=True
        )


# 1st Chart
draw_gauge(col2, "Batch 3 Invertory", used_pwa, failed_pwa, total_pwa)

# 2nd Chart (Batch W3)
progress_data = dashboard_worksheet.get_values("W1:Z1")
count_data = dashboard_worksheet.get_values("W3:Z3")
if progress_data and count_data:
    labels = progress_data[0]
    values = list(map(int, count_data[0]))
    used_pwa = values[labels.index('Used')]
    failed_pwa = values[labels.index('Failed')] + used_pwa
    total_pwa = values[labels.index('Total PWA')]
    draw_gauge(col1, "Batch 2 Inventory", used_pwa, failed_pwa, total_pwa)

# 3rd Chart (Batch W4)
label_row = dashboard_worksheet.get_values("W1:Z1")
count_row = dashboard_worksheet.get_values("W4:Z4")
if label_row and count_row:
    labels = label_row[0]
    values = list(map(int, count_row[0]))
    used_pwa = values[labels.index('Used')]
    failed_pwa = values[labels.index('Failed')] + used_pwa
    total_pwa = values[labels.index('Total PWA')]
    draw_gauge(col3, "Batch 4 Inventory", used_pwa, failed_pwa, total_pwa)
# ----- Shared Legend Below Charts -----
st.markdown(
    """
    <div style='text-align:center; margin-top: 20px;'>
        <span style='display:inline-block; margin-right: 20px;'>
            <span style='display:inline-block; width:14px; height:14px; background-color:#66cdfb; border-radius:3px; margin-right:6px;'></span>
            <span style='color:#ddd;'>Used PWA</span>
        </span>
        <span style='display:inline-block; margin-right: 20px;'>
            <span style='display:inline-block; width:14px; height:14px; background-color:#FF5733; border-radius:3px; margin-right:6px;'></span>
            <span style='color:#ddd;'>Failed PWA</span>
        </span>
        <span style='display:inline-block;'>
            <span style='display:inline-block; width:14px; height:14px; background-color:#D3D3D3; border-radius:3px; margin-right:6px;'></span>
            <span style='color:#ddd;'>Remaining PWA</span>
        </span>
    </div>
    """,
    unsafe_allow_html=True
)


# --- DEVICE ASSEMBLY TREND DASHBOARD (Batch 3) ---
st.write("### Device Assembly Trend")
# Ensure the required columns exist
required_columns = ["Date of Assambly", "Device Type", "PWA No"]
if all(col in df.columns for col in required_columns):
    
    # Convert Date column to datetime
    df["Date of Assambly"] = pd.to_datetime(df["Date of Assambly"], errors="coerce")
    
    # Filter invalid dates
    df = df.dropna(subset=["Date of Assambly"])
    
    col1, col2 = st.columns(2)

with col1:
      # Prevent auto-scrolling when selecting a device type
    st.markdown(
     """
    <style>
        div[data-testid='stRadio'] label {
            display: flex;
            align-items: center;
            padding: 6px 12px;
            margin-right: 10px;
            cursor: pointer;
            transition: all 0.3s;
            flex-direction: row;
        }
        div[data-testid='stRadio'] label:hover {
            background-color: #f0f0f0;
        }
        div[data-testid='stRadio'] label span {
            margin-right: 8px;
        }
    </style>
    """,
    unsafe_allow_html=True
    )
   # Tab selection for device type before date selection
    device_types = df["Device Type"].unique()
    if len(device_types) > 0:
        selected_device = st.radio("Select Device Type", device_types, horizontal=True, key="device_type")
    else:
        st.warning("No device types available.")
        st.stop()

    # Get today's date
    today = datetime.date.today()
    start_of_week = today - datetime.timedelta(days=today.weekday())
    start_of_month = today.replace(day=1)
    start_of_quarter = today.replace(month=((today.month - 1) // 3) * 3 + 1, day=1)
    
    # Radio button for quick date selection
    date_option = st.radio("Quick Select Date Range", ["Custom", "This Week", "This Month", "This Quarter"], horizontal=True)
    
    if date_option == "This Week":
        start_date, end_date = start_of_week, today
    elif date_option == "This Month":
        start_date, end_date = start_of_month, today
    elif date_option == "This Quarter":
        start_date, end_date = start_of_quarter, today
    else:
        col3, col4 = st.columns(2)
        with col3:
            start_date = st.date_input("From", today - datetime.timedelta(days=30))
        with col4:
            end_date = st.date_input("To", today)
    
    # Ensure start_date is before end_date
    if start_date > end_date:
        st.error("Start date cannot be after end date.")
        st.stop()
with col2:  
    # Filter data based on selected device type and dates
    filtered_df = df[(df["Device Type"] == selected_device) &
                     (df["Date of Assambly"] >= pd.to_datetime(start_date)) &
                     (df["Date of Assambly"] <= pd.to_datetime(end_date))]
    
    # Filter data for selected device type and remove non-manufacturing days
    device_counts = filtered_df.groupby("Date of Assambly").size().reset_index(name="Count")
    
    # Keep only days where manufacturing occurred
    device_counts = device_counts[device_counts["Count"] > 0]

    # Adjust bar width by treating dates as categorical
    device_counts["Date of Assambly"] = device_counts["Date of Assambly"].astype(str)

    # Create bar chart with rounded edges and emphasized data labels
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=device_counts["Date of Assambly"],
        y=device_counts["Count"],
        marker=dict(color="#66cdfb", opacity=0.9),
    ))
    
    # Apply rounded corners
    fig.update_traces(marker=dict(cornerradius=10))
    
    # Add circles around data labels for emphasis
    for i, row in device_counts.iterrows():
        fig.add_trace(go.Scatter(
            x=[row["Date of Assambly"]],
            y=[row["Count"]],
            mode="markers+text",
            marker=dict(size=30, color="#66cdfb", opacity=0.6),
            text=[row["Count"]],
            textfont=dict(size=14, color="white"),
            textposition="middle center",
            hoverinfo="none"
        ))
    
    # Improve layout
    fig.update_layout(
        title=f"Device Assembly Trend for {selected_device}",
        xaxis=dict(type='category', tickangle=-45),
        yaxis=dict(title="Count"),
        bargap=0.2, bargroupgap=0.02,
        showlegend=False
    )
    
    st.plotly_chart(fig)


# Display Data Preview from Sheet2
#st.write("### Data Preview (Manufacturing Data):")
#entries_to_show = st.selectbox("Show entries", options=[50, 100, 200, len(df)], index=0)
#st.dataframe(df.head(entries_to_show))

# Fetch data from Sheet1
worksheet2 = spreadsheet.worksheet("Sheet1")  # Fetching data from Sheet1
data2 = worksheet2.get_values("A:I")
df2 = pd.DataFrame(data2[1:], columns=data2[0])  # First row as header

# Trim spaces from column names
df2.columns = df2.columns.str.strip()

# Display Data Preview from Sheet1
#st.write("### Data Preview (Assembly Data):")
#entries_to_show2 = st.selectbox("Show entries", options=[50, 100, 200, len(df2)], index=0, key="assembly_entries")
#st.dataframe(df2.head(entries_to_show2))


# --- PWA DISTRIBUTION DASHBOARD (Batch 4 above Batch 3) ---

st.write("### PWA Distribution")

# --- BATCH 4 DATA (example: device types in X10:X14, counts in Y10:Y14) ---
# Adjust the ranges below as per actual dashboard layout

# Fetch device types (assumed same as Batch 3, i.e., header row of W9:X13, column X)
device_types_batch = dashboard_worksheet.get_values("W10:W13")
device_types_batch = [item[0] for item in device_types_batch] if device_types_batch else []

# Fetch Batch 4 counts (Y10:Y14)
batch4_counts = dashboard_worksheet.get_values("Y10:Y13")
batch4_counts = [int(item[0]) if item and item[0] else 0 for item in batch4_counts] if batch4_counts else []

# Prepare DataFrame for Batch 4
if device_types_batch and batch4_counts and len(device_types_batch) == len(batch4_counts):
    df_dashboard4 = pd.DataFrame({
        "Device Type": device_types_batch,
        "Count": batch4_counts
    })

    col4_1, col4_2 = st.columns(2)
    # Batch 4 Bar Chart
    with col4_2:
        fig_dashboard4 = go.Figure()
        fig_dashboard4.add_trace(go.Bar(
            x=df_dashboard4["Device Type"],
            y=df_dashboard4["Count"],
            marker=dict(color="#FFA600", opacity=0.9),
        ))
        fig_dashboard4.update_traces(marker=dict(cornerradius=10))

        for i, row in df_dashboard4.iterrows():
            fig_dashboard4.add_trace(go.Scatter(
                x=[row["Device Type"]],
                y=[row["Count"]],
                mode="markers+text",
                marker=dict(size=30, color="#FFA600", opacity=0.6),
                text=[row["Count"]],
                textfont=dict(size=14, color="white"),
                textposition="middle center",
                hoverinfo="none"
            ))
        fig_dashboard4.update_layout(
            title="Batch 4 Distribution",
            xaxis=dict(type='category', tickangle=0, title="Device Type"),
            yaxis=dict(title="Count"),
            bargap=0.2, bargroupgap=0.02,
            showlegend=False
        )
        st.plotly_chart(fig_dashboard4, use_container_width=True)

    # Batch 4 Doughnut Chart
    with col4_1:
        fig_doughnut4 = go.Figure()
        fig_doughnut4.add_trace(go.Pie(
            labels=df_dashboard4["Device Type"],
            values=df_dashboard4["Count"],
            hole=0.4,
            marker=dict(colors=["#636EFA", "#EF553B", "#00CC96", "#AB63FA", "#FFA15A"]),
            textinfo="percent+label"
        ))
        fig_doughnut4.update_layout(
            title="Batch 4 Percentage Distribution",
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.2,
                xanchor="right",
                x=0.85
            )
        )
        st.plotly_chart(fig_doughnut4, use_container_width=True)

# --- BATCH 3 DATA (Original code, just after Batch 4 section) ---
dashboard_data = dashboard_worksheet.get_values("W9:X13")
df_dashboard = pd.DataFrame(dashboard_data[1:], columns=dashboard_data[0])  # First row as header
df_dashboard.columns = df_dashboard.columns.str.strip()

col3_1, col3_2 = st.columns(2)
# Bar Chart for Batch 3
with col3_2:
    fig_dashboard = go.Figure()
    fig_dashboard.add_trace(go.Bar(
        x=df_dashboard[df_dashboard.columns[0]],
        y=pd.to_numeric(df_dashboard[df_dashboard.columns[1]], errors='coerce'),
        marker=dict(color="#FFA600", opacity=0.9),
    ))
    fig_dashboard.update_traces(marker=dict(cornerradius=10))

    for i, row in df_dashboard.iterrows():
        fig_dashboard.add_trace(go.Scatter(
            x=[row[df_dashboard.columns[0]]],
            y=[pd.to_numeric(row[df_dashboard.columns[1]], errors='coerce')],
            mode="markers+text",
            marker=dict(size=30, color="#FFA600", opacity=0.6),
            text=[row[df_dashboard.columns[1]]],
            textfont=dict(size=14, color="white"),
            textposition="middle center",
            hoverinfo="none"
        ))
    fig_dashboard.update_layout(
        title="Batch 3 Distribution",
        xaxis=dict(type='category', tickangle=0, title=df_dashboard.columns[0]),
        yaxis=dict(title=df_dashboard.columns[1]),
        bargap=0.2, bargroupgap=0.02,
        showlegend=False
    )
    st.plotly_chart(fig_dashboard, use_container_width=True)

# Doughnut Chart for Batch 3
with col3_1:
    fig_doughnut = go.Figure()
    fig_doughnut.add_trace(go.Pie(
        labels=df_dashboard[df_dashboard.columns[0]],
        values=pd.to_numeric(df_dashboard[df_dashboard.columns[1]], errors='coerce'),
        hole=0.4,
        marker=dict(colors=["#636EFA", "#EF553B", "#00CC96", "#AB63FA", "#FFA15A"]),
        textinfo="percent+label"
    ))
    fig_doughnut.update_layout(
        title="Batch 3 Percentage Distribution",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.2,
            xanchor="right",
            x=0.85
        )
    )
    st.plotly_chart(fig_doughnut, use_container_width=True)


# Fetch data from DashBoard sheet (X15:Z27) for stacked bar and stacked line chart
stacked_data = dashboard_worksheet.get_values("X15:Z27")
df_stacked = pd.DataFrame(stacked_data[1:], columns=stacked_data[0])  # First row as header

# Convert columns to numeric, skipping rows with zero values
df_stacked[df_stacked.columns[1]] = pd.to_numeric(df_stacked[df_stacked.columns[1]], errors='coerce')
df_stacked[df_stacked.columns[2]] = pd.to_numeric(df_stacked[df_stacked.columns[2]], errors='coerce')
df_stacked = df_stacked[(df_stacked[df_stacked.columns[1]] > 0) | (df_stacked[df_stacked.columns[2]] > 0)]
st.write("### Monthly Production")
# Create two columns
col1, col2 = st.columns(2)

# Create stacked bar chart with data labels
if not df_stacked.empty:
    with col1:
        
        fig_stacked = go.Figure()

        # Add first dataset (Y column)
        fig_stacked.add_trace(go.Bar(
            x=df_stacked[df_stacked.columns[0]],
            y=df_stacked[df_stacked.columns[1]],
            name=df_stacked.columns[1],
            marker=dict(color="#636EFA", opacity=0.9, line=dict(width=0))
        ))

        # Add second dataset (Z column) stacked above Y
        fig_stacked.add_trace(go.Bar(
            x=df_stacked[df_stacked.columns[0]],
            y=df_stacked[df_stacked.columns[2]],
            name=df_stacked.columns[2],
            marker=dict(color="#FFA600", opacity=0.9, line=dict(width=0))
        ))

        # Apply rounded corners
        fig_stacked.update_traces(marker=dict(cornerradius=10))

        # Add data labels on top of each stacked bar (Y + Z)
        for i, row in df_stacked.iterrows():
            total_value = row[df_stacked.columns[1]] + row[df_stacked.columns[2]]
            fig_stacked.add_trace(go.Scatter(
                x=[row[df_stacked.columns[0]]],
                y=[total_value],
                mode="markers+text",
                marker=dict(size=30, color="#FF5733", opacity=0.6),  # Adjust color if needed
                text=[total_value],
                textfont=dict(size=14, color="white"),
                textposition="middle center",
                hoverinfo="none"
            ))

        # Improve layout with bottom legend
        fig_stacked.update_layout(
            barmode='stack',
            xaxis=dict(title=df_stacked.columns[0]),
            yaxis=dict(title="Value"),
            bargap=0.2, bargroupgap=0.02,
            showlegend=False,
            legend=dict(orientation="h", yanchor="top", y=-0.2, xanchor="center", x=0.5)  # Move legend to bottom
        )

        st.plotly_chart(fig_stacked, use_container_width=True)


# Stacked Line Chart in Second Column
if not df_stacked.empty:
    with col2:
        #st.write("### "")")
        fig_line = go.Figure()

        colors = ["#636EFA", "#FFA600"]  # Dark theme-friendly colors

        # Add first dataset (Y column)
        fig_line.add_trace(go.Scatter(
            x=df_stacked[df_stacked.columns[0]],
            y=df_stacked[df_stacked.columns[1]],
            mode="lines",
            name=df_stacked.columns[1],
            line=dict(shape="spline", width=3, color=colors[0]),
            fill="tonexty",  # Fill below the line
            fillcolor=f"rgba{tuple(int(colors[0][1:][j:j+2], 16) for j in (0, 2, 4)) + (0.3,)}"
        ))

        # Add second dataset (Z column) stacked above Y
        fig_line.add_trace(go.Scatter(
            x=df_stacked[df_stacked.columns[0]],
            y=df_stacked[df_stacked.columns[2]] + df_stacked[df_stacked.columns[1]],  # Stack Z on top of Y
            mode="lines",
            name=df_stacked.columns[2],
            line=dict(shape="spline", width=3, color=colors[1]),
            fill="tonexty",  # Fill above the first line
            fillcolor=f"rgba{tuple(int(colors[1][1:][j:j+2], 16) for j in (0, 2, 4)) + (0.3,)}"
        ))

        # Improve layout for dark theme and move legend to bottom
        fig_line.update_layout(
            xaxis=dict(title=df_stacked.columns[0], gridcolor="rgba(255,255,255,0.2)"),
            yaxis=dict(title="Value", gridcolor="rgba(255,255,255,0.2)"),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            showlegend=True,
            legend=dict(orientation="h", yanchor="top", y=-0.2, xanchor="center", x=0.5)  # Move legend to bottom
        )

        st.plotly_chart(fig_line, use_container_width=True)



import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import datetime
import gspread
#from google.oauth2.service_account import Credentials
from streamlit_gsheets import GSheetsConnection

st.set_page_config(layout="wide")

st.title("📊 Device Manufacturing and Assembly Dashboard")

# 1️⃣ Create a connection to Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# Load credentials from Streamlit Secrets
#credentials_dict = st.secrets["GOOGLE_SHEETS_CREDENTIALS"]
print("Credentials loaded successfully.") #add this line




# 2️⃣ Fetch data from the Google Sheet
sheet_url = "https://docs.google.com/spreadsheets/d/1iWmEDXzfoqRPenAePMBOPSR-NCwelPCU-yZcQOyTltA/edit#gid=451421278"

# Read the "Sheet2" worksheet
worksheet = conn.read(spreadsheet=sheet_url, worksheet="Sheet2", ttl=300)  # Cached for 5 min

# Convert to DataFrame
df = pd.DataFrame(worksheet)

if df.empty:
    st.error("Failed to load data from Google Sheets.")
    st.stop()

# Trim spaces from column names
df.columns = df.columns.str.strip()

# 3️⃣ Fetch data for Dashboard worksheet
dashboard_worksheet = conn.read(spreadsheet=sheet_url, worksheet="DashBoard", ttl=300)

if dashboard_worksheet.empty:
    st.error("Failed to load dashboard data from Google Sheets.")
    st.stop()

# Fetch specific ranges for PWA Inventory and Additional Inventory
scorecard_data = dashboard_worksheet.iloc[7:8, 23:25].values  # X8:Y8
additional_scorecards = dashboard_worksheet.iloc[1:4, 26:28].values  # AA2:AB4

st.write("### Inventory Overview")

st.write("### Inventory Overview")

# Create four columns for scorecards
col1, col2, col3, col4 = st.columns(4)

# Display PWA Inventory scorecard in the first column
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
            height=150 # Force smaller height to reduce spacing
        )
        st.plotly_chart(fig_scorecard, use_container_width=True, config={"displayModeBar": False})

# Display additional inventory scorecards in the remaining three columns
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

# Fetch data from DashBoard sheet (W1:Z2) for progress bar
progress_data = dashboard_worksheet.get_values("W1:Z2")
if progress_data:
    labels = progress_data[0]
    values = list(map(int, progress_data[1]))
    total_pwa = values[-1] if values[-1] > 0 else 1  # Avoid division by zero
    
   
    fig_progress = go.Figure()
    fig_progress.add_trace(go.Bar(
        y=["PWA"],
        x=[values[0]],
        name=labels[0],
        marker=dict(color="#636EFA"),
        orientation="h"
    ))
    fig_progress.add_trace(go.Bar(
        y=["PWA"],
        x=[values[1]],
        name=labels[1],
        marker=dict(color="#EF553B"),
        orientation="h"
    ))
    fig_progress.add_trace(go.Bar(
        y=["PWA"],
        x=[values[2]],
        name=labels[2],
        marker=dict(color="#00CC96"),
        orientation="h"
    ))
    
    fig_progress.update_traces(
    marker=dict(
        cornerradius=5,  # Rounded edges
        line=dict(width=1, color="white"),  # Add subtle white separators
    )
)

fig_progress.update_layout(
    title="Batch 3 Board Inventory Tracking",
    xaxis=dict(title="Count", range=[0, total_pwa]),
    barmode="stack",
    showlegend=True,
    height=220,  # Slightly increased thickness
    bargap=0.1,  # Reduce gap between bars for a solid look
    legend=dict(orientation="h", yanchor="top", y=-0.2, xanchor="center", x=0.5),  # Move legend to bottom
)

st.plotly_chart(fig_progress, use_container_width=True)


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

# 1️⃣ Fetch data from "Sheet1"
worksheet2 = conn.read(spreadsheet=sheet_url, worksheet="Sheet1", ttl=300)  # ✅ Fetching Sheet1

if worksheet2.empty:
    st.error("Failed to load data from Sheet1.")
    st.stop()
data2 = worksheet2.get_values("A:I")
df2 = pd.DataFrame(data2[1:], columns=data2[0])  # First row as header

# Trim spaces from column names
df2.columns = df2.columns.str.strip()

# Display Data Preview from Sheet1
#st.write("### Data Preview (Assembly Data):")
#entries_to_show2 = st.selectbox("Show entries", options=[50, 100, 200, len(df2)], index=0, key="assembly_entries")
#st.dataframe(df2.head(entries_to_show2))


# Fetch data from DashBoard sheet (W9:X14)
#dashboard_worksheet = spreadsheet.worksheet("DashBoard")
# 1️⃣ Fetch data from "DashBoard"
dashboard_worksheet = conn.read(spreadsheet=sheet_url, worksheet="DashBoard", ttl=300)  # ✅ Fetching DashBoard sheet

if dashboard_worksheet.empty:
    st.error("Failed to load data from DashBoard sheet.")
    st.stop()
dashboard_data = dashboard_worksheet.get_values("W9:X13")
df_dashboard = pd.DataFrame(dashboard_data[1:], columns=dashboard_data[0])  # First row as header

# Trim spaces from column names
df_dashboard.columns = df_dashboard.columns.str.strip()


# Trim spaces from column names
df_dashboard.columns = df_dashboard.columns.str.strip()



# Create bar chart from DashBoard sheet data with rounded edges and emphasized labels
if not df_dashboard.empty:
    fig_dashboard = go.Figure()
    fig_dashboard.add_trace(go.Bar(
        x=df_dashboard[df_dashboard.columns[0]],
        y=pd.to_numeric(df_dashboard[df_dashboard.columns[1]], errors='coerce'),
        marker=dict(color="#FFA600", opacity=0.9),
    ))
    
    # Apply rounded corners
    fig_dashboard.update_traces(marker=dict(cornerradius=10))
    
    # Add circles around data labels for emphasis
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
    
    # Improve layout
st.write("### PWA Distribution")

# Create two columns for the charts
col1, col2 = st.columns(2)

# Bar Chart in first column
with col2:
    fig_dashboard.update_layout(
        title="Batch 3 Distribution",
        xaxis=dict(type='category', tickangle=0, title=df_dashboard.columns[0]),
        yaxis=dict(title=df_dashboard.columns[1]),
        bargap=0.2, bargroupgap=0.02,
        showlegend=False
    )
    st.plotly_chart(fig_dashboard, use_container_width=True)

# Doughnut Chart in second column
with col1:
    if not df_dashboard.empty:
        fig_doughnut = go.Figure()
        fig_doughnut.add_trace(go.Pie(
        labels=df_dashboard[df_dashboard.columns[0]],
        values=pd.to_numeric(df_dashboard[df_dashboard.columns[1]], errors='coerce'),
        hole=0.4,  # Creates the doughnut shape
        marker=dict(colors=["#636EFA", "#EF553B", "#00CC96", "#AB63FA", "#FFA15A"]),
        textinfo="percent+label"
    ))

    fig_doughnut.update_layout(
        title="Percentage Distribution",
        legend=dict(
            orientation="h",   # Horizontal layout
            yanchor="bottom",  # Anchors legend to the bottom
            y=-0.2,            # Moves it below the chart
            xanchor="right",   # Aligns legend to the right
            x=0.85                # Positions legend to the right
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
st.write("### Monthly Production (Stacked Bar)")
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
            showlegend=True,
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

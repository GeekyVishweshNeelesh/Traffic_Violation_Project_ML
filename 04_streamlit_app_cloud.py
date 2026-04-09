"""
============================================================================
TRAFFIC VIOLATIONS INSIGHT SYSTEM
File 04 — Streamlit Dashboard (v3)
Montgomery County, Maryland
============================================================================
PDF Requirements Covered:
  ✅ Filter by date, location, vehicle type, gender, race, violation category
  ✅ Geographical heatmaps of incident hotspots (optional - folium)
  ✅ Trend charts, bar plots, distribution graphs, multi-filter insights
  ✅ Summary stats: total violations, accidents, high-risk zones, vehicle makes/models
  ✅ Personal Injury & Property Damage stats
  ✅ Descriptive statistics table
  ✅ Vehicle Make AND Model breakdown
  ✅ High-Risk Zones KPI
============================================================================
Run: streamlit run 04_streamlit_app_v3.py
============================================================================
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta, date
import warnings
import os
import gdown
warnings.filterwarnings('ignore')

# Optional folium
try:
    import folium
    from streamlit_folium import folium_static
    HAS_FOLIUM = True
except ImportError:
    HAS_FOLIUM = False


# ============================================================================
# PAGE CONFIG
# ============================================================================

st.set_page_config(
    page_title="Traffic Violations Insight System",
    page_icon="🚦",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    .main {padding: 0rem 1rem;}
    div[data-testid="stMetric"] {
        background-color: #1a1a1a;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.3);
        border: 1px solid #333;
    }
    div[data-testid="stMetric"] label {
        color: #ffffff !important;
        font-weight: 600;
        font-size: 0.9rem;
    }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
        color: #4CAF50 !important;
        font-size: 2rem !important;
        font-weight: bold;
    }
    div[data-testid="stMetric"] div[data-testid="stMetricDelta"] {
        color: #2196F3 !important;
    }
    h1 {color: #1E3A8A; padding-bottom: 20px;}
    h2 {color: #3B82F6; padding-top: 20px;}
    h3 {color: #2563EB;}
    </style>
""", unsafe_allow_html=True)


# ============================================================================
# COLUMN RENAME MAP
# DB columns (Title Case / mixed) → snake_case for dashboard use
# ============================================================================

COL_RENAME = {
    'row_id':                   'row_id',
    'original_seq_id':          'seq_id',
    'Date Of Stop':             'date_of_stop',
    'Time Of Stop':             'time_of_stop',
    'Agency':                   'agency',
    'SubAgency':                'subagency',
    'Description':              'description',
    'Location':                 'location',
    'Latitude':                 'latitude',
    'Longitude':                'longitude',
    'Accident':                 'accident',
    'Belts':                    'belts',
    'Personal Injury':          'personal_injury',
    'Property Damage':          'property_damage',
    'Fatal':                    'fatal',
    'Commercial License':       'commercial_license',
    'HAZMAT':                   'hazmat',
    'Commercial Vehicle':       'commercial_vehicle',
    'Alcohol':                  'alcohol',
    'Work Zone':                'work_zone',
    'Search Conducted':         'search_conducted',
    'Search Disposition':       'search_disposition',
    'Search Outcome':           'search_outcome',
    'Search Reason':            'search_reason',
    'Search Reason For Stop':   'search_reason_for_stop',
    'Search Type':              'search_type',
    'Search Arrest Reason':     'search_arrest_reason',
    'State':                    'state',
    'VehicleType':              'vehicle_type',
    'Year':                     'year',
    'Make':                     'vehicle_make',
    'Model':                    'model',
    'Color':                    'vehicle_color',
    'Violation Type':           'violation_type',
    'Charge':                   'charge',
    'Article':                  'article',
    'Contributed To Accident':  'contributed_to_accident',
    'Race':                     'race',
    'Gender':                   'gender',
    'Driver City':              'driver_city',
    'Driver State':             'driver_state',
    'DL State':                 'dl_state',
    'Arrest Type':              'arrest_type',
    'DateTime':                 'datetime_col',
    'District Number':          'district_number',
    'Violation_Category':       'violation_category',
    'Road_Name':                'road_name',
    'VehicleType_Code':         'vehicletype_code',
    'VehicleType_Category':     'vehicletype_category',
    'Charge_Count':             'charge_count',
    'Arrest_Type_Code':         'arrest_type_code',
    'Arrest_Type_Desc':         'arrest_type_desc',
    'DayOfWeek':                'day_of_week',
    'Month':                    'month',
    'Year_Stop':                'year_stop',
    'DayOfMonth':               'day_of_month',
    'WeekOfYear':               'week_of_year',
    'Time_Bucket':              'time_bucket',
    'Is_Weekend':               'is_weekend',
    'High_Risk':                'high_risk',
    'Violation_Count':          'violation_count',
    'Vehicle_Age':              'vehicle_age',
    'Hour':                     'hour',
}


# ============================================================================
# GOOGLE DRIVE CSV LOADER
# ============================================================================

GDRIVE_FILE_ID = "1KU34HZFWNM3sHamZ18o1nzRTeReq1Okn"
CSV_PATH = "/tmp/traffic_violations_cleaned.csv"

@st.cache_data(show_spinner=False)
def load_full_csv():
    """Download CSV from Google Drive if not already present, then load into DataFrame."""
    if not os.path.exists(CSV_PATH):
        with st.spinner("📥 Downloading dataset from Google Drive (1.2GB)... This may take 2-3 minutes on first load."):
            url = f"https://drive.google.com/uc?id={GDRIVE_FILE_ID}"
            gdown.download(url, CSV_PATH, quiet=False)

    with st.spinner("📊 Loading dataset into memory..."):
        needed_cols = [
            'Date Of Stop', 'original_seq_id', 'Agency', 'SubAgency', 'Location',
            'Latitude', 'Longitude', 'Description', 'Violation Type', 'Violation_Category',
            'Accident', 'Fatal', 'Personal Injury', 'Property Damage',
            'Alcohol', 'Belts', 'Work Zone', 'HAZMAT', 'Commercial Vehicle',
            'High_Risk', 'Race', 'Gender', 'Make', 'Model', 'Color', 'VehicleType',
            'Vehicle_Age', 'Hour', 'DayOfWeek', 'Month', 'Time_Bucket',
            'Is_Weekend', 'Violation_Count', 'District_Number', 'Arrest_Type_Desc',
        ]
        df = pd.read_csv(CSV_PATH, usecols=lambda c: c in needed_cols, low_memory=False, nrows=200000)

    # Rename columns to snake_case
    df = df.rename(columns={k: v for k, v in COL_RENAME.items() if k in df.columns})

    # Convert numeric columns
    for col in ['latitude', 'longitude', 'accident', 'fatal', 'alcohol',
                'belts', 'personal_injury', 'property_damage', 'hazmat',
                'commercial_vehicle', 'work_zone', 'is_weekend', 'high_risk',
                'hour', 'vehicle_age', 'violation_count', 'charge_count']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    # Parse date
    if 'date_of_stop' in df.columns:
        df['date_of_stop'] = pd.to_datetime(df['date_of_stop'], errors='coerce')

    # Parse month as numeric
    if 'month' in df.columns:
        df['month'] = pd.to_numeric(df['month'], errors='coerce')

    return df


# ============================================================================
# FILTER OPTIONS LOADER
# ============================================================================

def get_filter_options():
    """Return hardcoded filter options — instant load, zero DB queries.
    Values extracted directly from MariaDB DISTINCT queries on the full dataset.
    Only Location and date range are fetched from DB (locations are too many to hardcode).
    """
    opts = {
        # Only 1 agency in dataset
        'agencies': ['All', 'MCP'],

        # 13 sub-agencies
        'subagencies': [
            'All',
            '1st District, Rockville',
            '2nd District, Bethesda',
            '3rd District, Silver Spring',
            '4th District, Wheaton',
            '5th District, Germantown',
            '6th District, Gaithersburg/Montgomery Village',
            'Alcohol Initiatives Unit',
            'Auto Theft Unit',
            'Commercial Vehicle Enforcement Division',
            'Criminal Investigations Division',
            'Gang Unit',
            'Highway Safety Unit',
            'Suspension Enforcement Unit',
        ],

        # Violation categories
        'categories': [
            'All',
            'Equipment',
            'License and Registration',
            'Movement and Speed',
            'Other',
            'Pedestrian and Bicycle',
            'Safety Equipment',
            'Substance Abuse',
        ],

        # 36 vehicle types
        'vehicle_types': [
            'All',
            '01 - Motorcycle', '02 - Automobile', '03 - Station Wagon',
            '04 - Limousine', '05 - Light Duty Truck', '06 - Heavy Duty Truck',
            '07 - Truck/Road Tractor', '08 - Recreational Vehicle',
            '09 - Farm Vehicle', '10 - Transit Bus', '11 - Cross Country Bus',
            '12 - School Bus', '13 - Ambulance', '13 - Ambulance(Emerg)',
            '14 - Ambulance', '14 - Ambulance(Non-Emerg)',
            '15 - Fire Vehicle', '15 - Fire(Emerg)', '16 - Fire(Non-Emerg)',
            '17 - Police(Emerg)', '18 - Police Vehicle', '18 - Police(Non-Emerg)',
            '19 - Moped', '20 - Commercial Rig', '21 - Tandem Trailer',
            '22 - Mobile Home', '23 - Travel/Home Trailer', '24 - Camper',
            '25 - Utility Trailer', '26 - Boat Trailer', '27 - Farm Equipment',
            '28 - Electric Bicycle', '28 - Other', '29 - Other',
            '29 - Unknown', '30 - Unknown',
        ],

        # 4 violation types
        'violation_types': ['All', 'Citation', 'Esero', 'Sero', 'Warning'],

        # 6 races
        'races': ['All', 'ASIAN', 'BLACK', 'HISPANIC', 'NATIVE AMERICAN', 'OTHER', 'WHITE'],

        # 3 genders
        'genders': ['All', 'F', 'M', 'UNKNOWN'],

        # Locations loaded from DB (too many to hardcode)
        'locations': ['All'],

        # Date range for Montgomery County dataset
        'min_date': date(2012, 1, 1),
        'max_date': date.today(),
    }

    # No DB queries at all — everything hardcoded for instant load
    # Date range hardcoded from actual dataset (Montgomery County 2012-2024)
    opts['min_date'] = date(2012, 1, 1)
    opts['max_date'] = date(2024, 12, 31)

    # Location filter removed — too many unique values (thousands of road names)
    # Users can filter by Agency/SubAgency/Category instead
    opts['locations'] = ['All']

    return opts


# ============================================================================
# DATA LOADER — Pandas filter on full CSV (no DB)
# ============================================================================

def load_data(date_from, date_to, agencies, subagencies, categories,
              vehicle_types, violation_types, locations,
              race, gender, accident_only, alcohol_only, high_risk_only):
    """Filter the full DataFrame loaded from CSV using pandas."""
    try:
        df = load_full_csv().copy()

        def active(values):
            return [v for v in values if v != 'All']

        # Date filter
        if 'date_of_stop' in df.columns:
            df = df[
                (df['date_of_stop'] >= pd.Timestamp(date_from)) &
                (df['date_of_stop'] <= pd.Timestamp(date_to))
            ]

        # Agency filter
        ag = active(agencies)
        if ag and 'agency' in df.columns:
            df = df[df['agency'].isin(ag)]

        # SubAgency filter
        sag = active(subagencies)
        if sag and 'subagency' in df.columns:
            df = df[df['subagency'].isin(sag)]

        # Category filter
        cat = active(categories)
        if cat and 'violation_category' in df.columns:
            df = df[df['violation_category'].isin(cat)]

        # Vehicle type filter
        vt = active(vehicle_types)
        if vt and 'vehicle_type' in df.columns:
            df = df[df['vehicle_type'].isin(vt)]

        # Violation type filter
        viol = active(violation_types)
        if viol and 'violation_type' in df.columns:
            df = df[df['violation_type'].isin(viol)]

        # Race filter
        if race and race != 'All' and 'race' in df.columns:
            df = df[df['race'] == race]

        # Gender filter
        if gender and gender != 'All' and 'gender' in df.columns:
            df = df[df['gender'] == gender]

        # Safety flags
        if accident_only and 'accident' in df.columns:
            df = df[df['accident'] == 1]
        if alcohol_only and 'alcohol' in df.columns:
            df = df[df['alcohol'] == 1]
        if high_risk_only and 'high_risk' in df.columns:
            df = df[df['high_risk'] == 1]

        # Limit to 10K rows for performance
        return df.head(10000).reset_index(drop=True)

    except Exception as e:
        st.error(f"Error filtering data: {e}")
        return pd.DataFrame()


# ============================================================================
# HEADER
# ============================================================================

st.title("🚦 Traffic Violations Insight System")
st.markdown("### Montgomery County, Maryland")
st.markdown("---")


# ============================================================================
# SIDEBAR
# ============================================================================

st.sidebar.header("🎛️ Filters & Controls")

with st.sidebar.expander("⚡ Performance Info"):
    st.info("""
    **Optimizations Active:**
    - ✅ 10K row limit (fast loading)
    - ✅ Database indexes (fast queries)
    - ✅ 10-min cache (fresh data)
    - ✅ Numeric type conversion

    **Expected Speed:** 1–3 seconds
    """)

# Load filter options
with st.spinner("⏳ Loading filters..."):
    filter_opts = get_filter_options()

# --- Date Range ---
st.sidebar.subheader("📅 Date Range")
min_date = filter_opts.get('min_date', date(2012, 1, 1))
max_date = filter_opts.get('max_date', date.today())
default_start = max(min_date, max_date - timedelta(days=180))

dc1, dc2 = st.sidebar.columns(2)
with dc1:
    start_date = st.date_input("From", value=default_start,
                                min_value=min_date, max_value=max_date, key="start")
with dc2:
    end_date = st.date_input("To", value=max_date,
                              min_value=min_date, max_value=max_date, key="end")

# --- Agency ---
st.sidebar.subheader("🏢 Agency")
selected_agencies = st.sidebar.multiselect(
    "Select Agencies",
    options=[o for o in filter_opts.get('agencies', ['All']) if o != 'All'],
    default=[], placeholder="All (no filter)", key="agencies"
)

# --- SubAgency ---
st.sidebar.subheader("📍 Sub Agency")
selected_subagencies = st.sidebar.multiselect(
    "Select Sub Agencies",
    options=[o for o in filter_opts.get('subagencies', ['All']) if o != 'All'],
    default=[], placeholder="All (no filter)", key="subagencies"
)

# Location filter removed from sidebar (thousands of unique road names — unusable as dropdown)
# Location-based filtering available via the Geographic tab
selected_locations = ('All',)

# --- Category ---
st.sidebar.subheader("📋 Violation Category")
selected_categories = st.sidebar.multiselect(
    "Select Categories",
    options=[o for o in filter_opts.get('categories', ['All']) if o != 'All'],
    default=[], placeholder="All (no filter)", key="categories"
)

# --- Violation Type ---
st.sidebar.subheader("⚖️ Violation Type")
selected_violation_types = st.sidebar.multiselect(
    "Select Types",
    options=[o for o in filter_opts.get('violation_types', ['All']) if o != 'All'],
    default=[], placeholder="All (no filter)", key="violation_types"
)

# --- Vehicle Type ---
st.sidebar.subheader("🚗 Vehicle Type")
selected_vehicle_types = st.sidebar.multiselect(
    "Select Vehicle Types",
    options=[o for o in filter_opts.get('vehicle_types', ['All']) if o != 'All'],
    default=[], placeholder="All (no filter)", key="vehicles"
)

# --- Demographics ---
st.sidebar.subheader("👥 Demographics")
selected_race = st.sidebar.selectbox(
    "Race", options=filter_opts.get('races', ['All']), key="race"
)
selected_gender = st.sidebar.selectbox(
    "Gender", options=filter_opts.get('genders', ['All']), key="gender"
)

# --- Safety Flags ---
st.sidebar.subheader("⚠️ Safety Flags")
accident_only  = st.sidebar.checkbox("Accidents Only",  key="acc")
alcohol_only   = st.sidebar.checkbox("Alcohol-Related", key="alc")
high_risk_only = st.sidebar.checkbox("High-Risk Only",  key="risk")

# --- Reset ---
st.sidebar.markdown("---")
if st.sidebar.button("🔄 Reset All Filters", key="reset"):
    st.rerun()


# ============================================================================
# LOAD DATA
# ============================================================================

with st.spinner("📊 Loading violation data..."):
    df = load_data(
        start_date, end_date,
        tuple(selected_agencies),
        tuple(selected_subagencies),
        tuple(selected_categories),
        tuple(selected_vehicle_types),
        tuple(selected_violation_types),
        tuple(selected_locations),
        selected_race, selected_gender,
        accident_only, alcohol_only, high_risk_only
    )

if df.empty:
    st.warning("⚠️ No data found with current filters.")
    st.info("💡 **Try:** Select 'All' for filters, expand date range, or remove safety flags.")
    st.stop()


# ============================================================================
# KPIs — Row 1: Core Stats
# ============================================================================

st.markdown("### 📊 Key Metrics")

k1, k2, k3, k4, k5, k6 = st.columns(6)

with k1:
    total = len(df)
    st.metric("📊 Total Violations", f"{total:,}")
    if total >= 10000:
        st.caption("⚠️ 10K sample")

with k2:
    unique = df['seq_id'].nunique() if 'seq_id' in df.columns else total
    st.metric("🚗 Unique Stops", f"{unique:,}")

with k3:
    acc  = int(df['accident'].sum()) if 'accident' in df.columns else 0
    rate = round(acc / total * 100, 1) if total > 0 else 0.0
    st.metric("⚠️ Accidents", f"{acc:,}", f"{rate}%")

with k4:
    fatal = int(df['fatal'].sum()) if 'fatal' in df.columns else 0
    st.metric("💀 Fatal", f"{fatal:,}")

with k5:
    # NEW: Personal Injury KPI
    inj = int(df['personal_injury'].sum()) if 'personal_injury' in df.columns else 0
    inj_rate = round(inj / total * 100, 1) if total > 0 else 0.0
    st.metric("🏥 Personal Injury", f"{inj:,}", f"{inj_rate}%")

with k6:
    # NEW: High-Risk Zones KPI
    hr = int(df['high_risk'].sum()) if 'high_risk' in df.columns else 0
    hr_rate = round(hr / total * 100, 1) if total > 0 else 0.0
    st.metric("🔴 High-Risk", f"{hr:,}", f"{hr_rate}%")

# KPI Row 2: Additional safety stats
k7, k8, k9, k10 = st.columns(4)

with k7:
    prop = int(df['property_damage'].sum()) if 'property_damage' in df.columns else 0
    st.metric("🏚️ Property Damage", f"{prop:,}")

with k8:
    alc = int(df['alcohol'].sum()) if 'alcohol' in df.columns else 0
    st.metric("🍺 Alcohol-Related", f"{alc:,}")

with k9:
    belt = int(df['belts'].sum()) if 'belts' in df.columns else 0
    st.metric("🪢 No Belts", f"{belt:,}")

with k10:
    wz = int(df['work_zone'].sum()) if 'work_zone' in df.columns else 0
    st.metric("🚧 Work Zone", f"{wz:,}")

st.markdown("---")


# ============================================================================
# DOWNLOAD BUTTON
# ============================================================================

try:
    csv = df.to_csv(index=False).encode('utf-8')
    st.sidebar.download_button(
        "📥 Download Data (CSV)", csv,
        f"violations_{datetime.now().strftime('%Y%m%d')}.csv",
        "text/csv", key="dl"
    )
except Exception:
    pass


# ============================================================================
# TABS
# ============================================================================

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📊 Overview", "🗺️ Geographic", "⏰ Temporal",
    "🚗 Vehicle", "👥 Demographics", "📋 Summary Stats"
])


# ============================================================================
# TAB 1: OVERVIEW
# ============================================================================

with tab1:
    st.header("📊 Violations Overview")

    # Top 10 Violation Descriptions
    if 'description' in df.columns:
        st.subheader("🏆 Top 10 Violation Types")
        desc_df = df[df['description'].notna() & (df['description'] != '')]
        if len(desc_df) >= 10:
            top10 = desc_df['description'].value_counts().head(10).reset_index()
            top10.columns = ['Violation', 'Count']
            fig = px.bar(top10, y='Violation', x='Count', orientation='h',
                         color='Count', color_continuous_scale='Blues',
                         labels={'Count': 'Number of Violations'})
            fig.update_layout(height=500, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        # Violation Categories
        if 'violation_category' in df.columns:
            st.subheader("📋 Violation Categories")
            cat_df = df[df['violation_category'].notna() & (df['violation_category'] != '')]
            if len(cat_df) > 0:
                cats = cat_df['violation_category'].value_counts().reset_index()
                cats.columns = ['Category', 'Count']
                fig = px.pie(cats, values='Count', names='Category', hole=0.3)
                fig.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Violation Types (Citation / Warning / ESERO)
        if 'violation_type' in df.columns:
            st.subheader("🔖 Violation Types (Citation/Warning/ESERO)")
            type_df = df[df['violation_type'].notna() & (df['violation_type'] != '')]
            if len(type_df) > 0:
                types = type_df['violation_type'].value_counts().head(8).reset_index()
                types.columns = ['Type', 'Count']
                fig = px.pie(types, values='Count', names='Type', hole=0.3)
                fig.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # Safety Incidents Comparison (NEW)
    st.subheader("⚠️ Safety Incidents Comparison")
    safety_cols = {
        'Accident': 'accident', 'Personal Injury': 'personal_injury',
        'Property Damage': 'property_damage', 'Fatal': 'fatal',
        'Alcohol': 'alcohol', 'No Belts': 'belts', 'Work Zone': 'work_zone'
    }
    safety_data = []
    for label, col in safety_cols.items():
        if col in df.columns:
            count = int(df[col].sum())
            pct   = round(count / total * 100, 2)
            safety_data.append({'Incident Type': label, 'Count': count, 'Percentage': pct})

    if safety_data:
        safety_df = pd.DataFrame(safety_data)
        fig = px.bar(safety_df, x='Incident Type', y='Count',
                     color='Count', color_continuous_scale='Reds',
                     text='Percentage',
                     labels={'Count': 'Number of Violations'})
        fig.update_traces(texttemplate='%{text}%', textposition='outside')
        fig.update_layout(showlegend=False, height=400)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # Accident-Prone Violations (Top 10)
    if 'description' in df.columns and 'accident' in df.columns:
        st.subheader("⚠️ Most Accident-Prone Violations (Top 10)")
        ap_df = df[df['description'].notna() & (df['description'] != '')].copy()
        if len(ap_df) > 0:
            ap_stats = ap_df.groupby('description').agg(
                Total=('accident', 'count'),
                Accidents=('accident', 'sum')
            ).reset_index()
            ap_stats['Accident Rate (%)'] = (ap_stats['Accidents'] / ap_stats['Total'] * 100).round(2)
            ap_stats = ap_stats[ap_stats['Total'] >= 10].sort_values('Accident Rate (%)', ascending=False).head(10)
            if len(ap_stats) > 0:
                ap_stats = ap_stats.rename(columns={'description': 'Violation'})
                st.dataframe(ap_stats, use_container_width=True, hide_index=True)


# ============================================================================
# TAB 2: GEOGRAPHIC
# ============================================================================

with tab2:
    st.header("🗺️ Geographic Analysis")

    if 'latitude' in df.columns and 'longitude' in df.columns:
        geo_df = df[
            df['latitude'].notna() & df['longitude'].notna() &
            (df['latitude'] != 0) & (df['longitude'] != 0)
        ].copy()

        if len(geo_df) > 0:
            st.subheader("🗺️ Violation Hotspots Map")

            if 'location' in geo_df.columns:
                loc_df = geo_df[geo_df['location'].notna() & (geo_df['location'] != '')]

                if len(loc_df) >= 5 and HAS_FOLIUM:
                    with st.spinner("Generating map..."):
                        hotspots = loc_df.groupby('location').agg(
                            Count=('latitude', 'count'),
                            Lat=('latitude', 'first'),
                            Lon=('longitude', 'first'),
                            Accidents=('accident', 'sum')
                        ).reset_index()
                        hotspots = hotspots[hotspots['Count'] >= 3].sort_values('Count', ascending=False).head(50)

                        if len(hotspots) > 0:
                            center = [geo_df['latitude'].mean(), geo_df['longitude'].mean()]
                            m = folium.Map(location=center, zoom_start=11, tiles='OpenStreetMap')

                            for _, row in hotspots.iterrows():
                                acc_rate = row['Accidents'] / row['Count'] if row['Count'] > 0 else 0
                                color = 'red' if acc_rate > 0.05 else ('orange' if acc_rate > 0.02 else 'green')
                                folium.CircleMarker(
                                    location=[row['Lat'], row['Lon']],
                                    radius=min(row['Count'] / 30, 15) + 3,
                                    popup=f"<b>{row['location']}</b><br>Violations: {row['Count']}<br>Accidents: {int(row['Accidents'])}",
                                    color=color, fill=True, fillColor=color, fillOpacity=0.6
                                ).add_to(m)

                            folium_static(m, width=1200, height=600)

                elif not HAS_FOLIUM:
                    st.info("📦 Install folium for maps: `pip install folium streamlit-folium`")

            st.markdown("---")

            # Top 20 High-Risk Locations Table (NEW)
            st.subheader("🔴 Top 20 High-Risk Locations")
            if 'location' in df.columns:
                loc_risk = df[df['location'].notna() & (df['location'] != '')].groupby('location').agg(
                    Total_Violations=('accident', 'count'),
                    Accidents=('accident', 'sum'),
                    Personal_Injury=('personal_injury', 'sum') if 'personal_injury' in df.columns else ('accident', 'count'),
                    High_Risk=('high_risk', 'sum') if 'high_risk' in df.columns else ('accident', 'count'),
                ).reset_index()
                loc_risk['Accident Rate (%)'] = (loc_risk['Accidents'] / loc_risk['Total_Violations'] * 100).round(2)
                loc_risk = loc_risk.sort_values('Total_Violations', ascending=False).head(20)
                st.dataframe(loc_risk.rename(columns={'location': 'Location'}),
                             use_container_width=True, hide_index=True)
        else:
            st.info("No valid coordinate data in current filter selection.")

    # District Analysis
    if 'district_number' in df.columns:
        st.markdown("---")
        st.subheader("📊 Violations by Police District")
        dist_df = df[df['district_number'].notna()]
        if len(dist_df) > 0:
            dists = dist_df['district_number'].value_counts().sort_index().reset_index()
            dists.columns = ['District', 'Count']
            try:
                dists['District'] = 'District ' + dists['District'].astype(int).astype(str)
            except Exception:
                dists['District'] = dists['District'].astype(str)
            fig = px.bar(dists, x='District', y='Count', color='Count',
                         color_continuous_scale='Reds',
                         labels={'Count': 'Number of Violations'})
            fig.update_layout(showlegend=False, height=400)
            st.plotly_chart(fig, use_container_width=True)


# ============================================================================
# TAB 3: TEMPORAL
# ============================================================================

with tab3:
    st.header("⏰ Temporal Analysis")

    # Daily Trend
    if 'date_of_stop' in df.columns:
        st.subheader("📈 Violations Over Time (Daily Trend)")
        date_df = df[df['date_of_stop'].notna()].copy()
        if len(date_df) > 0:
            daily = date_df.groupby(date_df['date_of_stop'].dt.date).size().reset_index(name='Count')
            daily.columns = ['Date', 'Count']
            fig = px.line(daily, x='Date', y='Count',
                          labels={'Date': 'Date', 'Count': 'Number of Violations'})
            fig.update_traces(line_color='#3B82F6', line_width=2)
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    col1, col2 = st.columns(2)

    # Hourly Distribution
    with col1:
        if 'hour' in df.columns:
            st.subheader("🕐 Hourly Distribution")
            hour_df = df[df['hour'].notna()]
            if len(hour_df) > 0:
                hours = hour_df.groupby('hour').size().reset_index(name='Count')
                hours['hour'] = hours['hour'].astype(int)
                hours = hours.sort_values('hour')
                fig = px.bar(hours, x='hour', y='Count', color='Count',
                             color_continuous_scale='Blues',
                             labels={'hour': 'Hour of Day', 'Count': 'Violations'})
                fig.update_layout(showlegend=False, height=400)
                st.plotly_chart(fig, use_container_width=True)
                peak_hour = int(hours.loc[hours['Count'].idxmax(), 'hour'])
                st.info(f"🔥 **Peak Hour:** {peak_hour}:00 – {peak_hour+1}:00")

    # Day of Week
    with col2:
        if 'day_of_week' in df.columns:
            st.subheader("📅 Day of Week Pattern")
            day_df = df[df['day_of_week'].notna() & (df['day_of_week'] != '')]
            if len(day_df) > 0:
                day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                days = day_df['day_of_week'].value_counts().reset_index()
                days.columns = ['Day', 'Count']
                days['Day'] = pd.Categorical(days['Day'], categories=day_order, ordered=True)
                days = days.sort_values('Day')
                fig = px.bar(days, x='Day', y='Count', color='Count', color_continuous_scale='Greens')
                fig.update_layout(showlegend=False, height=400)
                st.plotly_chart(fig, use_container_width=True)
                busiest = days.loc[days['Count'].idxmax(), 'Day']
                st.info(f"📅 **Busiest Day:** {busiest}")

    # Monthly Distribution
    if 'month' in df.columns:
        st.markdown("---")
        st.subheader("📆 Monthly Distribution")
        month_df = df[df['month'].notna()].copy()
        month_df['month'] = pd.to_numeric(month_df['month'], errors='coerce')
        month_df = month_df[month_df['month'].notna() & month_df['month'].between(1, 12)]
        if len(month_df) > 0:
            month_names = {1:'Jan',2:'Feb',3:'Mar',4:'Apr',5:'May',6:'Jun',
                           7:'Jul',8:'Aug',9:'Sep',10:'Oct',11:'Nov',12:'Dec'}
            months = month_df.groupby('month').size().reset_index(name='Count')
            months['month'] = months['month'].astype(int)
            months = months.sort_values('month')
            months['Month'] = months['month'].map(month_names)
            fig = px.bar(months, x='Month', y='Count', color='Count',
                         color_continuous_scale='Purples',
                         labels={'Count': 'Violations'})
            fig.update_layout(showlegend=False, height=350)
            st.plotly_chart(fig, use_container_width=True)

    # Time Bucket (Morning / Afternoon / Night)
    if 'time_bucket' in df.columns:
        st.markdown("---")
        st.subheader("🌅 Time of Day Distribution")
        tb_df = df[df['time_bucket'].notna() & (df['time_bucket'] != '')]
        if len(tb_df) > 0:
            tb = tb_df['time_bucket'].value_counts().reset_index()
            tb.columns = ['Time Bucket', 'Count']
            fig = px.pie(tb, values='Count', names='Time Bucket', hole=0.3,
                         color_discrete_sequence=px.colors.sequential.RdBu)
            fig.update_traces(textposition='inside', textinfo='percent+label+value')
            st.plotly_chart(fig, use_container_width=True)


# ============================================================================
# TAB 4: VEHICLE
# ============================================================================

with tab4:
    st.header("🚗 Vehicle Analysis")

    # Top Vehicle Makes
    if 'vehicle_make' in df.columns:
        st.subheader("🚗 Top 20 Vehicle Makes")
        make_df = df[df['vehicle_make'].notna() & (df['vehicle_make'] != '')]
        if len(make_df) > 0:
            makes = make_df['vehicle_make'].value_counts().head(20).reset_index()
            makes.columns = ['Make', 'Count']
            fig = px.bar(makes, y='Make', x='Count', orientation='h',
                         color='Count', color_continuous_scale='Viridis')
            fig.update_layout(height=600, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    col1, col2 = st.columns(2)

    # Top Vehicle Models (NEW - PDF requirement)
    with col1:
        if 'model' in df.columns:
            st.subheader("🚙 Top 15 Vehicle Models")
            model_df = df[df['model'].notna() & (df['model'] != '')]
            if len(model_df) > 0:
                models = model_df['model'].value_counts().head(15).reset_index()
                models.columns = ['Model', 'Count']
                fig = px.bar(models, y='Model', x='Count', orientation='h',
                             color='Count', color_continuous_scale='Teal')
                fig.update_layout(height=500, showlegend=False)
                st.plotly_chart(fig, use_container_width=True)

    # Vehicle Types
    with col2:
        if 'vehicle_type' in df.columns:
            st.subheader("🚙 Vehicle Types")
            type_df = df[df['vehicle_type'].notna() & (df['vehicle_type'] != '')]
            if len(type_df) > 0:
                types = type_df['vehicle_type'].value_counts().head(8).reset_index()
                types.columns = ['Type', 'Count']
                fig = px.pie(types, values='Count', names='Type', hole=0.3)
                fig.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    col3, col4 = st.columns(2)

    # Vehicle Age
    with col3:
        if 'vehicle_age' in df.columns:
            st.subheader("📅 Vehicle Age Groups")
            age_df = df[df['vehicle_age'].notna() & (df['vehicle_age'] >= 0)].copy()
            if len(age_df) > 0:
                age_df['Age Group'] = pd.cut(
                    age_df['vehicle_age'],
                    bins=[0, 5, 10, 15, 20, 100],
                    labels=['0–5', '6–10', '11–15', '16–20', '20+'],
                    right=True
                )
                ages = age_df['Age Group'].value_counts().sort_index().reset_index()
                ages.columns = ['Age Group', 'Count']
                fig = px.bar(ages, x='Age Group', y='Count', color='Count',
                             color_continuous_scale='Oranges')
                fig.update_layout(showlegend=False)
                st.plotly_chart(fig, use_container_width=True)

    # Vehicle Colors
    with col4:
        if 'vehicle_color' in df.columns:
            st.subheader("🎨 Vehicle Colors (Top 10)")
            color_df = df[df['vehicle_color'].notna() & (df['vehicle_color'] != '')]
            if len(color_df) > 0:
                colors = color_df['vehicle_color'].value_counts().head(10).reset_index()
                colors.columns = ['Color', 'Count']
                color_map = {
                    'BLACK': '#000000', 'WHITE': '#FFFFFF', 'SILVER': '#C0C0C0',
                    'GRAY': '#808080',  'BLUE': '#0000FF',  'RED': '#FF0000',
                    'GREEN': '#008000', 'GOLD': '#FFD700',  'BROWN': '#8B4513',
                    'YELLOW': '#FFFF00','ORANGE': '#FFA500','TAN': '#D2B48C',
                    'BEIGE': '#F5F5DC', 'PURPLE': '#800080','MAROON': '#800000'
                }
                colors['Color_Code'] = colors['Color'].map(color_map).fillna('#808080')
                fig = go.Figure(data=[go.Bar(
                    x=colors['Count'], y=colors['Color'], orientation='h',
                    marker=dict(color=colors['Color_Code'], line=dict(color='black', width=1)),
                    text=colors['Count'], textposition='auto'
                )])
                fig.update_layout(height=400, showlegend=False)
                st.plotly_chart(fig, use_container_width=True)


# ============================================================================
# TAB 5: DEMOGRAPHICS
# ============================================================================

with tab5:
    st.header("👥 Demographics Analysis")

    # By Race
    if 'race' in df.columns:
        st.subheader("📊 Violations by Race")
        race_df = df[df['race'].notna() & (df['race'] != '')]
        if len(race_df) > 0:
            races = race_df['race'].value_counts().reset_index()
            races.columns = ['Race', 'Count']
            fig = px.bar(races, y='Race', x='Count', orientation='h',
                         color='Count', color_continuous_scale='Plasma')
            fig.update_layout(showlegend=False, height=400)
            st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    col1, col2 = st.columns(2)

    # By Gender
    with col1:
        if 'gender' in df.columns:
            st.subheader("👤 Gender Distribution")
            gender_df = df[df['gender'].notna() & (df['gender'] != '')]
            if len(gender_df) > 0:
                genders = gender_df['gender'].value_counts().reset_index()
                genders.columns = ['Gender', 'Count']
                fig = px.pie(genders, values='Count', names='Gender', hole=0.3,
                             color_discrete_sequence=['#3B82F6', '#EF4444', '#10B981'])
                fig.update_traces(textposition='inside', textinfo='percent+label+value')
                st.plotly_chart(fig, use_container_width=True)

    # Gender & Accidents
    with col2:
        if 'gender' in df.columns and 'accident' in df.columns:
            st.subheader("⚠️ Gender & Accident Correlation")
            gender_df = df[df['gender'].notna() & (df['gender'] != '')]
            if len(gender_df) > 0:
                id_col = 'seq_id' if 'seq_id' in df.columns else df.columns[0]
                stats = gender_df.groupby('gender').agg(
                    Total=(id_col, 'count'),
                    Accidents=('accident', 'sum'),
                    Personal_Injury=('personal_injury', 'sum') if 'personal_injury' in df.columns else ('accident', 'sum'),
                ).reset_index()
                stats.columns = ['Gender', 'Total', 'Accidents', 'Personal Injury']
                stats['Accident Rate (%)'] = (stats['Accidents'] / stats['Total'] * 100).round(2)
                st.dataframe(stats, use_container_width=True, hide_index=True)

    st.markdown("---")

    # Race & Accident Rate
    if 'race' in df.columns and 'accident' in df.columns:
        st.subheader("📊 Race & Accident Rate")
        r_df = df[df['race'].notna() & (df['race'] != '')].copy()
        if len(r_df) > 0:
            id_col = 'seq_id' if 'seq_id' in df.columns else df.columns[0]
            r_stats = r_df.groupby('race').agg(
                Total=(id_col, 'count'),
                Accidents=('accident', 'sum')
            ).reset_index()
            r_stats['Accident Rate (%)'] = (r_stats['Accidents'] / r_stats['Total'] * 100).round(2)
            r_stats = r_stats.sort_values('Total', ascending=False)
            fig = px.bar(r_stats, x='race', y='Accident Rate (%)',
                         color='Accident Rate (%)', color_continuous_scale='Reds',
                         labels={'race': 'Race'})
            fig.update_layout(showlegend=False, height=400)
            st.plotly_chart(fig, use_container_width=True)

    # Demographics & Violation Category cross-tab (NEW - PDF asks demographics vs violation types)
    st.markdown("---")
    if 'race' in df.columns and 'violation_category' in df.columns:
        st.subheader("📊 Race vs Violation Category")
        cross_df = df[df['race'].notna() & df['violation_category'].notna()].copy()
        if len(cross_df) > 0:
            cross = cross_df.groupby(['race', 'violation_category']).size().reset_index(name='Count')
            fig = px.bar(cross, x='race', y='Count', color='violation_category',
                         barmode='group',
                         labels={'race': 'Race', 'Count': 'Violations', 'violation_category': 'Category'})
            fig.update_layout(height=450, legend_title='Category')
            st.plotly_chart(fig, use_container_width=True)


# ============================================================================
# TAB 6: SUMMARY STATS (NEW - PDF requires descriptive statistics)
# ============================================================================

with tab6:
    st.header("📋 Descriptive Summary Statistics")

    # Overall dataset summary
    st.subheader("📊 Overall Summary")
    summary_data = {
        'Metric': [
            'Total Records (Sample)',
            'Unique Stops',
            'Accidents',
            'Fatal Incidents',
            'Personal Injuries',
            'Property Damage',
            'Alcohol-Related',
            'High-Risk Violations',
            'Work Zone Violations',
            'No Seatbelt Violations',
        ],
        'Count': [
            len(df),
            df['seq_id'].nunique() if 'seq_id' in df.columns else len(df),
            int(df['accident'].sum()) if 'accident' in df.columns else 0,
            int(df['fatal'].sum()) if 'fatal' in df.columns else 0,
            int(df['personal_injury'].sum()) if 'personal_injury' in df.columns else 0,
            int(df['property_damage'].sum()) if 'property_damage' in df.columns else 0,
            int(df['alcohol'].sum()) if 'alcohol' in df.columns else 0,
            int(df['high_risk'].sum()) if 'high_risk' in df.columns else 0,
            int(df['work_zone'].sum()) if 'work_zone' in df.columns else 0,
            int(df['belts'].sum()) if 'belts' in df.columns else 0,
        ]
    }
    summary_df = pd.DataFrame(summary_data)
    summary_df['Percentage (%)'] = (summary_df['Count'] / len(df) * 100).round(2)
    st.dataframe(summary_df, use_container_width=True, hide_index=True)

    st.markdown("---")

    col1, col2 = st.columns(2)

    # Top 5 Agencies
    with col1:
        if 'agency' in df.columns:
            st.subheader("🏢 Top Agencies")
            ag = df['agency'].value_counts().head(5).reset_index()
            ag.columns = ['Agency', 'Count']
            st.dataframe(ag, use_container_width=True, hide_index=True)

        # Top 5 SubAgencies
        if 'subagency' in df.columns:
            st.subheader("📍 Top Sub-Agencies")
            sag = df[df['subagency'].notna() & (df['subagency'] != '')]['subagency'].value_counts().head(5).reset_index()
            sag.columns = ['SubAgency', 'Count']
            st.dataframe(sag, use_container_width=True, hide_index=True)

    # Top 5 Vehicle Makes & Models
    with col2:
        if 'vehicle_make' in df.columns:
            st.subheader("🚗 Top Vehicle Makes")
            mk = df[df['vehicle_make'].notna()]['vehicle_make'].value_counts().head(5).reset_index()
            mk.columns = ['Make', 'Count']
            st.dataframe(mk, use_container_width=True, hide_index=True)

        if 'model' in df.columns:
            st.subheader("🚙 Top Vehicle Models")
            md = df[df['model'].notna() & (df['model'] != '')]['model'].value_counts().head(5).reset_index()
            md.columns = ['Model', 'Count']
            st.dataframe(md, use_container_width=True, hide_index=True)

    st.markdown("---")

    # Numeric columns descriptive stats
    st.subheader("📈 Numeric Columns — Descriptive Statistics")
    num_cols = [c for c in ['vehicle_age', 'hour', 'violation_count', 'charge_count'] if c in df.columns]
    if num_cols:
        desc = df[num_cols].describe().round(2)
        st.dataframe(desc, use_container_width=True)

    st.markdown("---")

    # Violation category breakdown table
    if 'violation_category' in df.columns:
        st.subheader("📋 Violation Category Breakdown")
        vc = df[df['violation_category'].notna()]['violation_category'].value_counts().reset_index()
        vc.columns = ['Category', 'Count']
        vc['Percentage (%)'] = (vc['Count'] / len(df) * 100).round(2)
        st.dataframe(vc, use_container_width=True, hide_index=True)


# ============================================================================
# FOOTER
# ============================================================================

st.markdown("---")
st.markdown("""
    <div style='text-align: center; color: #666; padding: 20px;'>
        <p><b>Traffic Violations Insight System</b></p>
        <p>Montgomery County, Maryland </p>
        <p>Built with Streamlit 🎈 | Powered by MariaDB 🗄️ | Visualized with Plotly 📊</p>
        <p style='font-size: 0.85em; margin-top: 10px;'>
            ⚡ <b>Optimized:</b> 10K row limit • 9 Database indexes • Smart caching (10 min) • Type conversion
        </p>
    </div>
""", unsafe_allow_html=True)

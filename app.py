import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster
from geopy.distance import geodesic
from streamlit_folium import st_folium
import numpy as np

# -----------------------
# Page Config & CSS
# -----------------------
st.set_page_config(layout="wide")

st.markdown("""
    <style>
        * { color: black !important; }

        /* Sidebar background */
        section[data-testid="stSidebar"] {
            background-color: #41AED4 !important;
        }

        /* Filters title */
        .sidebar-title h1, .sidebar-title h2, .sidebar-title h3, .sidebar-title h4 {
            font-weight: bold;
        }

        /* Facility Types label */
        .stExpander summary {
            font-size: 1.3rem !important;
            font-weight: bold !important;
        }

        /* Population Type label */
        .stRadio > label {
            font-weight: bold !important;
        }

        /* Radio buttons - keep normal */
        .stRadio div[role="radiogroup"] label {
            font-weight: normal !important;
        }

        /* Slider label */
        .stSlider > label {
            font-weight: bold !important;
        }

        /* Slider value bubble (selected number) */
        .stSlider .css-1e5imcs {
            color: red !important;
            font-weight: bold !important;
        }

        /* Slider range text (min/max) */
        .stSlider .css-14gy7wr {
            color: black !important;
            font-weight: bold !important;
        }

        /* Logo image styling */
        .yamamah-logo {
            display: block;
            margin-left: auto;
            margin-right: auto;
            width: 100%;
            max-width: 150px;
        }
    </style>
""", unsafe_allow_html=True)

# -----------------------
# Logo & Sidebar Filters
# -----------------------
with st.sidebar:
    st.image("https://i.ibb.co/HDynzq8C/yamamah-logo.png", use_container_width=True)
    st.markdown("### Filters", unsafe_allow_html=True)

    with st.expander("Select up to 3 Facility Types"):
        facility_types = ['Clinic', 'Hospital', 'PHC', 'Urgent Care']
        type_flags = {ft: st.checkbox(ft, value=False) for ft in facility_types}
        selected_types = [k for k, v in type_flags.items() if v]
        if len(selected_types) > 3:
            st.error("⚠️ Please select no more than 3 facility types.")
            selected_types = selected_types[:3]

    pop_type = st.radio("Select Population Type:", ['Population', 'Insured Population', 'Diabetic Population'])
    radius = st.slider("Coverage (meters):", 100, 3000, 500, step=100)

# -----------------------
# Hardcoded Data
# -----------------------
pop_data = pd.DataFrame([
    {"Grid_ID": "G1", "Latitude": 24.7100, "Longitude": 46.6700, "Population": 1034, "Insured Population": 1352, "Diabetic Population": 630},
    {"Grid_ID": "G2", "Latitude": 24.7125, "Longitude": 46.6625, "Population": 3672, "Insured Population": 1518, "Diabetic Population": 550},
    {"Grid_ID": "G3", "Latitude": 24.7180, "Longitude": 46.6580, "Population": 4002, "Insured Population": 1323, "Diabetic Population": 861},
    {"Grid_ID": "G4", "Latitude": 24.7200, "Longitude": 46.6650, "Population": 2420, "Insured Population": 3033, "Diabetic Population": 736},
    {"Grid_ID": "G5", "Latitude": 24.7150, "Longitude": 46.6750, "Population": 2115, "Insured Population": 2142, "Diabetic Population": 699},
    {"Grid_ID": "G6", "Latitude": 24.7235, "Longitude": 46.6780, "Population": 2490, "Insured Population": 3828, "Diabetic Population": 132},
    {"Grid_ID": "G7", "Latitude": 24.7270, "Longitude": 46.6720, "Population": 4205, "Insured Population": 3261, "Diabetic Population": 535},
])
facilities = pd.DataFrame({
    'Name': [f'Facility {i}' for i in range(1, 16)],
    'Type': ['Clinic', 'Hospital', 'PHC', 'Urgent Care', 'Clinic', 'PHC', 'Clinic', 'Hospital', 'Urgent Care', 'Clinic',
             'PHC', 'Clinic', 'Urgent Care', 'Hospital', 'PHC'],
    'Latitude': [24.7150, 24.7250, 24.7100, 24.7175, 24.7185, 24.7190, 24.7120, 24.7240, 24.7160, 24.7090,
                 24.7130, 24.7280, 24.7070, 24.7205, 24.7220],
    'Longitude': [46.6780, 46.6850, 46.6620, 46.6765, 46.6700, 46.6790, 46.6690, 46.6840, 46.6675, 46.6630,
                  46.6665, 46.6870, 46.6610, 46.6805, 46.6820]
})
filtered_facilities = facilities[facilities['Type'].isin(selected_types)]

# -----------------------
# Utility Functions
# -----------------------
def calc_min_distance(point, fac_df):
    if fac_df.empty:
        return np.nan
    return fac_df.apply(lambda f: geodesic(point, (f['Latitude'], f['Longitude'])).meters, axis=1).min()

def count_nearby_facilities(point, fac_df, r):
    if fac_df.empty:
        return 0
    return fac_df.apply(lambda f: geodesic(point, (f['Latitude'], f['Longitude'])).meters <= r, axis=1).sum()

def sum_population_in_radius(point, pop_df, pop_type, r):
    return pop_df.apply(
        lambda row: row[pop_type] if geodesic(point, (row['Latitude'], row['Longitude'])).meters <= r else 0,
        axis=1
    ).sum()

# -----------------------
# Scoring
# -----------------------
results = []
for _, row in pop_data.iterrows():
    center = (row['Latitude'], row['Longitude'])
    total_pop = sum_population_in_radius(center, pop_data, pop_type, radius)
    dist = calc_min_distance(center, filtered_facilities)
    count = count_nearby_facilities(center, filtered_facilities, radius)
    results.append((row['Grid_ID'], row['Latitude'], row['Longitude'], row[pop_type], total_pop, dist, count))

scored_df = pd.DataFrame(results, columns=['Grid_ID', 'Latitude', 'Longitude', 'Pop_Center', 'Pop_Sum', 'Min_Dist', 'Facility_Count'])

# Normalize and score
pop_max = scored_df['Pop_Sum'].max() or 1
dist_max = scored_df['Min_Dist'].max() or 1
fac_max = scored_df['Facility_Count'].max() or 1
if filtered_facilities.empty:
    scored_df['Composite_Score'] = (scored_df['Pop_Sum'] / pop_max).clip(0, 1)
else:
    scored_df['Composite_Score'] = (
        (scored_df['Pop_Sum'] / pop_max) * 0.6 +
        (scored_df['Min_Dist'] / dist_max) * 0.2 +
        ((fac_max - scored_df['Facility_Count']) / fac_max) * 0.2
    ).clip(0, 1)

# -----------------------
# Map
# -----------------------
m = folium.Map(location=[24.715, 46.675], zoom_start=13)
marker_cluster = MarkerCluster().add_to(m)

for _, row in filtered_facilities.iterrows():
    folium.Marker(
        location=[row['Latitude'], row['Longitude']],
        popup=f"{row['Name']} ({row['Type']})",
        icon=folium.Icon(color='blue')
    ).add_to(marker_cluster)

offset = 0.001
for _, row in scored_df.iterrows():
    corners = [
        [row['Latitude'] - offset, row['Longitude'] - offset],
        [row['Latitude'] - offset, row['Longitude'] + offset],
        [row['Latitude'] + offset, row['Longitude'] + offset],
        [row['Latitude'] + offset, row['Longitude'] - offset]
    ]
    folium.Polygon(
        locations=corners,
        color='crimson',
        fill=True,
        fill_opacity=0.4,
        tooltip=(
            f"<b>Grid</b>: {row['Grid_ID']}<br>"
            f"<b>Population</b>: {int(row['Pop_Center'])}<br>"
            f"<b>Population in Coverage</b>: {int(row['Pop_Sum'])}<br>"
            f"<b>Nearby Facilities</b>: {int(row['Facility_Count'])}<br>"
            f"<b>Distance to Nearest</b>: {int(row['Min_Dist']) if not np.isnan(row['Min_Dist']) else 'N/A'} m<br>"
            f"<b>Composite Score</b>: {row['Composite_Score']:.2f}"
        )
    ).add_to(m)

top3 = scored_df.sort_values('Composite_Score', ascending=False).head(3)
for _, row in top3.iterrows():
    folium.Marker(
        location=[row['Latitude'], row['Longitude']],
        popup=f"BEST LOCATION\nScore: {row['Composite_Score']:.2f}",
        icon=folium.Icon(color='red', icon='star')
    ).add_to(m)

st.subheader("Map Showing Best Locations Based on Selected Facility Types")
st_data = st_folium(m, width=2400, height=850)

# -----------------------
# Click to Score
# -----------------------
if st_data and st_data.get("last_clicked"):
    lat = st_data["last_clicked"]["lat"]
    lon = st_data["last_clicked"]["lng"]
    click_point = (lat, lon)

    pop_sum = sum_population_in_radius(click_point, pop_data, pop_type, radius)
    dist = calc_min_distance(click_point, filtered_facilities)
    count = count_nearby_facilities(click_point, filtered_facilities, radius)

    pop_score = pop_sum / pop_max if pop_max else 0
    dist_score = dist / dist_max if dist_max else 0
    fac_score = (fac_max - count) / fac_max if fac_max else 0

    final_score = pop_score if filtered_facilities.empty else pop_score * 0.6 + dist_score * 0.2 + fac_score * 0.2
    final_score = max(0, min(final_score, 1))

    st.markdown(f"""
    ### 📍 Clicked Location Summary
    - **Population in Coverage**: {int(pop_sum)}
    - **Nearby Facilities**: {int(count)}
    - **Distance to Nearest Facility**: {int(dist) if not np.isnan(dist) else 'N/A'} meters
    - **Composite Score**: **{final_score:.2f}**
    """)
m.save("best_location_map.html")

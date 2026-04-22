import streamlit as st
import os
import json
from streamlit_folium import st_folium

from scripts.food_agent import get_recommendation_with_distance
from scripts.map_generator import generate_indore_map

st.set_page_config(page_title="Indore Food AI", layout="wide")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
json_path = os.path.join(BASE_DIR, "data", "indore_vendors.json")

# ---------------- LOAD DATA ----------------
@st.cache_data
def load_data(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

vendors = load_data(json_path)

st.title("🍴 Indore Food Intelligence")

# ---------------- SIDEBAR ----------------
st.sidebar.header("Filters")

u_lat = st.sidebar.number_input("Latitude", value=22.7196)
u_lon = st.sidebar.number_input("Longitude", value=75.8577)

search = st.sidebar.text_input("Search food", "")

# ---------------- FILTER ----------------
def filter_data(vendors, search):
    if not search:
        return vendors
    return [
        v for v in vendors
        if search.lower() in v.get("name", "").lower()
        or search.lower() in v.get("specialty", "").lower()
    ]

filtered = filter_data(vendors, search)
st.sidebar.write(f"{len(filtered)} results")

# ---------------- AI SECTION ----------------
st.subheader("🤖 AI Recommendation")

query = st.text_input("What do you want to eat?")

# Button click → store results
if st.button("Get Recommendation"):
    if not query.strip():
        st.warning("Please enter something to search")
    else:
        response, top3 = get_recommendation_with_distance(
            u_lat, u_lon, query, filtered
        )

        # STORE in session
        st.session_state.response = response
        st.session_state.top_vendors = top3

# ---------------- DISPLAY STORED RESULTS ----------------
if "response" in st.session_state:
    st.success(st.session_state.response)

    st.subheader("Top Matches")

    for v in st.session_state.top_vendors:
        st.markdown(f"""
        **{v['name']}**
        - {v['specialty']}
        - {v['dist']:.2f} km
        """)

# ---------------- MAP ----------------
st.subheader("🗺️ Live Food Map")

if "top_vendors" in st.session_state:
    m = generate_indore_map(
        u_lat,
        u_lon,
        st.session_state.top_vendors
    )
    st_folium(m, width=700, height=500)
else:
    st.info("Run AI recommendation to see map")
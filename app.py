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

veg_filter = st.sidebar.selectbox(
    "Veg Preference",
    ["All", "Veg Only", "Non-Veg"]
)

price_filter = st.sidebar.selectbox(
    "Price",
    ["All", "low", "medium"]
)

# ---------------- FILTER FUNCTION ----------------
def filter_data(vendors, search, veg_filter, price_filter):
    result = vendors

    if search:
        result = [
            v for v in result
            if search.lower() in v.get("name", "").lower()
            or search.lower() in v.get("specialty", "").lower()
        ]

    if veg_filter == "Veg Only":
        result = [v for v in result if v.get("is_pure_veg")]
    elif veg_filter == "Non-Veg":
        result = [v for v in result if not v.get("is_pure_veg")]

    if price_filter != "All":
        result = [v for v in result if v.get("price_range") == price_filter]

    return result

filtered = filter_data(vendors, search, veg_filter, price_filter)
st.sidebar.write(f"{len(filtered)} results")

# ---------------- AI SECTION ----------------
st.subheader("🤖 AI Recommendation")

query = st.text_input("What do you want to eat?")

if st.button("Get Recommendation"):
    if not query.strip():
        st.warning("Please enter something")
    elif len(filtered) == 0:
        st.error("No vendors match current filters")
    else:
        response, top3 = get_recommendation_with_distance(
            u_lat, u_lon, query, filtered
        )

        st.session_state.response = response
        st.session_state.top_vendors = top3

# ---------------- DISPLAY RESULTS ----------------
if "response" in st.session_state:
    st.success(st.session_state.response)

    st.subheader("🔥 Top Recommendations")

    top_vendors = st.session_state.top_vendors

    for i, v in enumerate(top_vendors):
        with st.container():
            if i == 0:
                st.markdown("### 🏆 Best Choice")

            col1, col2 = st.columns([3, 1])

            with col1:
                st.markdown(f"**{v['name']}**")
                st.write(f"🍽 {v['specialty']}")
                st.write(f"📍 {v['location']}")

            with col2:
                st.metric("Distance", f"{v['dist']:.2f} km")

            # Tags
            tags = []
            if v.get("is_pure_veg"):
                tags.append("Veg")
            else:
                tags.append("Non-Veg")

            if v.get("price_range"):
                tags.append(v["price_range"].capitalize())

            st.caption(" | ".join(tags))

            st.divider()

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
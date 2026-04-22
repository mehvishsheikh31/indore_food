import streamlit as st
import os
import json
import streamlit.components.v1 as components
from scripts.food_agent import get_recommendation_with_distance
from scripts.map_generator import generate_indore_map

st.set_page_config(page_title="Indore Food AI", layout="wide")

# 1. Load Data
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
json_path = os.path.join(BASE_DIR, "data", "indore_vendors.json")

if os.path.exists(json_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        all_vendors = json.load(f)
else:
    all_vendors = []
    st.error("JSON file not found in data/ folder!")

st.title("🍴 Indore Street Food Intelligence")

# 2. Sidebar Search and Filters
st.sidebar.header("📍 Navigation & Search")
u_lat = st.sidebar.number_input("Your Latitude", value=22.7196, format="%.4f")
u_lon = st.sidebar.number_input("Your Longitude", value=75.8577, format="%.4f")

search_query = st.sidebar.text_input("🔍 Search for Swaad (e.g. Dahi Bada, Poha)", "")

# 3. Filtering Logic (This connects Search to the Map)
if search_query:
    display_vendors = [v for v in all_vendors if search_query.lower() in v['name'].lower() or search_query.lower() in v['specialty'].lower()]
    st.sidebar.success(f"Found {len(display_vendors)} matching spots!")
else:
    display_vendors = all_vendors

# 4. AI Recommendation Box
user_query = st.text_input("Bhiya, what's on your mind?", "Best spicy food nearby")
if st.button("Ask AI Guide"):
    with st.spinner("Finding the best swaad..."):
        response = get_recommendation_with_distance(u_lat, u_lon, user_query)
        st.markdown("### 🤖 Indori AI Says:")
        st.info(response)

# 5. Map Update (This runs on every search/filter change)
generate_indore_map(u_lat, u_lon, display_vendors)

st.subheader("Interactive Food Map")
map_path = os.path.join(BASE_DIR, "data", "indore_food_map.html")

if os.path.exists(map_path):
    with open(map_path, 'r', encoding='utf-8') as f:
        html_data = f.read()
        components.html(html_data, height=550)
else:
    st.warning("Map file is being generated...")
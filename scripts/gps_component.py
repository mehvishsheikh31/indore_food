"""
gps_component.py – GPS using streamlit-js-eval
"""
import streamlit as st
from config import DEFAULT_LAT, DEFAULT_LON

def gps_location_widget() -> tuple:
    try:
        from streamlit_js_eval import get_geolocation
    except ImportError:
        st.warning("Run: pip install streamlit-js-eval")
        c1, c2 = st.columns(2)
        lat = c1.number_input("Latitude", value=DEFAULT_LAT, format="%.4f")
        lon = c2.number_input("Longitude", value=DEFAULT_LON, format="%.4f")
        return lat, lon, False

    if "gps_lat" not in st.session_state:
        st.session_state.gps_lat = None
        st.session_state.gps_lon = None

    # get_geolocation() runs on EVERY render — only activate when user wants it
    if st.session_state.get("gps_requested"):
        loc = get_geolocation()
        if loc and "coords" in loc:
            st.session_state.gps_lat = loc["coords"]["latitude"]
            st.session_state.gps_lon = loc["coords"]["longitude"]
            st.session_state.gps_requested = False

    col_btn, col_clear = st.columns([2, 1])
    with col_btn:
        if st.button("📡 Detect My Location", use_container_width=True, type="primary"):
            st.session_state.gps_requested = True
            st.rerun()
    with col_clear:
        if st.session_state.gps_lat:
            if st.button("✖ Clear", use_container_width=True):
                st.session_state.gps_lat = None
                st.session_state.gps_lon = None
                st.rerun()

    if st.session_state.gps_lat:
        lat = st.session_state.gps_lat
        lon = st.session_state.gps_lon
        st.success(f"📡 GPS: {lat:.5f}, {lon:.5f}")
        return lat, lon, True
    else:
        if st.session_state.get("gps_requested"):
            st.info("⏳ Waiting for browser location... (allow the popup)")
        st.caption("Or enter manually:")
        c1, c2 = st.columns(2)
        lat = c1.number_input("Latitude", value=DEFAULT_LAT, format="%.4f", key="manual_lat")
        lon = c2.number_input("Longitude", value=DEFAULT_LON, format="%.4f", key="manual_lon")
        return lat, lon, False
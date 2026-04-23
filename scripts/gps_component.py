"""
gps_component.py – Browser GPS auto-detect for Streamlit

How it works:
  1. We render a small HTML snippet with a button.
  2. On click, browser's navigator.geolocation fires.
  3. The JS writes lat/lon into the Streamlit query params via URL manipulation,
     then triggers a page reload — Streamlit reads them on the next run.
"""
import streamlit as st
from config import DEFAULT_LAT, DEFAULT_LON


GPS_HTML = """
<style>
  .gps-btn {{
    display: inline-flex;
    align-items: center;
    gap: 8px;
    background: {bg};
    color: {fg};
    border: 1.5px solid {border};
    border-radius: 8px;
    padding: 8px 16px;
    font-size: 14px;
    font-weight: 600;
    cursor: pointer;
    transition: all .2s;
    width: 100%;
    justify-content: center;
  }}
  .gps-btn:hover {{ opacity: 0.85; transform: translateY(-1px); }}
  .gps-status {{
    font-size: 12px;
    margin-top: 6px;
    color: #888;
    text-align: center;
    min-height: 16px;
  }}
</style>

<button class="gps-btn" id="gpsBtn"
  onclick="detectGPS()"
  style="">
  📡 Detect My Location
</button>
<div class="gps-status" id="gpsStatus"></div>

<script>
function detectGPS() {{
  const btn = document.getElementById('gpsBtn');
  const status = document.getElementById('gpsStatus');

  if (!navigator.geolocation) {{
    status.textContent = '❌ Geolocation not supported by this browser.';
    return;
  }}

  btn.textContent = '⏳ Getting location...';
  btn.disabled = true;
  status.textContent = 'Please allow location access when prompted.';

  navigator.geolocation.getCurrentPosition(
    function(pos) {{
      const lat = pos.coords.latitude.toFixed(6);
      const lon = pos.coords.longitude.toFixed(6);
      const acc = Math.round(pos.coords.accuracy);

      status.textContent = `✅ Got it! Accuracy ~${{acc}}m. Updating...`;

      // Write to URL query params and reload so Streamlit picks them up
      const url = new URL(window.parent.location.href);
      url.searchParams.set('gps_lat', lat);
      url.searchParams.set('gps_lon', lon);
      window.parent.location.href = url.toString();
    }},
    function(err) {{
      btn.textContent = '📡 Detect My Location';
      btn.disabled = false;
      const msgs = {{
        1: '❌ Permission denied. Please allow location in browser settings.',
        2: '❌ Position unavailable. Try again.',
        3: '❌ Timed out. Try again.',
      }};
      status.textContent = msgs[err.code] || '❌ Unknown error.';
    }},
    {{
      enableHighAccuracy: true,
      timeout: 10000,
      maximumAge: 60000,
    }}
  );
}}
</script>
"""


def gps_location_widget() -> tuple[float, float, bool]:
    """
    Renders the GPS detect button in the sidebar.

    Returns:
        (latitude, longitude, gps_active)
        gps_active = True if location came from GPS (not manual input)
    """
    params = st.query_params

    gps_lat = params.get("gps_lat")
    gps_lon = params.get("gps_lon")

    gps_active = False
    lat_val = DEFAULT_LAT
    lon_val = DEFAULT_LON

    if gps_lat and gps_lon:
        try:
            lat_val = float(gps_lat)
            lon_val = float(gps_lon)
            gps_active = True
        except ValueError:
            pass

    # Render the detect button
    st.components.v1.html(GPS_HTML, height=80)

    if gps_active:
        st.success(f"📡 GPS: {lat_val:.5f}, {lon_val:.5f}")
        if st.button("✖ Clear GPS / Enter Manually", use_container_width=True):
            # Remove GPS params and reload
            params.clear()
            st.rerun()
    else:
        st.caption("Or enter manually:")
        col1, col2 = st.columns(2)
        with col1:
            lat_val = st.number_input("Latitude", value=lat_val, format="%.4f", key="manual_lat")
        with col2:
            lon_val = st.number_input("Longitude", value=lon_val, format="%.4f", key="manual_lon")

    return lat_val, lon_val, gps_active

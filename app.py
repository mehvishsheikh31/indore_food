"""
app.py – Indore Food Intelligence (v2)
Streamlit UI with AI recommendations, history, explore mode, and live map.
"""
import os
import json
import time
import streamlit as st
from streamlit_folium import st_folium
from scripts.food_agent import get_recommendation, rank_vendors
from scripts.map_generator import generate_map
from scripts.gps_component import gps_location_widget
from config import DEFAULT_LAT, DEFAULT_LON, APP_TITLE, APP_ICON


# ─────────────────────────────────────────────────────────
# Page config
# ─────────────────────────────────────────────────────────
st.set_page_config(
    page_title=APP_TITLE,
    page_icon=APP_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────
# Custom CSS
# ─────────────────────────────────────────────────────────
st.markdown("""
<style>
  /* card */
  .food-card {
    background: #fff;
    border: 1px solid #f0f0f0;
    border-radius: 12px;
    padding: 16px 20px;
    margin-bottom: 12px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    transition: transform .15s;
  }
  .food-card:hover { transform: translateY(-2px); }
  .rank-badge {
    display:inline-block;
    background:#FF6B35;color:#fff;
    border-radius:20px;padding:2px 10px;
    font-size:13px;font-weight:600;
    margin-bottom:6px;
  }
  .tag-pill {
    display:inline-block;background:#f4f4f4;
    border-radius:20px;padding:2px 9px;
    font-size:12px;margin:2px;color:#555;
  }
  .ai-box {
    background:linear-gradient(135deg,#fff8f4,#fff3ec);
    border-left: 4px solid #FF6B35;
    border-radius: 0 12px 12px 0;
    padding: 16px 20px;
    margin: 12px 0;
    font-size:15px;line-height:1.7;
  }
  /* sidebar area */
  .stSidebar { background: #fafafa; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────
# Data loading
# ─────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

@st.cache_data
def load_vendors(path: str):
    with open(path, encoding="utf-8") as f:
        return json.load(f)

vendors_all = load_vendors(os.path.join(BASE_DIR, "data", "indore_vendors.json"))

# ─────────────────────────────────────────────────────────
# Session state init
# ─────────────────────────────────────────────────────────
def _init_state():
    defaults = {
        "ai_response": None,
        "top_vendors": None,
        "history": [],          # list of {"query", "response", "top_vendors"}
        "last_query": "",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

_init_state()

# ─────────────────────────────────────────────────────────
# Sidebar – Filters & Location
# ─────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"## {APP_ICON} {APP_TITLE}")
    st.caption("Your AI-powered Indore food guide")
    st.divider()
     
    st.markdown("### 📍 Your Location")
    u_lat, u_lon, gps_active = gps_location_widget()

    st.markdown("### 🔍 Filters")
    search_text = st.text_input("Search by name / dish", placeholder="e.g. poha, biryani")

    veg_pref = st.selectbox("Veg Preference", ["All", "Veg Only", "Non-Veg"])

    price_pref = st.selectbox("Price Range", ["All", "low", "medium"])

    area_options = ["All"] + sorted({v.get("area", "") for v in vendors_all if v.get("area")})
    area_pref = st.selectbox("Area", area_options)

    show_all_on_map = st.checkbox("Show all vendors on map", value=False)

    st.divider()
    if st.button("🗑 Clear History", use_container_width=True):
        st.session_state.history = []
        st.toast("History cleared!")

# ─────────────────────────────────────────────────────────
# Filter logic
# ─────────────────────────────────────────────────────────
def apply_filters(vendors, search, veg, price, area):
    result = vendors

    if search:
        q = search.lower()
        result = [
            v for v in result
            if q in v.get("name", "").lower()
            or q in v.get("specialty", "").lower()
            or any(q in t.lower() for t in v.get("tags", []))
        ]

    if veg == "Veg Only":
        result = [v for v in result if v.get("is_pure_veg")]
    elif veg == "Non-Veg":
        result = [v for v in result if not v.get("is_pure_veg")]

    if price != "All":
        result = [v for v in result if v.get("price_range") == price]

    if area != "All":
        result = [v for v in result if v.get("area") == area]

    return result


filtered_vendors = apply_filters(vendors_all, search_text, veg_pref, price_pref, area_pref)

# Update sidebar count
with st.sidebar:
    st.caption(f"✅ **{len(filtered_vendors)}** vendors match your filters")

# ─────────────────────────────────────────────────────────
# Main area – Tabs
# ─────────────────────────────────────────────────────────
st.markdown(f"# {APP_ICON} Indore Food Intelligence")
st.caption("AI-powered street food guide for the city of food lovers")

tab_ai, tab_explore, tab_map, tab_history, tab_share = st.tabs([
    "🤖 AI Recommend", "🧭 Explore", "🗺️ Map", "📜 History", "📤 Share"
])

# ═══════════════════════════════════════════════════════
# TAB 1 – AI Recommendation
# ═══════════════════════════════════════════════════════
with tab_ai:
    st.subheader("What are you craving right now?")

    quick_picks = ["🍽 Poha", "🍬 Something Sweet", "🌶 Spicy Snack",
                   "🍗 Non-Veg", "🥤 Cold Drink", "🍱 Lunch", "🌙 Late Night"]
    cols = st.columns(len(quick_picks))
    for i, qp in enumerate(quick_picks):
        if cols[i].button(qp, use_container_width=True, key=f"qp_{i}"):
            st.session_state["_quick_query"] = qp.split(" ", 1)[1]  # strip emoji

    query = st.text_input(
        "Describe your craving:",
        value=st.session_state.get("_quick_query", ""),
        placeholder="e.g. something tangy and spicy for evening...",
        key="main_query",
    )

    col_btn, col_tip = st.columns([1, 3])
    run_btn = col_btn.button("🔍 Get Recommendation", use_container_width=True, type="primary")
    col_tip.caption("Tip: Be descriptive — mention mood, taste, time of day, area!")

    if run_btn:
        if not query.strip():
            st.warning("Please enter your craving first!")
        elif not filtered_vendors:
            st.error("No vendors match your current filters. Try relaxing them.")
        else:
            with st.spinner("Finding the best spot for you..."):
                try:
                    ai_text, top = get_recommendation(u_lat, u_lon, query, filtered_vendors)
                    st.session_state.ai_response = ai_text
                    st.session_state.top_vendors = top
                    st.session_state.last_query = query
                    # Save to history
                    st.session_state.history.insert(0, {
                        "query": query,
                        "response": ai_text,
                        "top_vendors": top,
                    })
                    if len(st.session_state.history) > 10:
                        st.session_state.history = st.session_state.history[:10]
                    # clear quick pick
                    st.session_state.pop("_quick_query", None)
                except Exception as e:
                    st.error(f"AI error: {e}")

    # ── Results ──
    if st.session_state.ai_response:
        st.markdown("### 🤖 AI Says:")
        st.markdown(
            f'<div class="ai-box">{st.session_state.ai_response}</div>',
            unsafe_allow_html=True,
        )

        st.markdown("### 🔥 Top Picks for You")
        for i, v in enumerate(st.session_state.top_vendors):
            rank_label = "🏆 Best Match" if i == 0 else f"#{i + 1}"
            veg_tag = "🟢 Veg" if v.get("is_pure_veg") else "🔴 Non-Veg"
            price_tag = v.get("price_range", "").capitalize()
            tags_html = "".join(
                f'<span class="tag-pill">{t}</span>' for t in v.get("tags", [])
            )

            with st.container():
                st.markdown(f"""
                <div class="food-card">
                  <span class="rank-badge">{rank_label}</span>
                  <h4 style="margin:4px 0">{v['name']}</h4>
                  <p style="margin:2px 0;color:#555">🍽 {v['specialty']} &nbsp;|&nbsp; 📍 {v['location']}</p>
                  <p style="margin:2px 0;color:#555">⭐ {v.get('rating','N/A')} &nbsp;|&nbsp; 📏 {v['dist']:.2f} km &nbsp;|&nbsp; 💰 {price_tag} &nbsp;|&nbsp; {veg_tag}</p>
                  {"<p style='margin:4px 0;color:#FF6B35;font-size:13px'><b>Must Try:</b> " + v.get('must_try','') + "</p>" if v.get('must_try') else ""}
                  <div style="margin-top:6px">{tags_html}</div>
                </div>
                """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════
# TAB 2 – Explore
# ═══════════════════════════════════════════════════════
with tab_explore:
    st.subheader(f"Exploring {len(filtered_vendors)} Vendors")

    # Sort controls
    sort_col, _ = st.columns([1, 2])
    sort_by = sort_col.selectbox(
        "Sort by",
        ["Rating (High→Low)", "Distance (Near→Far)", "Name (A→Z)"],
    )

    # Compute distances for sort
    display_vendors = []
    for v in filtered_vendors:
        vc = dict(v)
        lat2, lon2 = vc["coordinates"]
        dist = ((lat2 - u_lat)**2 + (lon2 - u_lon)**2) ** 0.5 * 111  # approx km
        vc["dist"] = round(dist, 2)
        display_vendors.append(vc)

    if sort_by == "Rating (High→Low)":
        display_vendors.sort(key=lambda x: x.get("rating", 0), reverse=True)
    elif sort_by == "Distance (Near→Far)":
        display_vendors.sort(key=lambda x: x["dist"])
    else:
        display_vendors.sort(key=lambda x: x["name"])

    # 3-column card grid
    cols = st.columns(3)
    for idx, v in enumerate(display_vendors):
        with cols[idx % 3]:
            veg_tag = "🟢" if v.get("is_pure_veg") else "🔴"
            famous = "⭐ Famous" if v.get("is_famous") else ""
            tags_str = " · ".join(v.get("tags", [])[:3])
            st.markdown(f"""
            <div class="food-card">
              <b>{veg_tag} {v['name']}</b> {famous}<br>
              <span style="color:#FF6B35">{v['specialty']}</span><br>
              <span style="font-size:12px;color:#777">📍 {v['location']} &nbsp; ⭐{v.get('rating','N/A')} &nbsp; 💰{v.get('price_range','').capitalize()} &nbsp; ~{v['dist']:.1f}km</span><br>
              <span style="font-size:11px;color:#aaa">{tags_str}</span>
            </div>
            """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════
# TAB 3 – Map
# ═══════════════════════════════════════════════════════
with tab_map:
    if st.session_state.top_vendors:
        st.subheader(f"Map — Top picks for: *{st.session_state.last_query}*")
        m = generate_map(
            u_lat, u_lon,
            st.session_state.top_vendors,
            show_all=show_all_on_map,
            all_vendors=filtered_vendors,
        )
        st_folium(m, width="100%", height=520, returned_objects=[])
        st.caption("🟢 Best match · 🟠 #2 · 🔵 #3 · 🔵 You · Dashed line = route to top pick")
    else:
        # Show a default map with all filtered vendors
        st.info("Run an AI recommendation to see ranked results. Showing all filtered vendors below.")
        from scripts.food_agent import haversine
        preview = []
        for v in filtered_vendors[:15]:
            vc = dict(v)
            lat2, lon2 = vc["coordinates"]
            vc["dist"] = round(haversine(u_lat, u_lon, lat2, lon2), 2)
            preview.append(vc)
        m = generate_map(u_lat, u_lon, preview[:5], show_all=show_all_on_map, all_vendors=preview)
        st_folium(m, width="100%", height=520, returned_objects=[])

# ═══════════════════════════════════════════════════════
# TAB 4 – History
# ═══════════════════════════════════════════════════════
with tab_history:
    st.subheader("Your Recent Searches")
    if not st.session_state.history:
        st.info("No searches yet. Ask the AI for a recommendation!")
    else:
        for i, item in enumerate(st.session_state.history):
            with st.expander(f"🔍 **{item['query']}**", expanded=(i == 0)):
                st.markdown(
                    f'<div class="ai-box">{item["response"]}</div>',
                    unsafe_allow_html=True,
                )
                if item.get("top_vendors"):
                    best = item["top_vendors"][0]
                    st.caption(
                        f"Top pick: **{best['name']}** — {best['specialty']} "
                        f"({best['dist']:.2f} km) ⭐ {best.get('rating', 'N/A')}"
                    )
                    # Re-run button
                    if st.button("Use this search again", key=f"rerun_{i}"):
                        st.session_state["_quick_query"] = item["query"]
                        st.rerun()

# ═══════════════════════════════════════════════════════
# TAB 5 – Share / Export
# ═══════════════════════════════════════════════════════
with tab_share:
    st.subheader("📤 Share Your Food Picks")

    if not st.session_state.top_vendors:
        st.info("Run an AI recommendation first, then come here to share your picks!")
    else:
        query = st.session_state.last_query

        # ── Build shareable text ──
        lines = [f"🍴 Indore Food Picks — \"{query}\"", ""]
        for i, v in enumerate(st.session_state.top_vendors):
            rank = "🏆" if i == 0 else f"#{i+1}"
            veg  = "🟢 Veg" if v.get("is_pure_veg") else "🔴 Non-Veg"
            lines.append(f"{rank} {v['name']}")
            lines.append(f"   📍 {v['location']}  |  🍽 {v['specialty']}")
            lines.append(f"   ⭐ {v.get('rating','N/A')}  |  📏 {v['dist']:.2f} km  |  {veg}")
            if v.get("must_try"):
                lines.append(f"   ✨ Must try: {v['must_try']}")
            lines.append("")

        lines.append("— via Indore Food Intelligence 🍴")
        share_text = "\n".join(lines)

        # ── Preview ──
        st.markdown("**Preview:**")
        st.code(share_text, language=None)

        # ── Copy button (downloads as .txt since Streamlit has no clipboard API) ──
        st.download_button(
            label="⬇️ Download as .txt",
            data=share_text,
            file_name=f"indore_food_{query[:20].replace(' ','_')}.txt",
            mime="text/plain",
            use_container_width=True,
        )

        # ── WhatsApp share link ──
        import urllib.parse
        wa_text = urllib.parse.quote(share_text)
        wa_url  = f"https://wa.me/?text={wa_text}"
        st.markdown(
            f'<a href="{wa_url}" target="_blank">'
            f'<button style="background:#25D366;color:white;border:none;'
            f'padding:10px 20px;border-radius:8px;font-size:15px;cursor:pointer;width:100%">'
            f'💬 Share on WhatsApp</button></a>',
            unsafe_allow_html=True,
        )

        st.divider()

        # ── Export all filtered vendors as CSV ──
        st.markdown("**Export full vendor list (filtered) as CSV:**")
        import csv, io
        buf = io.StringIO()
        fields = ["name", "location", "specialty", "rating", "price_range",
                  "is_pure_veg", "is_famous", "area", "dist"]
        writer = csv.DictWriter(buf, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()

        # Re-compute dist for filtered vendors
        from scripts.food_agent import haversine
        for v in filtered_vendors:
            vc = dict(v)
            lat2, lon2 = vc["coordinates"]
            vc["dist"] = round(haversine(u_lat, u_lon, lat2, lon2), 2)
            writer.writerow(vc)

        st.download_button(
            label="⬇️ Download vendors as CSV",
            data=buf.getvalue(),
            file_name="indore_vendors_filtered.csv",
            mime="text/csv",
            use_container_width=True,
        )
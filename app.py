"""
app.py – Indore Food Intelligence (v3)
Improved UI with better design, rating filter, fixed haversine, top_n control,
enhanced cards, stats dashboard, and smoother UX.
"""
import os
import json
import time
import urllib.parse
import csv
import io
import streamlit as st
from streamlit_folium import st_folium
from scripts.food_agent import get_recommendation, rank_vendors, haversine
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
# Custom CSS – Redesigned
# ─────────────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:ital,wght@0,300;0,400;0,500;1,400&display=swap');

  html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
  }

  /* ── Hero header ── */
  .hero-header {
    background: linear-gradient(135deg, #1a0a00 0%, #2d1200 40%, #1a0800 100%);
    border-radius: 20px;
    padding: 36px 40px;
    margin-bottom: 28px;
    position: relative;
    overflow: hidden;
    border: 1px solid rgba(255,107,53,0.2);
  }
  .hero-header::before {
    content: '';
    position: absolute;
    top: -60px; right: -60px;
    width: 220px; height: 220px;
    background: radial-gradient(circle, rgba(255,107,53,0.18) 0%, transparent 70%);
    border-radius: 50%;
  }
  .hero-header::after {
    content: '';
    position: absolute;
    bottom: -40px; left: 30%;
    width: 160px; height: 160px;
    background: radial-gradient(circle, rgba(255,180,50,0.10) 0%, transparent 70%);
    border-radius: 50%;
  }
  .hero-title {
    font-family: 'Syne', sans-serif;
    font-size: 2.4rem;
    font-weight: 800;
    color: #fff;
    margin: 0 0 6px 0;
    letter-spacing: -0.5px;
  }
  .hero-sub {
    color: rgba(255,255,255,0.55);
    font-size: 1rem;
    margin: 0;
    font-weight: 300;
  }
  .hero-accent {
    color: #FF6B35;
  }

  /* ── Stat cards ── */
  .stat-row {
    display: flex;
    gap: 12px;
    margin-bottom: 24px;
    flex-wrap: wrap;
  }
  .stat-card {
    flex: 1;
    min-width: 100px;
    background: #fff;
    border: 1px solid #f0ece8;
    border-radius: 14px;
    padding: 14px 18px;
    text-align: center;
    box-shadow: 0 2px 12px rgba(0,0,0,0.04);
  }
  .stat-num {
    font-family: 'Syne', sans-serif;
    font-size: 1.7rem;
    font-weight: 700;
    color: #FF6B35;
    line-height: 1;
  }
  .stat-label {
    font-size: 11px;
    color: #999;
    margin-top: 4px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  /* ── Food vendor card ── */
  .food-card {
    background: #fff;
    border: 1px solid #f0ece8;
    border-radius: 16px;
    padding: 18px 22px;
    margin-bottom: 14px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.05);
    transition: transform .18s ease, box-shadow .18s ease;
    position: relative;
    overflow: hidden;
  }
  .food-card:hover {
    transform: translateY(-3px);
    box-shadow: 0 8px 28px rgba(255,107,53,0.12);
  }
  .food-card::before {
    content: '';
    position: absolute;
    left: 0; top: 0; bottom: 0;
    width: 4px;
    background: #FF6B35;
    border-radius: 16px 0 0 16px;
  }
  .food-card.gold::before { background: linear-gradient(180deg, #FFB800, #FF6B35); }
  .food-card.silver::before { background: #94a3b8; }
  .food-card.bronze::before { background: #c97c4a; }

  .rank-badge {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    background: #FF6B35;
    color: #fff;
    border-radius: 20px;
    padding: 3px 12px;
    font-size: 12px;
    font-weight: 600;
    margin-bottom: 8px;
    font-family: 'Syne', sans-serif;
  }
  .rank-badge.gold { background: linear-gradient(90deg, #FFB800, #FF6B35); }

  .vendor-name {
    font-family: 'Syne', sans-serif;
    font-size: 1.15rem;
    font-weight: 700;
    color: #1a0a00;
    margin: 2px 0 6px 0;
  }
  .vendor-meta {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    font-size: 13px;
    color: #666;
    margin: 4px 0;
  }
  .vendor-meta span { display: flex; align-items: center; gap: 3px; }

  .tag-pill {
    display: inline-block;
    background: #fff5f0;
    border: 1px solid #ffe0d0;
    border-radius: 20px;
    padding: 2px 10px;
    font-size: 11px;
    color: #FF6B35;
    margin: 2px;
    font-weight: 500;
  }
  .must-try-badge {
    display: inline-block;
    background: linear-gradient(90deg, #fff8f0, #fff3e8);
    border-left: 3px solid #FF6B35;
    border-radius: 0 8px 8px 0;
    padding: 5px 12px;
    font-size: 12.5px;
    color: #b34000;
    margin-top: 8px;
    font-weight: 500;
  }

  /* ── AI response box ── */
  .ai-box {
    background: linear-gradient(135deg, #1a0a00, #2d1500);
    border: 1px solid rgba(255,107,53,0.25);
    border-radius: 16px;
    padding: 20px 24px;
    margin: 14px 0 20px 0;
    font-size: 15px;
    line-height: 1.75;
    color: #f5e6d8;
    position: relative;
  }
  .ai-box::before {
    content: '"';
    position: absolute;
    top: -8px; left: 16px;
    font-size: 60px;
    color: rgba(255,107,53,0.2);
    font-family: Georgia, serif;
    line-height: 1;
  }

  /* ── Quick pick buttons ── */
  .stButton > button {
    border-radius: 10px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 500 !important;
  }

  /* ── Section heading ── */
  .section-heading {
    font-family: 'Syne', sans-serif;
    font-size: 1.1rem;
    font-weight: 700;
    color: #1a0a00;
    margin: 20px 0 12px 0;
    display: flex;
    align-items: center;
    gap: 8px;
  }

  /* ── Explore grid card ── */
  .explore-card {
    background: #fff;
    border: 1px solid #f0ece8;
    border-radius: 14px;
    padding: 14px 16px;
    margin-bottom: 12px;
    transition: transform .15s, box-shadow .15s;
    cursor: default;
  }
  .explore-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(255,107,53,0.10);
  }
  .explore-name {
    font-family: 'Syne', sans-serif;
    font-weight: 700;
    font-size: 14px;
    color: #1a0a00;
  }
  .explore-specialty {
    color: #FF6B35;
    font-size: 12.5px;
    font-weight: 500;
  }
  .explore-meta {
    font-size: 11.5px;
    color: #888;
    margin-top: 4px;
  }
  .famous-badge {
    display: inline-block;
    background: #FFB800;
    color: #fff;
    border-radius: 6px;
    padding: 1px 7px;
    font-size: 10px;
    font-weight: 700;
    margin-left: 4px;
    vertical-align: middle;
  }

  /* ── Divider ── */
  hr { border-color: #f0ece8 !important; }

  /* ── Sidebar ── */
  section[data-testid="stSidebar"] {
    background: #fdfaf8 !important;
  }
  section[data-testid="stSidebar"] .stMarkdown h2,
  section[data-testid="stSidebar"] .stMarkdown h3 {
    font-family: 'Syne', sans-serif !important;
  }

  /* ── History ── */
  .history-item {
    background: #fff;
    border: 1px solid #f0ece8;
    border-radius: 14px;
    padding: 14px 18px;
    margin-bottom: 10px;
  }
  .history-query {
    font-family: 'Syne', sans-serif;
    font-weight: 700;
    font-size: 15px;
    color: #1a0a00;
  }

  /* ── Empty state ── */
  .empty-state {
    text-align: center;
    padding: 48px 24px;
    color: #bbb;
  }
  .empty-state .icon { font-size: 2.8rem; margin-bottom: 12px; }
  .empty-state p { font-size: 15px; margin: 4px 0; }

  /* ── Metric inline ── */
  .inline-metric {
    font-size: 12px;
    background: #fff5f0;
    border-radius: 8px;
    padding: 2px 8px;
    color: #FF6B35;
    font-weight: 600;
  }
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
        "history": [],
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
    st.markdown("## 🍴 Indore Food")
    st.caption("AI-powered street food guide")
    st.divider()

    st.markdown("### 📍 Your Location")
    u_lat, u_lon, gps_active = gps_location_widget()

    st.markdown("### 🔍 Filters")
    search_text = st.text_input("Search by name / dish", placeholder="e.g. poha, biryani")
    veg_pref    = st.selectbox("Veg Preference", ["All", "Veg Only", "Non-Veg"])
    price_pref  = st.selectbox("Price Range", ["All", "low", "medium"])

    area_options = ["All"] + sorted({v.get("area", "") for v in vendors_all if v.get("area")})
    area_pref    = st.selectbox("Area", area_options)

    min_rating = st.slider("Min Rating ⭐", 0.0, 5.0, 0.0, step=0.5)
    top_n      = st.slider("Results to show", 3, 10, 5)

    show_all_on_map = st.checkbox("Show all vendors on map", value=False)

    st.divider()
    col_clear, col_info = st.columns([3, 1])
    with col_clear:
        if st.button("🗑 Clear History", use_container_width=True):
            st.session_state.history = []
            st.toast("History cleared!")

# ─────────────────────────────────────────────────────────
# Filter logic
# ─────────────────────────────────────────────────────────
def apply_filters(vendors, search, veg, price, area, min_rat):
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

    if min_rat > 0:
        result = [v for v in result if v.get("rating", 0) >= min_rat]

    return result


filtered_vendors = apply_filters(
    vendors_all, search_text, veg_pref, price_pref, area_pref, min_rating
)

with st.sidebar:
    st.caption(f"✅ **{len(filtered_vendors)}** of **{len(vendors_all)}** vendors match")

# ─────────────────────────────────────────────────────────
# Helper: vendor card HTML
# ─────────────────────────────────────────────────────────
def render_vendor_card(v: dict, rank: int):
    rank_class = ["gold", "silver", "bronze"][rank] if rank < 3 else ""
    rank_labels = ["🏆 Best Match", "#2 Pick", "#3 Pick"]
    rank_label  = rank_labels[rank] if rank < 3 else f"#{rank + 1}"
    badge_class = "gold" if rank == 0 else ""

    veg_tag   = "🟢 Veg" if v.get("is_pure_veg") else "🔴 Non-Veg"
    price_tag = v.get("price_range", "").capitalize()
    tags_html = "".join(f'<span class="tag-pill">{t}</span>' for t in v.get("tags", []))
    must_try  = f'<div class="must-try-badge">✨ Must try: {v["must_try"]}</div>' if v.get("must_try") else ""
    cash_note = '<span style="font-size:11px;color:#e67e22;font-weight:500">💵 Cash only</span>' if v.get("cash_only") else ""
    open_hr   = f'<span>🕐 {v["open_hours"]}</span>' if v.get("open_hours") else ""
    seating   = '<span>🪑 Seating</span>' if v.get("seating") else '<span>🧍 Standing</span>'

    st.markdown(f"""
    <div class="food-card {rank_class}">
      <span class="rank-badge {badge_class}">{rank_label}</span>
      <div class="vendor-name">{v['name']}</div>
      <div class="vendor-meta">
        <span>🍽 {v['specialty']}</span>
        <span>📍 {v['location']}</span>
      </div>
      <div class="vendor-meta">
        <span>⭐ {v.get('rating','N/A')}</span>
        <span>📏 {v['dist']:.2f} km</span>
        <span>💰 {price_tag}</span>
        <span>{veg_tag}</span>
        {cash_note}
        {seating}
        {open_hr}
      </div>
      {must_try}
      <div style="margin-top: 8px">{tags_html}</div>
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────
# Hero Header
# ─────────────────────────────────────────────────────────
# Compute some quick stats for the hero
total_veg    = sum(1 for v in vendors_all if v.get("is_pure_veg"))
total_famous = sum(1 for v in vendors_all if v.get("is_famous"))
areas_count  = len({v.get("area") for v in vendors_all if v.get("area")})

st.markdown(f"""
<div class="hero-header">
  <div class="hero-title">🍴 Indore <span class="hero-accent">Food</span> Intelligence</div>
  <p class="hero-sub">AI-powered street food guide for the city of food lovers</p>
</div>
""", unsafe_allow_html=True)

# Stats row
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(f'<div class="stat-card"><div class="stat-num">{len(vendors_all)}</div><div class="stat-label">Vendors</div></div>', unsafe_allow_html=True)
with c2:
    st.markdown(f'<div class="stat-card"><div class="stat-num">{total_famous}</div><div class="stat-label">Famous Spots</div></div>', unsafe_allow_html=True)
with c3:
    st.markdown(f'<div class="stat-card"><div class="stat-num">{areas_count}</div><div class="stat-label">Areas</div></div>', unsafe_allow_html=True)
with c4:
    st.markdown(f'<div class="stat-card"><div class="stat-num">{len(filtered_vendors)}</div><div class="stat-label">Matching Now</div></div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────
# Tabs
# ─────────────────────────────────────────────────────────
tab_ai, tab_explore, tab_map, tab_history, tab_share = st.tabs([
    "🤖 AI Recommend", "🧭 Explore", "🗺️ Map", "📜 History", "📤 Share"
])

# ═══════════════════════════════════════════════════════
# TAB 1 – AI Recommendation
# ═══════════════════════════════════════════════════════
with tab_ai:
    st.markdown('<div class="section-heading">💬 What are you craving right now?</div>', unsafe_allow_html=True)

    # Quick picks
    quick_picks = [
        ("🍽", "Poha"), ("🍬", "Sweet"), ("🌶", "Spicy"), ("🍗", "Non-Veg"),
        ("🥤", "Cold Drink"), ("🍱", "Lunch"), ("🌙", "Late Night"), ("🧆", "Snack"),
    ]
    cols = st.columns(len(quick_picks))
    for i, (em, label) in enumerate(quick_picks):
        if cols[i].button(f"{em} {label}", use_container_width=True, key=f"qp_{i}"):
            st.session_state["_quick_query"] = label

    query = st.text_input(
        "Describe your craving:",
        value=st.session_state.get("_quick_query", ""),
        placeholder="e.g. something tangy and spicy for evening near Sarafa...",
        key="main_query",
    )

    col_btn, col_tip = st.columns([1, 3])
    run_btn = col_btn.button("🔍 Find My Food", use_container_width=True, type="primary")
    col_tip.caption(f"💡 Tip: Mention mood, taste, time, or area · Showing top **{top_n}** results")

    if run_btn:
        if not query.strip():
            st.warning("Please enter your craving first!")
        elif not filtered_vendors:
            st.error("No vendors match your filters. Try relaxing them in the sidebar.")
        else:
            with st.spinner("Hunting down the perfect spot for you... 🔍"):
                try:
                    ai_text, top = get_recommendation(u_lat, u_lon, query, filtered_vendors)
                    # Limit to user-selected top_n
                    top = top[:top_n]
                    st.session_state.ai_response = ai_text
                    st.session_state.top_vendors  = top
                    st.session_state.last_query   = query
                    st.session_state.history.insert(0, {
                        "query": query,
                        "response": ai_text,
                        "top_vendors": top,
                    })
                    if len(st.session_state.history) > 20:
                        st.session_state.history = st.session_state.history[:20]
                    st.session_state.pop("_quick_query", None)
                except Exception as e:
                    st.error(f"AI error: {e}")

    # ── Results ──
    if st.session_state.ai_response:
        st.markdown('<div class="section-heading">🤖 AI Says</div>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="ai-box">{st.session_state.ai_response}</div>',
            unsafe_allow_html=True,
        )

        st.markdown('<div class="section-heading">🔥 Top Picks for You</div>', unsafe_allow_html=True)
        for i, v in enumerate(st.session_state.top_vendors):
            render_vendor_card(v, i)
    else:
        st.markdown("""
        <div class="empty-state">
          <div class="icon">🍽</div>
          <p><b>Tell me what you're craving</b></p>
          <p>Use the quick picks above or describe your mood — I'll find the perfect spot!</p>
        </div>
        """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════
# TAB 2 – Explore
# ═══════════════════════════════════════════════════════
with tab_explore:
    st.markdown(
        f'<div class="section-heading">🧭 Exploring <span class="inline-metric">{len(filtered_vendors)} vendors</span></div>',
        unsafe_allow_html=True,
    )

    # Sort + view controls
    col_sort, col_view, _ = st.columns([1.5, 1, 2])
    sort_by = col_sort.selectbox(
        "Sort by",
        ["Rating (High→Low)", "Distance (Near→Far)", "Name (A→Z)", "Price (Low→High)"],
        label_visibility="collapsed",
    )

    # Compute distances using haversine (consistent with AI tab)
    display_vendors = []
    for v in filtered_vendors:
        vc = dict(v)
        lat2, lon2 = vc["coordinates"]
        vc["dist"] = round(haversine(u_lat, u_lon, lat2, lon2), 2)
        display_vendors.append(vc)

    if sort_by == "Rating (High→Low)":
        display_vendors.sort(key=lambda x: x.get("rating", 0), reverse=True)
    elif sort_by == "Distance (Near→Far)":
        display_vendors.sort(key=lambda x: x["dist"])
    elif sort_by == "Name (A→Z)":
        display_vendors.sort(key=lambda x: x["name"])
    elif sort_by == "Price (Low→High)":
        order = {"low": 0, "medium": 1, "high": 2}
        display_vendors.sort(key=lambda x: order.get(x.get("price_range", ""), 99))

    # 3-column card grid
    cols = st.columns(3)
    for idx, v in enumerate(display_vendors):
        with cols[idx % 3]:
            veg_tag  = "🟢" if v.get("is_pure_veg") else "🔴"
            famous   = '<span class="famous-badge">FAMOUS</span>' if v.get("is_famous") else ""
            tags_str = " · ".join(v.get("tags", [])[:3])
            must     = f'<div style="font-size:11px;color:#FF6B35;margin-top:4px">✨ {v["must_try"]}</div>' if v.get("must_try") else ""
            hours    = f'<span style="color:#888">🕐 {v["open_hours"]}</span>' if v.get("open_hours") else ""
            cash     = '<span style="color:#e67e22">💵 Cash</span>' if v.get("cash_only") else ""
            st.markdown(f"""
            <div class="explore-card">
              <div class="explore-name">{veg_tag} {v['name']} {famous}</div>
              <div class="explore-specialty">{v['specialty']}</div>
              <div class="explore-meta">
                📍 {v['location']} &nbsp; ⭐ {v.get('rating','N/A')} &nbsp; ~{v['dist']:.1f} km &nbsp; 💰 {v.get('price_range','').capitalize()}
              </div>
              <div class="explore-meta" style="margin-top:3px">{hours} {cash}</div>
              {must}
              <div style="margin-top:5px;font-size:11px;color:#bbb">{tags_str}</div>
            </div>
            """, unsafe_allow_html=True)

    if not display_vendors:
        st.markdown("""
        <div class="empty-state">
          <div class="icon">🔍</div>
          <p><b>No vendors match your filters</b></p>
          <p>Try adjusting the filters in the sidebar</p>
        </div>
        """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════
# TAB 3 – Map
# ═══════════════════════════════════════════════════════
with tab_map:
    if st.session_state.top_vendors:
        st.markdown(
            f'<div class="section-heading">🗺️ Map for: <em style="color:#FF6B35">{st.session_state.last_query}</em></div>',
            unsafe_allow_html=True,
        )
        m = generate_map(
            u_lat, u_lon,
            st.session_state.top_vendors,
            show_all=show_all_on_map,
            all_vendors=filtered_vendors,
        )
        st_folium(m, width="100%", height=540, returned_objects=[])
        st.caption("🟢 Best match · 🟠 #2 · 🔵 #3 · 🔵 You · Dashed line = route to top pick")
    else:
        st.info("Run an AI recommendation to see ranked results on the map. Showing filtered vendors below.")
        preview = []
        for v in filtered_vendors[:15]:
            vc = dict(v)
            lat2, lon2 = vc["coordinates"]
            vc["dist"] = round(haversine(u_lat, u_lon, lat2, lon2), 2)
            preview.append(vc)
        m = generate_map(u_lat, u_lon, preview[:5], show_all=show_all_on_map, all_vendors=preview)
        st_folium(m, width="100%", height=540, returned_objects=[])

# ═══════════════════════════════════════════════════════
# TAB 4 – History
# ═══════════════════════════════════════════════════════
with tab_history:
    st.markdown('<div class="section-heading">📜 Recent Searches</div>', unsafe_allow_html=True)

    if not st.session_state.history:
        st.markdown("""
        <div class="empty-state">
          <div class="icon">📭</div>
          <p><b>No searches yet</b></p>
          <p>Ask the AI for a recommendation to see your history here</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        for i, item in enumerate(st.session_state.history):
            with st.expander(f"🔍 {item['query']}", expanded=(i == 0)):
                st.markdown(
                    f'<div class="ai-box" style="padding:14px 18px;font-size:14px">{item["response"]}</div>',
                    unsafe_allow_html=True,
                )
                if item.get("top_vendors"):
                    best = item["top_vendors"][0]
                    col_info, col_btn = st.columns([3, 1])
                    col_info.caption(
                        f"Top pick: **{best['name']}** — {best['specialty']} "
                        f"({best.get('dist', 0):.2f} km) ⭐ {best.get('rating', 'N/A')}"
                    )
                    if col_btn.button("🔁 Re-run", key=f"rerun_{i}", use_container_width=True):
                        st.session_state["_quick_query"] = item["query"]
                        st.rerun()

# ═══════════════════════════════════════════════════════
# TAB 5 – Share / Export
# ═══════════════════════════════════════════════════════
with tab_share:
    st.markdown('<div class="section-heading">📤 Share Your Food Picks</div>', unsafe_allow_html=True)

    if not st.session_state.top_vendors:
        st.markdown("""
        <div class="empty-state">
          <div class="icon">📤</div>
          <p><b>Nothing to share yet</b></p>
          <p>Run an AI recommendation first, then come back to share!</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        q = st.session_state.last_query

        # Build shareable text
        lines = [f'🍴 Indore Food Picks — "{q}"', ""]
        for i, v in enumerate(st.session_state.top_vendors):
            rank = "🏆" if i == 0 else f"#{i+1}"
            veg  = "🟢 Veg" if v.get("is_pure_veg") else "🔴 Non-Veg"
            lines.append(f"{rank} {v['name']}")
            lines.append(f"   📍 {v['location']}  |  🍽 {v['specialty']}")
            lines.append(f"   ⭐ {v.get('rating','N/A')}  |  📏 {v.get('dist',0):.2f} km  |  {veg}")
            if v.get("must_try"):
                lines.append(f"   ✨ Must try: {v['must_try']}")
            lines.append("")
        lines.append("— via Indore Food Intelligence 🍴")
        share_text = "\n".join(lines)

        col_prev, col_actions = st.columns([3, 2])

        with col_prev:
            st.markdown("**📋 Preview**")
            st.code(share_text, language=None)

        with col_actions:
            st.markdown("**⬇️ Download**")
            st.download_button(
                label="📄 Download as .txt",
                data=share_text,
                file_name=f"indore_food_{q[:20].replace(' ','_')}.txt",
                mime="text/plain",
                use_container_width=True,
            )

            # WhatsApp share
            wa_text = urllib.parse.quote(share_text)
            wa_url  = f"https://wa.me/?text={wa_text}"
            st.markdown(
                f'<a href="{wa_url}" target="_blank">'
                f'<button style="background:#25D366;color:white;border:none;'
                f'padding:10px 20px;border-radius:10px;font-size:14px;cursor:pointer;'
                f'width:100%;margin-top:4px;font-family:DM Sans,sans-serif;font-weight:500">'
                f'💬 Share on WhatsApp</button></a>',
                unsafe_allow_html=True,
            )

            st.markdown("---")
            st.markdown("**📊 Export CSV**")

            buf = io.StringIO()
            fields = ["name", "location", "specialty", "rating", "price_range",
                      "is_pure_veg", "is_famous", "area", "open_hours", "cash_only", "dist"]
            writer = csv.DictWriter(buf, fieldnames=fields, extrasaction="ignore")
            writer.writeheader()
            for v in filtered_vendors:
                vc = dict(v)
                lat2, lon2 = vc["coordinates"]
                vc["dist"] = round(haversine(u_lat, u_lon, lat2, lon2), 2)
                writer.writerow(vc)

            st.download_button(
                label="⬇️ Download vendors CSV",
                data=buf.getvalue(),
                file_name="indore_vendors_filtered.csv",
                mime="text/csv",
                use_container_width=True,
            )
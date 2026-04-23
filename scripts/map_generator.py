"""
map_generator.py – Folium map with rich popups and color coding
"""
import folium
from folium.plugins import MarkerCluster
from typing import List, Dict


RANK_COLORS = ["green", "orange", "blue", "purple", "red"]
RANK_ICONS  = ["star", "cutlery", "info-sign", "map-marker", "map-marker"]


def _vendor_popup(v: Dict, rank: int) -> str:
    veg_badge = "🟢 Veg" if v.get("is_pure_veg") else "🔴 Non-Veg"
    price = v.get("price_range", "").capitalize()
    rating = v.get("rating", "N/A")
    dist = v.get("dist", 0)
    must_try = v.get("must_try", "")
    tags = " · ".join(v.get("tags", []))

    rank_label = "🏆 Top Pick" if rank == 0 else f"#{rank + 1}"

    html = f"""
    <div style="font-family:Arial,sans-serif;min-width:200px;max-width:260px">
      <div style="background:#FF6B35;color:white;padding:6px 10px;border-radius:4px 4px 0 0;font-weight:bold">
        {rank_label} — {v['name']}
      </div>
      <div style="padding:8px 10px;border:1px solid #eee;border-top:none;border-radius:0 0 4px 4px">
        <p style="margin:2px 0"><b>🍽</b> {v['specialty']}</p>
        <p style="margin:2px 0"><b>📍</b> {v['location']}</p>
        <p style="margin:2px 0"><b>⭐</b> {rating} &nbsp; <b>📏</b> {dist:.2f} km</p>
        <p style="margin:2px 0"><b>💰</b> {price} &nbsp; {veg_badge}</p>
        {"<p style='margin:4px 0;color:#FF6B35'><b>Must Try:</b> " + must_try + "</p>" if must_try else ""}
        {"<p style='margin:4px 0;font-size:11px;color:#888'>" + tags + "</p>" if tags else ""}
      </div>
    </div>
    """
    return html


def generate_map(
    user_lat: float,
    user_lon: float,
    vendors: List[Dict],
    show_all: bool = False,
    all_vendors: List[Dict] = None,
) -> folium.Map:
    """
    Generates a Folium map.
    - Blue pulse marker = user location
    - Ranked markers for top vendors (green=1st, orange=2nd, etc.)
    - Optional grey cluster for all other vendors
    """
    m = folium.Map(
        location=[user_lat, user_lon],
        zoom_start=14,
        tiles="CartoDB positron",
    )

    # ── User location ──────────────────────────────────
    folium.CircleMarker(
        location=[user_lat, user_lon],
        radius=10,
        color="#0078FF",
        fill=True,
        fill_color="#0078FF",
        fill_opacity=0.4,
        popup="📍 You are here",
        tooltip="Your Location",
    ).add_to(m)

    folium.Marker(
        [user_lat, user_lon],
        popup="📍 You are here",
        tooltip="You",
        icon=folium.Icon(color="blue", icon="user", prefix="fa"),
    ).add_to(m)

    # ── All vendors cluster (background, grey) ─────────
    if show_all and all_vendors:
        cluster = MarkerCluster(name="All Vendors").add_to(m)
        top_names = {v["name"] for v in vendors}
        for v in all_vendors:
            if v["name"] in top_names:
                continue
            lat, lon = v["coordinates"]
            folium.CircleMarker(
                location=[lat, lon],
                radius=5,
                color="#aaa",
                fill=True,
                fill_color="#ccc",
                fill_opacity=0.6,
                tooltip=v["name"],
                popup=folium.Popup(
                    f"<b>{v['name']}</b><br>{v['specialty']}<br>{v['location']}",
                    max_width=200,
                ),
            ).add_to(cluster)

    # ── Top vendors ────────────────────────────────────
    for i, v in enumerate(vendors):
        lat, lon = v["coordinates"]
        color = RANK_COLORS[i] if i < len(RANK_COLORS) else "gray"
        icon  = RANK_ICONS[i]  if i < len(RANK_ICONS)  else "map-marker"

        popup_html = _vendor_popup(v, i)

        folium.Marker(
            [lat, lon],
            popup=folium.Popup(popup_html, max_width=280),
            tooltip=f"{'🏆' if i == 0 else f'#{i+1}'} {v['name']}",
            icon=folium.Icon(color=color, icon=icon, prefix="glyphicon"),
        ).add_to(m)

        # Draw line from user to top pick
        if i == 0:
            folium.PolyLine(
                locations=[[user_lat, user_lon], [lat, lon]],
                color="#FF6B35",
                weight=2.5,
                dash_array="6",
                tooltip=f"{v['dist']:.2f} km to {v['name']}",
            ).add_to(m)

    # ── Layer control ──────────────────────────────────
    folium.LayerControl().add_to(m)

    return m

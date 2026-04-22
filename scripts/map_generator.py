import folium

def generate_indore_map(user_lat, user_lon, vendors):
    import folium

    m = folium.Map(location=[user_lat, user_lon], zoom_start=14)

    # User marker
    folium.Marker(
        [user_lat, user_lon],
        popup="You are here",
        icon=folium.Icon(color="blue")
    ).add_to(m)

    # Vendors
    for i, v in enumerate(vendors):
        lat, lon = v["coordinates"]
        color = "green" if i == 0 else "red"

        folium.Marker(
            [lat, lon],
            popup=f"{v['name']}<br>{v['specialty']}<br>{v.get('dist',0):.2f} km",
            tooltip=v["name"],
            icon=folium.Icon(color=color)
        ).add_to(m)

    return m   # ✅ THIS LINE WAS MISSING
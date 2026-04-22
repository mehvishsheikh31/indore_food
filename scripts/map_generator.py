import folium
import os

def generate_indore_map(user_lat, user_lon, vendors_to_show):
    # Center map on User or the city center
    indore_map = folium.Map(location=[user_lat, user_lon], zoom_start=14)

    # Add User Marker (Blue)
    folium.Marker(
        location=[user_lat, user_lon],
        popup="Bhiya, You are here!",
        icon=folium.Icon(color='blue', icon='user', prefix='fa')
    ).add_to(indore_map)

    # Add markers for the filtered food spots (Red)
    for v in vendors_to_show:
        folium.Marker(
            location=v['coordinates'],
            popup=f"<b>{v['name']}</b><br>Specialty: {v['specialty']}",
            tooltip=v['name'],
            icon=folium.Icon(color='red', icon='cutlery', prefix='fa')
        ).add_to(indore_map)

    # Ensure data folder exists
    if not os.path.exists('data'):
        os.makedirs('data')
        
    indore_map.save('data/indore_food_map.html')
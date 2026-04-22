import json
from geopy.geocoders import Nominatim
import time
import os

# Create data directory if it doesn't exist
if not os.path.exists('data'):
    os.makedirs('data')

# 1. ADD YOUR LIST HERE (Expand this to 100 names)
famous_spots = [
    # --- Chappan Dukan (56 Shops) ---
    {"name": "Vijay Chaat House, Chappan Dukan", "specialty": "Khopra Patties"},
    {"name": "Johny Hot Dog, Chappan Dukan", "specialty": "Egg Benjo"},
    {"name": "Madhuram Sweets, Chappan Dukan", "specialty": "Shikanji"},
    {"name": "Young Tarang, Chappan Dukan", "specialty": "Poha Jalebi"},
    {"name": "Sam's Momos, Chappan Dukan", "specialty": "Tandoori Momos"},
    {"name": "Ramesh Masala Dosa, Chappan Dukan", "specialty": "Dosa"},
    {"name": "Michael's Dosa, Chappan Dukan", "specialty": "Fusion Dosa"},
    {"name": "Gangaur Sweets, Chappan Dukan", "specialty": "Bengali Sweets"},
    {"name": "Coconut Crush, Chappan Dukan", "specialty": "Coconut Drinks"},
    {"name": "Addiction, Chappan Dukan", "specialty": "Coffee & Shakes"},

    # --- Sarafa Night Market ---
    {"name": "Joshi Dahi Bada House, Sarafa Bazaar", "specialty": "Dahi Bada"},
    {"name": "Nagori Shikanji, Sarafa Bazaar", "specialty": "Indori Shikanji"},
    {"name": "Jai Bhole Jaleba, Sarafa Bazaar", "specialty": "Jaleba"},
    {"name": "Sanwariya Seth Sabudana Khichdi, Sarafa Bazaar", "specialty": "Sabudana Khichdi"},
    {"name": "Anna Bhaiya Paan, Sarafa Bazaar", "specialty": "Gundi Paan"},
    {"name": "Rajhans, Sarafa Bazaar", "specialty": "Dal Bafla"},
    {"name": "Avon Garadu, Sarafa Bazaar", "specialty": "Garadu"},
    {"name": "Agrawal 420, Sarafa Bazaar", "specialty": "Gajak"},
    {"name": "Kulfi In A Kulhad, Sarafa Bazaar", "specialty": "Kulfi"},
    {"name": "Sita Ram Garadu, Sarafa Bazaar", "specialty": "Spicy Garadu"},

    # --- Rajwada & Old City ---
    {"name": "Prashant Nashta Corner, Rajwada", "specialty": "Poha Jalebi"},
    {"name": "Head Sahab Ke Pohe, Gali No 1 Rajwada", "specialty": "Usal Poha"},
    {"name": "Samosa Corner, Rajwada", "specialty": "Khatta Samosa"},
    {"name": "Janta Kachori, Rajwada", "specialty": "Kachori"},
    {"name": "Sindhi Colony Dal Pakwan, Sindhi Colony", "specialty": "Dal Pakwan"},
    {"name": "Hira Chaat Corner, Rajwada", "specialty": "Aloo Tikki"},
    {"name": "Gurukripa, Sarwate Bus Stand", "specialty": "Sev Tamatar"},
    {"name": "Ghamandi Lassi, Sarwate Bus Stand", "specialty": "Lassi"},

    # --- Vijay Nagar & Palasia ---
    {"name": "Kebabsville, Sayaji Hotel", "specialty": "Kebabs"},
    {"name": "Nafees Restaurant, Old Palasia", "specialty": "Biryani"},
    {"name": "Tinku's, New Palasia", "specialty": "Cold Coffee"},
    {"name": "Apna Sweets, Vijay Nagar", "specialty": "Namkeen"},
    {"name": "Shreemaya Celebrity, Vijay Nagar", "specialty": "Pastries"},
    {"name": "Little Monk, Bypass Road", "specialty": "Buffet"},
    {"name": "Mocha, Vijay Nagar", "specialty": "Continental"},
    {"name": "The Yellow Chilli, Vijay Nagar", "specialty": "Indian Cuisine"},
    {"name": "C21 Mall Food Court, Vijay Nagar", "specialty": "Fast Food"},
    {"name": "O'Indore, Bhawarkuan", "specialty": "Indori Meals"},
    {"name": "Sagar Gaire, New Palasia", "specialty": "Pasta"},
    {"name": "Chai Kaapi, Vijay Nagar", "specialty": "Adrak Chai"}
    
    # ... You can continue this pattern to reach 100!
]

geolocator = Nominatim(user_agent="indore_urban_geocoder")
final_data = []

print("📍 Starting Geocoder... please wait.")
for spot in famous_spots:
    try:
        # STRATEGY: Try searching for the shop name first
        query = f"{spot['name']}, Indore, Madhya Pradesh"
        location = geolocator.geocode(query)
        
        # If not found, try searching just for the landmark/area
        if not location and "," in spot['name']:
            fallback_query = f"{spot['name'].split(',')[1].strip()}, Indore"
            print(f"⚠️ Retrying with area: {fallback_query}")
            location = geolocator.geocode(fallback_query)

        if location:
            final_data.append({
                "name": spot['name'].split(',')[0],
                "location": spot['name'].split(',')[1].strip() if ',' in spot['name'] else "Indore",
                "coordinates": [location.latitude, location.longitude],
                "specialty": spot['specialty'],
                "vibe": "Iconic",
                "opening_time": "09:00",
                "closing_time": "22:00"
            })
            print(f"✅ Found: {spot['name']}")
        else:
            print(f"❌ Could not find: {spot['name']}")
        
        time.sleep(1.2) 
    except Exception as e:
        print(f"⚠️ Error: {e}")
# Save the final file
with open('data/indore_vendors.json', 'w') as f:
    json.dump(final_data, f, indent=4)

print(f"\n🚀 Done! {len(final_data)} locations saved to data/indore_vendors.json")
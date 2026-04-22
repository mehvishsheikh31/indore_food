import json
import math
from config import get_groq_client

def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371.0  # Earth radius in km
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def get_recommendation_with_distance(user_lat, user_lon, user_query):
    with open('data/indore_vendors.json', 'r') as f:
        vendors = json.load(f)
    
    # Calculate distance for all and find the closest
    for v in vendors:
        v['dist'] = calculate_distance(user_lat, user_lon, v['coordinates'][0], v['coordinates'][1])
    
    # Sort by distance
    vendors.sort(key=lambda x: x['dist'])
    nearest_vendor = vendors[0]
    
    client = get_groq_client()
    prompt = f"""
    You are 'Indori Foodie AI', a helpful and witty guide.
    User is at ({user_lat}, {user_lon}).
    The nearest famous spot is '{nearest_vendor['name']}' which is only {nearest_vendor['dist']:.2f}km away.
    
    User Craving: {user_query}
    Vendor Context: {nearest_vendor}
    
    Task:
    1. Acknowledge their craving.
    2. Tell them exactly how far {nearest_vendor['name']} is.
    3. Use a bit of Indori lingo (Bhiya, Swaad, Chalo).
    4. Mention if the current 'Vibe' ({nearest_vendor['vibe']}) matches their query.
    """
    
    response = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama-3.1-8b-instant",
    )
    return response.choices[0].message.content
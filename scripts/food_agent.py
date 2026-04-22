import math
from config import get_groq_client

def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = math.sin(dphi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def score_vendor(v, query, user_lat, user_lon):
    score = 0
    query = query.lower()

    # Distance
    dist = calculate_distance(user_lat, user_lon, v['coordinates'][0], v['coordinates'][1])
    v['dist'] = dist
    score += max(0, 15 - dist)

    # Specialty match
    if query in v.get("specialty", "").lower():
        score += 15

    # Taste match
    for t in v.get("taste_profile", []):
        if t in query:
            score += 10

    # Time match
    for t in v.get("best_time", []):
        if t in query:
            score += 8

    # Famous boost
    if v.get("is_famous"):
        score += 5

    return score


def get_recommendation_with_distance(user_lat, user_lon, user_query, vendors):
    # Score all vendors
    for v in vendors:
        v['score'] = score_vendor(v, user_query, user_lat, user_lon)

    ranked = sorted(vendors, key=lambda x: x['score'], reverse=True)

    top3 = ranked[:3]
    best = top3[0]

    context = "\n".join([
        f"{v['name']} - {v['specialty']} ({v['dist']:.2f} km)"
        for v in top3
    ])

    client = get_groq_client()

    prompt = f"""
You are a smart Indore food expert.

User craving: {user_query}

Top options:
{context}

Rules:
- Recommend ONLY 1 best option
- Explain based on distance + taste match
- Keep answer short (4-5 lines)
- Use light local tone (not cringe)
"""

    response = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama-3.1-8b-instant",
    )

    return response.choices[0].message.content, top3
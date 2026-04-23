"""
food_agent.py – Scoring + Groq recommendation engine
"""
import math
from typing import List, Dict, Tuple
from config import get_groq_client, GROQ_MODEL, TOP_N


# ──────────────────────────────────────────────
# Distance
# ──────────────────────────────────────────────
def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Returns distance in km between two GPS points."""
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


# ──────────────────────────────────────────────
# Scoring
# ──────────────────────────────────────────────
def _score_vendor(v: Dict, query: str, user_lat: float, user_lon: float) -> float:
    """
    Multi-factor scoring:
      - Proximity        (max 20 pts, drops linearly over 10 km)
      - Specialty match  (15 pts exact, 8 pts partial)
      - Taste profile    (10 pts per matching taste word)
      - Best-time match  (8 pts per matching time word)
      - Famous boost     (5 pts)
      - Rating           (up to 5 pts)
      - Tags match       (5 pts per matching tag word)
    """
    q = query.lower()
    lat2, lon2 = v["coordinates"]
    dist = haversine(user_lat, user_lon, lat2, lon2)
    v["dist"] = round(dist, 3)

    score = 0.0

    # Proximity (linear decay: 20 pts at 0 km → 0 pts at 10 km)
    score += max(0, 20 - dist * 2)

    # Specialty
    specialty = v.get("specialty", "").lower()
    if q in specialty:
        score += 15
    elif any(word in specialty for word in q.split()):
        score += 8

    # Taste profile
    for taste in v.get("taste_profile", []):
        if taste.lower() in q:
            score += 10

    # Best time
    for t in v.get("best_time", []):
        if t.lower() in q:
            score += 8

    # Famous
    if v.get("is_famous"):
        score += 5

    # Rating boost (out of 5 → map to 0-5)
    rating = v.get("rating", 0)
    score += rating

    # Tags
    for tag in v.get("tags", []):
        if tag.lower() in q:
            score += 5

    return score


def rank_vendors(
    vendors: List[Dict],
    query: str,
    user_lat: float,
    user_lon: float,
    top_n: int = TOP_N,
) -> List[Dict]:
    """Returns a copy of top_n vendors sorted by score (desc)."""
    scored = []
    for v in vendors:
        vc = dict(v)           # don't mutate original
        vc["score"] = _score_vendor(vc, query, user_lat, user_lon)
        scored.append(vc)
    return sorted(scored, key=lambda x: x["score"], reverse=True)[:top_n]


# ──────────────────────────────────────────────
# AI Recommendation
# ──────────────────────────────────────────────
def build_prompt(query: str, top_vendors: List[Dict], user_lat: float, user_lon: float) -> str:
    lines = []
    for i, v in enumerate(top_vendors):
        badge = "🏆 Top Pick" if i == 0 else f"#{i+1}"
        lines.append(
            f"{badge} | {v['name']} ({v['location']}) | {v['specialty']} "
            f"| {v['dist']:.2f} km | Rating {v.get('rating', 'N/A')}"
        )
    context = "\n".join(lines)

    return f"""You are a passionate Indore street food expert — knowledgeable, warm, and a little cheeky.

User craving: "{query}"
User coordinates: {user_lat:.4f}, {user_lon:.4f}

Top matching spots:
{context}

Instructions:
- Recommend the single BEST match. Mention its name clearly.
- In 4-6 lines explain WHY it suits the craving (taste, distance, vibe).
- Mention one must-try dish.
- Use a friendly, local Indori tone — English only, no cringe transliteration.
- End with a one-liner hype sentence.

Do NOT list all options. Focus on the BEST one only."""


def get_recommendation(
    user_lat: float,
    user_lon: float,
    query: str,
    vendors: List[Dict],
) -> Tuple[str, List[Dict]]:
    """
    Returns (ai_text, top_vendors_list).
    top_vendors already have 'dist' and 'score' populated.
    """
    top = rank_vendors(vendors, query, user_lat, user_lon)
    prompt = build_prompt(query, top, user_lat, user_lon)

    client = get_groq_client()
    response = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model=GROQ_MODEL,
        temperature=0.7,
        max_tokens=300,
    )
    text = response.choices[0].message.content.strip()
    return text, top


def stream_recommendation(
    user_lat: float,
    user_lon: float,
    query: str,
    vendors: List[Dict],
):
    """
    Generator that yields (chunk_text, top_vendors | None).
    top_vendors is returned in the FIRST yield as second element,
    then subsequent yields have None as second element.
    """
    top = rank_vendors(vendors, query, user_lat, user_lon)
    prompt = build_prompt(query, top, user_lat, user_lon)

    client = get_groq_client()
    with client.chat.completions.stream(
        messages=[{"role": "user", "content": prompt}],
        model=GROQ_MODEL,
        temperature=0.7,
        max_tokens=300,
    ) as stream:
        first = True
        for chunk in stream:
            delta = chunk.choices[0].delta.content or ""
            if delta:
                if first:
                    yield delta, top
                    first = False
                else:
                    yield delta, None

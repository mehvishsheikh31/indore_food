"""
food_agent.py - Agentic scoring + Groq decision engine

This is the "agent" layer. It runs a multi-step loop instead of a single
LLM call that just narrates a pre-picked winner:

    1. PERCEIVE  -> LLM parses the free-text craving into structured intent
                     (mood, budget, time, veg preference, keywords)
    2. ACT       -> deterministic scoring engine ranks candidates using
                     that structured intent
    3. DECIDE    -> LLM looks at the top candidates and actually CHOOSES
                     the winner itself (not just describes Python's pick),
                     and reports a confidence score
    4. REFLECT   -> if the LLM isn't confident enough in its own pick,
                     the agent autonomously widens the search pool
                     (drops filters, considers more vendors) and re-runs
                     steps 2-3 -- up to one retry
    5. RESPOND   -> LLM writes the final friendly recommendation for the
                     vendor IT chose

Every step is captured in a `trace` list so the UI can show what the
agent actually did (useful for demoing "agentic" behavior).
"""
import json
import math
from typing import List, Dict, Tuple, Optional
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


def _safe_json_parse(raw: str) -> Optional[dict]:
    """Groq sometimes wraps JSON in ```json fences despite instructions - strip them."""
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("```")[1]
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:]
    cleaned = cleaned.strip()
    try:
        return json.loads(cleaned)
    except (json.JSONDecodeError, IndexError):
        return None


# ──────────────────────────────────────────────
# STEP 1 - PERCEIVE: parse free text into structured intent
# ──────────────────────────────────────────────
def extract_intent(query: str) -> Dict:
    """
    Uses the LLM to turn a natural-language craving into structured fields.
    Falls back to a permissive default if parsing fails, so the agent
    never crashes the app.
    """
    prompt = f"""Extract structured food-search intent from this user query.

User query: "{query}"

Respond with ONLY valid JSON (no markdown fences, no commentary), matching
exactly this schema:
{{
  "time_of_day": "morning" | "afternoon" | "evening" | "night" | "any",
  "mood_keywords": [list of taste/mood words like "spicy","sweet","tangy","light","heavy"],
  "budget": "low" | "medium" | "high" | "any",
  "veg_only": true | false | null,
  "dish_keywords": [list of specific dish/food names mentioned, empty list if none]
}}"""

    client = get_groq_client()
    default_intent = {
        "time_of_day": "any",
        "mood_keywords": [],
        "budget": "any",
        "veg_only": None,
        "dish_keywords": [],
    }
    try:
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=GROQ_MODEL,
            temperature=0.2,
            max_tokens=200,
        )
        parsed = _safe_json_parse(response.choices[0].message.content)
        if parsed:
            return {**default_intent, **parsed}
    except Exception:
        pass
    return default_intent


# ──────────────────────────────────────────────
# STEP 2 - ACT: deterministic scoring, now driven by parsed intent
# ──────────────────────────────────────────────
def _score_vendor(v: Dict, query: str, intent: Dict, user_lat: float, user_lon: float) -> float:
    q = query.lower()
    lat2, lon2 = v["coordinates"]
    dist = haversine(user_lat, user_lon, lat2, lon2)
    v["dist"] = round(dist, 3)

    score = 0.0

    # Proximity (linear decay: 20 pts at 0 km -> 0 pts at 10 km)
    score += max(0, 20 - dist * 2)

    # Specialty / dish keywords (from intent, falls back to raw query)
    specialty = v.get("specialty", "").lower()
    dish_terms = [d.lower() for d in intent.get("dish_keywords", [])] or q.split()
    if any(term in specialty for term in dish_terms):
        score += 15

    # Taste / mood match
    taste_profile = [t.lower() for t in v.get("taste_profile", [])]
    for mood in intent.get("mood_keywords", []):
        if mood.lower() in taste_profile or mood.lower() in q:
            score += 10

    # Best time match
    tod = intent.get("time_of_day", "any")
    if tod != "any" and tod in [t.lower() for t in v.get("best_time", [])]:
        score += 8

    # Budget match
    budget = intent.get("budget", "any")
    if budget != "any" and v.get("price_range", "").lower() == budget:
        score += 8

    # Veg filter as a strong signal (not a hard filter, so agent can still recover)
    if intent.get("veg_only") is True and v.get("is_pure_veg"):
        score += 6
    if intent.get("veg_only") is False and not v.get("is_pure_veg"):
        score += 2

    # Famous boost
    if v.get("is_famous"):
        score += 5

    # Rating boost
    score += v.get("rating", 0)

    # Tags
    for tag in v.get("tags", []):
        if tag.lower() in q:
            score += 5

    return score


def rank_vendors(
    vendors: List[Dict],
    query: str,
    intent: Dict,
    user_lat: float,
    user_lon: float,
    top_n: int = TOP_N,
) -> List[Dict]:
    scored = []
    for v in vendors:
        vc = dict(v)
        vc["score"] = _score_vendor(vc, query, intent, user_lat, user_lon)
        scored.append(vc)
    return sorted(scored, key=lambda x: x["score"], reverse=True)[:top_n]


# ──────────────────────────────────────────────
# STEP 3 - DECIDE: LLM actually picks the winner + confidence
# ──────────────────────────────────────────────
def agent_decide(query: str, candidates: List[Dict], user_lat: float, user_lon: float) -> Optional[Dict]:
    """
    Gives the LLM the candidate list and makes IT choose, rather than
    trusting the scoring engine's #1 blindly. Returns None on failure
    so the caller can fall back gracefully.
    """
    lines = []
    for v in candidates:
        lines.append(
            f"- {v['name']} | specialty: {v['specialty']} | taste: {v.get('taste_profile')} "
            f"| best_time: {v.get('best_time')} | price: {v.get('price_range')} "
            f"| veg: {v.get('is_pure_veg')} | rating: {v.get('rating')} | dist_km: {v['dist']:.2f} "
            f"| prescore: {v['score']:.1f}"
        )
    candidate_block = "\n".join(lines)

    prompt = f"""You are a street-food recommendation agent for Indore, India.

User craving: "{query}"
User coordinates: {user_lat:.4f}, {user_lon:.4f}

Candidate vendors (with a rough pre-score, which you may override if you
disagree — you are the final decision maker, not the pre-score):
{candidate_block}

Decide the single best vendor for this craving. Be honest about how
confident you are: if none of these candidates are a good match for what
the user asked for, say so with a low confidence score instead of forcing
a pick.

Respond with ONLY valid JSON (no markdown fences), matching exactly:
{{
  "chosen_name": "<exact vendor name from the list>",
  "confidence": <float 0.0 to 1.0>,
  "reasoning": "<1-2 sentence internal justification>",
  "narrative": "<4-6 line friendly Indori-toned recommendation for the user, mentioning the must-try dish and ending with a short hype line>",
  "need_wider_search": <true/false — true if none of these candidates fit well>
}}"""

    client = get_groq_client()
    try:
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=GROQ_MODEL,
            temperature=0.5,
            max_tokens=400,
        )
        return _safe_json_parse(response.choices[0].message.content)
    except Exception:
        return None


# ──────────────────────────────────────────────
# STEP 4/5 orchestration - REFLECT + RESPOND
# ──────────────────────────────────────────────
def get_recommendation(
    user_lat: float,
    user_lon: float,
    query: str,
    vendors: List[Dict],
    all_vendors: Optional[List[Dict]] = None,
) -> Tuple[str, List[Dict], List[Dict]]:
    """
    Runs the full agent loop.

    `vendors`      - the filtered pool (respects the user's sidebar filters)
    `all_vendors`  - the full unfiltered pool, used only if the agent decides
                      the filtered pool doesn't have a good match and wants
                      to widen its search. Falls back to `vendors` if not given.

    Returns (narrative_text, top_candidates_shown, agent_trace)
    trace is a list of dicts describing each step, for UI transparency.
    """
    trace = []
    search_pool = vendors
    all_vendors = all_vendors or vendors

    # STEP 1 - PERCEIVE
    intent = extract_intent(query)
    trace.append({"step": "Parsed intent", "detail": intent})

    # STEP 2 - ACT (first pass)
    top = rank_vendors(search_pool, query, intent, user_lat, user_lon, top_n=max(TOP_N, 5))
    trace.append({
        "step": "Scored candidates",
        "detail": f"Ranked {len(search_pool)} vendors, top pre-score pick: "
                  f"{top[0]['name'] if top else 'none'}"
    })

    # STEP 3 - DECIDE
    decision = agent_decide(query, top, user_lat, user_lon) if top else None

    # STEP 4 - REFLECT (autonomous retry with a wider pool if unconfident)
    widened = False
    if (decision is None or decision.get("need_wider_search") or
            (decision and decision.get("confidence", 1) < 0.45)) and len(all_vendors) > len(search_pool):
        trace.append({
            "step": "Low confidence -> widening search",
            "detail": f"Confidence was "
                      f"{decision.get('confidence') if decision else 'N/A'}; "
                      f"expanding from {len(search_pool)} to {len(all_vendors)} vendors"
        })
        search_pool = all_vendors
        top = rank_vendors(search_pool, query, intent, user_lat, user_lon, top_n=8)
        decision = agent_decide(query, top, user_lat, user_lon) or decision
        widened = True

    # Fallback if the LLM decision step failed entirely
    if decision is None:
        trace.append({"step": "Decision failed, falling back to top pre-score pick", "detail": None})
        best = top[0] if top else None
        text = (f"{best['name']} looks like your best bet for \"{query}\" — "
                f"try the {best.get('must_try', best['specialty'])}!") if best else \
               "Couldn't find a solid match — try loosening your filters."
        return text, top[:TOP_N], trace

    trace.append({
        "step": "Agent decided",
        "detail": {
            "chosen_name": decision.get("chosen_name"),
            "confidence": decision.get("confidence"),
            "reasoning": decision.get("reasoning"),
            "widened_search": widened,
        }
    })

    # Reorder so the LLM's chosen vendor is #1 in what we show, since the
    # agent may have overridden the pre-score ranking
    chosen_name = decision.get("chosen_name")
    if chosen_name:
        top = sorted(top, key=lambda v: v["name"] != chosen_name)

    narrative = decision.get("narrative") or "Here's a great pick for your craving!"
    return narrative, top[:TOP_N], trace
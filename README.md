<div align="center">

# 🍴 Indore Food Intelligence

### *Your AI-powered street food guide for the City of Food Lovers*

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.32+-FF4B4B?style=flat-square&logo=streamlit&logoColor=white)](https://streamlit.io)
[![Groq](https://img.shields.io/badge/Groq-LLaMA_3.1-F55036?style=flat-square)](https://groq.com)
[![Folium](https://img.shields.io/badge/Folium-Maps-77B829?style=flat-square)](https://python-visualization.github.io/folium)
[![License](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](LICENSE)

<br/>

> *"Tell me you're craving something tangy and spicy at midnight —*
> *and I'll point you to the best dahi wada in Sarafa."*

<br/>

</div>

---

## 🌟 What Is This?

**Indore Food Intelligence** is a geospatial **agentic AI** app that helps you discover the best street food vendors in Indore, Madhya Pradesh — instantly. Describe your craving in plain language and the app finds the perfect spot based on your **location**, **mood**, **budget**, and **time of day**.

No generic lists. No sponsored results. Just a local food-obsessed AI that actually gets Indori culture.

---

## ✨ Features

| Feature | Description |
|---|---|
| 🤖 **AI Recommendation** | Describe your craving naturally — the LLM picks the single best match and explains why |
| 🧭 **Explore Mode** | Browse all vendors in a filterable, sortable card grid |
| 🗺️ **Live Map** | Interactive Folium map with ranked markers, your location pin & route lines |
| 📜 **Search History** | Recent searches saved in session — re-run any past query in one click |
| 📤 **Share & Export** | Copy picks as text, share via WhatsApp, or download filtered vendors as CSV |
| 📍 **GPS Support** | Auto-detects your location for distance-aware recommendations |
| 🔍 **Smart Filters** | Filter by area, veg/non-veg, price range, min rating, and free-text search |
| ⚡ **One-tap quick picks** | Poha, Spicy, Late Night, etc. — tap to instantly fill and search |

---

## 🧠 How the AI Agent Works

This isn't a single LLM call that narrates a pre-picked winner — it's a real multi-step agent loop:

```
Your Craving (natural language)
        │
        ▼
 1. PERCEIVE — LLM parses free text into structured intent
  ┌─────────────────────────────┐
  │  Time: morning / evening …  │
  │  Mood: spicy / sweet / …    │
  │  Budget: low / medium       │
  └─────────────────────────────┘
        │
        ▼
 2. ACT — deterministic multi-factor scoring (per vendor)
  ┌──────────────────────────────────────┐
  │  📍 Proximity          → max 20 pts  │
  │  🍽  Specialty match   → max 15 pts  │
  │  🌶  Taste/mood match  → max 12 pts  │
  │  🕐  Best-time match   → max 10 pts  │
  │  💰  Budget match      →  max 8 pts  │
  │  ⭐  Rating boost      →  max 5 pts  │
  │  🏷  Tag match         →  max 5 pts  │
  └──────────────────────────────────────┘
        │
        ▼
 3. DECIDE — LLM looks at top candidates and picks the
    winner itself, with a confidence score
        │
        ▼
 4. REFLECT — if confidence is low, the agent autonomously
    widens the search pool and re-runs steps 2-3 (up to 1 retry)
        │
        ▼
 5. RESPOND — LLM writes the final friendly recommendation
    for the vendor it chose 🎉
```

Every step is logged to an `agent_trace`, visible in the app under **"🧠 See how the agent decided this."**

---

## 🗂️ Project Structure

```
indore_food-main/
├── app.py                  # Streamlit UI — all tabs & session state
├── config.py                # API keys, constants, Groq client init
├── build_dataset.py         # Script to build/extend vendor JSON
├── requirements.txt         # Python dependencies
│
├── data/
│   └── indore_vendors.json  # 40 vendors across 10 Indore areas
│
└── scripts/
    ├── food_agent.py        # Agent loop: perceive → act → decide → reflect → respond
    ├── map_generator.py     # Folium map builder
    └── gps_component.py     # Browser GPS widget
```

---

## 🚀 Getting Started

### 1 — Clone the repo

```bash
git clone https://github.com/your-username/indore_food.git
cd indore_food
```

### 2 — Install dependencies

```bash
pip install -r requirements.txt
```

### 3 — Set up your API key

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key_here
```

> Get a free key at [console.groq.com](https://console.groq.com)

### 4 — Run the app

```bash
streamlit run app.py
```

Open `http://localhost:8501` in your browser. 🎉

---

## 🗺️ Vendor Coverage

**40 vendors** across **10 Indore food zones:**

| Area | Known For |
|---|---|
| 🌙 **Sarafa** | Late-night street food paradise |
| 🏪 **Chappan Dukan** | 56 shops, the ultimate food street |
| 🍽 **Anand Bazaar** | Breakfast & morning specials |
| 🛍 **Vijay Nagar** | Modern cafes + quick bites |
| 🏰 **Rajwada** | Heritage area, old-school flavours |
| 🌿 **Palasia** | Veg-heavy, family-friendly spots |
| 🚉 **Sarwate** | Budget street food near the bus stand |
| 🏡 **Rajendra Nagar** | Local neighbourhood gems |
| 🏘 **LIG Colony** | Residential-area local favourites |
| 🕌 **Chhatripura** | Old-city classic vendors |

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | Streamlit |
| **AI / LLM** | Groq API — LLaMA 3.1 8B Instant (agentic loop, not a single call) |
| **Maps** | Folium + streamlit-folium |
| **Geolocation** | Browser GPS via `streamlit-js-eval` |
| **Data** | Hand-curated JSON dataset |
| **Language** | Python 3.10+ |

---

## 📦 Dependencies

```txt
streamlit>=1.32.0
streamlit-folium>=0.18.0
folium>=0.16.0
groq>=0.9.0
python-dotenv>=1.0.0
streamlit-js-eval>=0.1.7
```

---

## 🩹 Changelog / Fixes

**Latest update — click-through & stability fixes:**

- 🐛 **Fixed:** Quick-pick buttons (Poha, Spicy, Late Night, etc.) didn't fill the search box — a Streamlit widget state-timing bug meant every click was silently ignored.
- 🐛 **Fixed:** The History tab's "🔁 Re-run" button crashed the app with a `StreamlitAPIException` (writing to a widget's state after it had already rendered in the same pass).
- 🐛 **Fixed:** `streamlit-js-eval` was used by `gps_component.py` but missing from `requirements.txt`, so GPS detection would fail on a fresh install.
- ✅ Verified end-to-end with Streamlit's `AppTest` harness: every button, tab, filter, slider, and the full agent loop (Perceive → Act → Decide → Reflect → Respond) now runs without exceptions.

---

## 🤝 Contributing

Pull requests are welcome! To add a new vendor, edit `data/indore_vendors.json` following this schema:

```json
{
  "name": "Vendor Name",
  "location": "Landmark / Street",
  "area": "Area Name",
  "coordinates": [22.7196, 75.8577],
  "specialty": "Signature Dish",
  "vibe": "Casual / Theatrical / Quick Service",
  "is_pure_veg": true,
  "price_range": "low",
  "is_famous": true,
  "taste_profile": ["spicy", "tangy"],
  "best_time": ["evening", "night"],
  "rating": 4.5,
  "must_try": "The dish everyone orders",
  "tags": ["street food", "famous", "sarafa"]
}
```

---

## 📄 License

MIT License — free to use, fork, and build upon.

---

<div align="center">

Made with ❤️ for Indore — *Khao, Piyo, Maze Karo* 🌶️

</div>
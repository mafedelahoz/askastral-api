from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from astropy.coordinates import get_body, EarthLocation, solar_system_ephemeris
from astropy.time import Time
from astropy.coordinates import CartesianRepresentation
import numpy as np

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "🌌 Welcome to AskAstral API"}

@app.get("/planet/{planet_name}")
def get_planet_position(planet_name: str):
    try:
        location = EarthLocation.of_site("greenwich")
        now = Time(datetime.utcnow())
        planet = get_body(planet_name.lower(), now, location)
        ra_deg = planet.ra.deg
        retrograde = is_retrograde(planet_name.lower(), now)

        prediction = get_emotional_prediction_by_position(planet_name, ra_deg, retrograde)

        return {
            "planet": planet_name.lower(),
            "zodiac_sign": prediction["sign"],
            "position": {
                "ra": f"{planet.ra.deg:.2f}°",
                "dec": f"{planet.dec.deg:.2f}°",
                "distance_au": f"{planet.distance.au:.2f} AU"
            },
            "timestamp": str(now),
            "retrograde": retrograde,
            "prediction": {
                "summary": prediction["summary"],
                "advice": prediction["advice"],
                "vibe": prediction["vibe"]
            }
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/daily-insight")
def daily_insight():
    planets = ["mercury", "venus", "mars", "jupiter", "saturn"]
    location = EarthLocation.of_site("greenwich")
    now = Time(datetime.utcnow())

    results = []

    for planet_name in planets:
        try:
            planet = get_body(planet_name, now, location)
            ra_deg = planet.ra.deg
            retrograde = is_retrograde(planet_name, now)
            prediction = get_emotional_prediction_by_position(planet_name, ra_deg, retrograde)

            results.append({
                "planet": planet_name,
                "zodiac_sign": prediction["sign"],
                "retrograde": retrograde,
                "prediction": {
                    "summary": prediction["summary"],
                    "advice": prediction["advice"],
                    "vibe": prediction["vibe"]
                }
            })
        except Exception as e:
            results.append({
                "planet": planet_name,
                "error": str(e)
            })

    return {
        "timestamp": str(now),
        "daily_insight": results
    }

def ra_to_zodiac_sign(ra_deg: float) -> str:
    signs = [
        "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
        "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
    ]
    index = int((ra_deg % 360) / 30)
    return signs[index]

def is_retrograde(planet_name: str, now: Time) -> bool:
    try:
        with solar_system_ephemeris.set("builtin"):
            delta_days = 1.0
            pos1 = get_body(planet_name, now - delta_days).cartesian
            pos2 = get_body(planet_name, now + delta_days).cartesian
            vel_vector = pos2 - pos1
            earth_to_planet = get_body(planet_name, now) - get_body("earth", now)
            return np.dot(earth_to_planet.cartesian.xyz, vel_vector.xyz) < 0
    except Exception:
        return False

def get_emotional_prediction_by_position(planet_name: str, ra_deg: float, retrograde: bool) -> dict:
    zodiac_sign = ra_to_zodiac_sign(ra_deg)

    predictions = {
        "venus": {
            "leo": {
                "summary": "Desire for recognition in personal connections may intensify.",
                "advice": "Be mindful of ego-driven behavior. Stay clear in expressing expectations.",
                "vibe": "Expressive, socially driven"
            },
            "scorpio": {
                "summary": "Emotional intensity affects intimacy and trust dynamics.",
                "advice": "Avoid ultimatums. Stay factual in emotionally charged conversations.",
                "vibe": "Intense and introspective"
            },
            "default": {
                "summary": "Relationship themes are active today.",
                "advice": "Stay aware of unspoken emotional needs in close interactions.",
                "vibe": "Relational"
            }
        },
        "mars": {
            "aries": {
                "summary": "Energy is high; action feels natural.",
                "advice": "Use this drive productively. Avoid acting before thinking.",
                "vibe": "High physical momentum"
            },
            "cancer": {
                "summary": "Behavior may be reactive or defensive.",
                "advice": "Pause and process emotional triggers before taking action.",
                "vibe": "Emotionally reactive"
            },
            "default": {
                "summary": "Motivation and assertiveness are impacted.",
                "advice": "Stay focused on goals. Avoid confrontation over small issues.",
                "vibe": "Assertive"
            }
        },
        "mercury": {
            "gemini": {
                "summary": "Mental agility increases. Communication flows easily.",
                "advice": "Good time to write, speak, or plan. Be clear with details.",
                "vibe": "Fast-paced thinking"
            },
            "pisces": {
                "summary": "Thinking may be idealistic or scattered.",
                "advice": "Use outlines and verification to keep plans grounded.",
                "vibe": "Imaginative but unfocused"
            },
            "default": {
                "summary": "Communication and mental processing are active.",
                "advice": "Stay fact-based. Avoid distractions and speculation.",
                "vibe": "Cognitive focus"
            }
        },
        "jupiter": {
            "sagittarius": {
                "summary": "Optimism and exploration are heightened.",
                "advice": "Use the momentum for learning or big-picture planning.",
                "vibe": "Expansive"
            },
            "default": {
                "summary": "Philosophical or belief systems may be challenged or reinforced.",
                "advice": "Reflect on values. Avoid overconfidence.",
                "vibe": "Reflective and broad"
            }
        },
        "saturn": {
            "capricorn": {
                "summary": "Discipline and responsibility come naturally.",
                "advice": "Organize long-term plans. Take serious commitments seriously.",
                "vibe": "Structured and focused"
            },
            "default": {
                "summary": "Themes of structure, limits, or obligations may arise.",
                "advice": "Manage time well. Face responsibilities head-on.",
                "vibe": "Stable but strict"
            }
        }
    }

    planet = planet_name.lower()
    sign = zodiac_sign.lower()
    default = predictions.get(planet, {}).get("default", {
        "summary": "No specific interpretation available.",
        "advice": "Proceed as normal, noting any unusual behavioral patterns.",
        "vibe": "Neutral"
    })

    result = predictions.get(planet, {}).get(sign, default)

    if retrograde:
        result["summary"] += " (Retrograde phase may bring internalized effects or delays.)"
        result["advice"] += " Reflect before acting. Reevaluate ongoing matters."

    return {
        "summary": result["summary"],
        "advice": result["advice"],
        "vibe": result["vibe"],
        "sign": zodiac_sign
    }

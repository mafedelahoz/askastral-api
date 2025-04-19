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

#This endpoint provides the current position of a specified planet in the sky.
# It returns the planet's right ascension (RA), declination (Dec), distance from Earth, and its zodiac sign.
# It also indicates whether the planet is in retrograde motion and provides an emotional prediction based on its position.
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

#This endpoint provides a daily insight based on the positions of five planets: Mercury, Venus, Mars, Jupiter, and Saturn.
# It calculates the right ascension (RA) of each planet, checks if they are in retrograde motion, and provides an emotional prediction based on their positions.
@app.get("/daily-insight")
def daily_insight():
    planets = ["mercury", "venus", "mars", "jupiter", "saturn"]
    location = EarthLocation.of_site("greenwich")
    now = Time(datetime.utcnow())

    insights = []

    for planet_name in planets:
        try:
            planet = get_body(planet_name, now, location)
            ra_deg = planet.ra.deg
            retrograde = is_retrograde(planet_name, now)
            prediction = get_emotional_prediction_by_position(planet_name, ra_deg, retrograde)

            weight = get_influence_weight(planet_name, retrograde)

            insights.append({
                "planet": planet_name,
                "zodiac_sign": prediction["sign"],
                "retrograde": retrograde,
                "prediction": {
                    "summary": prediction["summary"],
                    "advice": prediction["advice"],
                    "vibe": prediction["vibe"]
                },
                "weight": weight
            })
        except Exception as e:
            insights.append({
                "planet": planet_name,
                "error": str(e),
                "weight": 0
            })

    strongest = sorted(insights, key=lambda x: x.get("weight", 0), reverse=True)[0]

    return {
        "timestamp": str(now),
        "most_influential": {
            "planet": strongest["planet"],
            "zodiac_sign": strongest.get("zodiac_sign"),
            "retrograde": strongest.get("retrograde"),
            "prediction": strongest.get("prediction")
        }
    }

#Converts the right ascension (RA) in degrees to a zodiac sign.
def ra_to_zodiac_sign(ra_deg: float) -> str:
    signs = [
        "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
        "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
    ]
    index = int((ra_deg % 360) / 30)
    return signs[index]
#Calculates if a planet is in retrograde motion based on its position relative to Earth.
#It uses the positions of the planet at two different times to determine the direction of its motion.
#If the dot product of the planet's position vector and its velocity vector is negative, it indicates retrograde motion.
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
#Calculates the influence weight of a planet based on its name and whether it is in retrograde motion.
#The weight is determined by a predefined base weight for each planet, and retrograde motion adds an additional weight.
def get_influence_weight(planet: str, retrograde: bool) -> int:
    base_weight = {
        "mercury": 5,
        "venus": 6,
        "mars": 7,
        "jupiter": 4,
        "saturn": 4
    }
    weight = base_weight.get(planet.lower(), 3)
    if retrograde:
        weight += 3  # Retrograde amplifies introspective or disruptive potential
    return weight

#Provides an emotional prediction based on the planet's position in a specific zodiac sign.
#It uses the right ascension (RA) of the planet and its retrograde status to determine the prediction.
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

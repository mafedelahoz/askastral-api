from fastapi import FastAPI
from datetime import datetime
from astropy.coordinates import get_body, EarthLocation
from astropy.time import Time

app = FastAPI()

@app.get("/")
def root():
    return {"message": "🌌 Welcome to AskAstral API"}
@app.get("/planet/{planet_name}")
def get_planet_position(planet_name: str):
    try:
        location = EarthLocation.of_site("greenwich")
        now = Time(datetime.utcnow())
        planet = get_body(planet_name.lower(), now, location)

        ra_deg = planet.ra.deg  # Ascensión recta en grados

        prediction = get_emotional_prediction_by_position(planet_name, ra_deg)

        return {
            "planet": planet_name.lower(),
            "zodiac_sign": ra_to_zodiac_sign(ra_deg),
            "position": {
                "ra": f"{planet.ra.deg:.2f}°",
                "dec": f"{planet.dec.deg:.2f}°",
                "distance_au": f"{planet.distance.au:.2f} AU"
            },
            "timestamp": str(now),
            "prediction": prediction
        }
    except Exception as e:
        return {"error": str(e)}


def ra_to_zodiac_sign(ra_deg: float) -> str:
    signs = [
        "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
        "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
    ]
    index = int((ra_deg % 360) / 30)
    return signs[index]

def get_emotional_prediction_by_position(planet_name: str, ra_deg: float) -> str:
    zodiac_sign = ra_to_zodiac_sign(ra_deg)

    mood_map = {
        "venus": {
            "leo": "You may feel bold in love, seeking attention and warmth.",
            "pisces": "Love takes a dreamy turn; intuition leads the way.",
            "scorpio": "Relationships intensify. Deep emotions rise to the surface.",
        },
        "mars": {
            "aries": "You're driven, courageous, maybe a bit impulsive.",
            "cancer": "You may feel emotionally reactive. Channel energy into home matters.",
            "capricorn": "Focused and strategic, your ambition is strong today.",
        },
        "default": "Your emotional energy is influenced by cosmic alignments. Reflect and adapt."
    }

    key = planet_name.lower()
    planet_effects = mood_map.get(key, {})
    prediction = planet_effects.get(zodiac_sign.lower(), mood_map.get("default"))
    
    return f"{planet_name.capitalize()} in {zodiac_sign}: {prediction}"

# CORS Middleware
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

import os
import re
import requests
from duckduckgo_search import DDGS
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

def _get_weather(location: str) -> str:
    """Fetch real-time weather for any location using Open-Meteo API (free, no auth required)."""
    try:
        # First, geocode the location
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={location}&count=1&language=en&format=json"
        geo_response = requests.get(geo_url, timeout=5)
        geo_data = geo_response.json()
        
        if not geo_data.get("results"):
            # Fallback to DuckDuckGo search
            try:
                with DDGS() as ddgs:
                    results = list(ddgs.text(f"current weather temperature conditions in {location}", max_results=3))
                if results:
                    return f"Raj, according to online reports for {location}: {results[0].get('body', '')}"
            except Exception:
                pass
            return f"Raj, I couldn't find weather data for {location}."
        
        # Get coordinates
        result = geo_data["results"][0]
        lat, lon = result["latitude"], result["longitude"]
        city_name = result.get("name", location)
        country = result.get("country", "")
        
        # Fetch current weather
        weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m&temperature_unit=celsius"
        weather_response = requests.get(weather_url, timeout=5)
        weather_data = weather_response.json()
        
        current = weather_data.get("current", {})
        temp = current.get("temperature_2m", "N/A")
        humidity = current.get("relative_humidity_2m", "N/A")
        wind_speed = current.get("wind_speed_10m", "N/A")
        weather_code = current.get("weather_code", 0)
        
        # Map weather codes to descriptions
        weather_descriptions = {
            0: "Clear sky",
            1: "Mainly clear",
            2: "Partly cloudy",
            3: "Overcast",
            45: "Foggy",
            48: "Foggy with rime",
            51: "Light drizzle",
            53: "Moderate drizzle",
            55: "Dense drizzle",
            61: "Slight rain",
            63: "Moderate rain",
            65: "Heavy rain",
            71: "Slight snow",
            73: "Moderate snow",
            75: "Heavy snow",
            80: "Slight rain showers",
            81: "Moderate rain showers",
            82: "Violent rain showers",
            85: "Slight snow showers",
            86: "Heavy snow showers",
            95: "Thunderstorm",
            96: "Thunderstorm with slight hail",
            99: "Thunderstorm with heavy hail",
        }
        weather_desc = weather_descriptions.get(weather_code, "Unknown")
        
        result_text = f"Raj, the weather in {city_name}, {country} is: {weather_desc} with {temp}°C temperature, {humidity}% humidity, and {wind_speed} km/h wind speed."
        return result_text
    
    except Exception as e:
        # Fallback to duckduckgo search
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(f"current weather temperature conditions in {location}", max_results=3))
            if results:
                return f"Raj, according to online reports for {location}: {results[0].get('body', '')}"
        except Exception:
            pass
        return f"Weather lookup failed for {location}, Raj. Please check spelling."

# IATA city codes for common Indian cities
CITY_CODES = {
    "mumbai": "BOM", "delhi": "DEL", "bangalore": "BLR", "bengaluru": "BLR",
    "hyderabad": "HYD", "chennai": "MAA", "kolkata": "CCU", "pune": "PNQ",
    "ahmedabad": "AMD", "goa": "GOI", "jaipur": "JAI", "lucknow": "LKO",
    "kochi": "COK", "cochin": "COK", "surat": "STV", "nagpur": "NAG",
    "indore": "IDR", "bhopal": "BHO", "patna": "PAT", "varanasi": "VNS",
    "new york": "JFK", "london": "LHR", "dubai": "DXB", "singapore": "SIN",
    "paris": "CDG", "tokyo": "NRT", "sydney": "SYD", "toronto": "YYZ",
}

def _get_city_code(city: str) -> str:
    return CITY_CODES.get(city.lower().strip(), city.upper().replace(" ", ""))

def _detect_intent(cmd: str):
    """Detect what kind of web query this is and return (intent, url, search_query)."""

    # --- Flights ---
    if any(w in cmd for w in ["flight", "flights", "fly", "airline", "airways"]):
        from_city, to_city, airline = "", "", ""
        for kw in ["from"]:
            if kw in cmd:
                part = cmd.split(kw)[-1].strip()
                for tk in ["to", "for"]:
                    if tk in part:
                        from_city = part.split(tk)[0].strip()
                        to_city = part.split(tk)[-1].strip()
                        break
        # Extract airline name
        for airline_kw in ["air india", "indigo", "spicejet", "vistara", "akasa", "go first", "air asia"]:
            if airline_kw in cmd:
                airline = airline_kw
                break
        from_code = _get_city_code(from_city) if from_city else ""
        to_code = _get_city_code(to_city) if to_city else ""
        if from_code and to_code:
            url = f"https://www.google.com/travel/flights?q=flights+from+{from_city.replace(' ','+')}+to+{to_city.replace(' ','+')}"
            if airline:
                url += f"+{airline.replace(' ', '+')}"
        else:
            url = f"https://www.google.com/travel/flights?q={cmd.replace(' ', '+')}"
        return ("flight", url, f"{airline+' ' if airline else ''}flights from {from_city} to {to_city}")

    # --- Instagram profile ---
    # Examples: "open instagram profile of avneetkaur_13", "open @avneetkaur_13", "instagram avneetkaur_13"
    insta_match = None
    # Prefer explicit @mention
    m_at = re.search(r'@([A-Za-z0-9_.]{2,30})', cmd)
    if m_at:
        insta_match = m_at.group(1)
    else:
        # look for the token after 'instagram' or 'insta'
        tokens = re.split(r'\s+', cmd)
        for i, t in enumerate(tokens):
            if t in ("instagram", "insta"):
                j = i + 1
                # skip common connector words like 'profile', 'of', 'user'
                while j < len(tokens) and tokens[j] in ("profile", "of", "user", "the", "show", "on"):
                    j += 1
                if j < len(tokens):
                    candidate = tokens[j].lstrip('@').strip('.,!?')
                    if re.fullmatch(r'[A-Za-z0-9_.]{2,30}', candidate):
                        insta_match = candidate
                        break

    if insta_match:
        url = f"https://www.instagram.com/{insta_match}/"
        return ("instagram", url, f"instagram profile {insta_match}")

    # --- YouTube episode (search by show + episode number) ---
    # Examples: "tmkoc episode no 126", "play tmkoc ep 126 on youtube"
    yt_m = re.search(r'([a-z0-9 &]+?)\s*(?:episode|ep)\s*(?:no\.?\s*)?(\d+)', cmd)
    if yt_m:
        show = yt_m.group(1).strip()
        # remove stray words and action verbs
        show = re.sub(r'\b(youtube|on youtube|on yt|play|open|watch|search for|search|the)\b', '', show).strip()
        num = yt_m.group(2)
        search_query = f"{show} episode {num}"
        url = f"https://www.youtube.com/results?search_query={search_query.replace(' ', '+')}"
        return ("youtube_episode", url, search_query)

    # --- Trains ---
    elif any(w in cmd for w in ["train", "trains", "railway", "irctc"]):
        from_city, to_city = "", ""
        if "from" in cmd:
            part = cmd.split("from")[-1].strip()
            for tk in ["to", "for"]:
                if tk in part:
                    from_city = part.split(tk)[0].strip()
                    to_city = part.split(tk)[-1].strip()
                    break
        url = f"https://www.irctc.co.in/nget/train-search" if not from_city else \
              f"https://www.google.com/search?q=trains+from+{from_city.replace(' ','+')}+to+{to_city.replace(' ','+')}"
        return ("train", url, f"trains from {from_city} to {to_city}")

    # --- Hotels ---
    elif any(w in cmd for w in ["hotel", "hotels", "stay", "accommodation", "resort"]):
        location = ""
        for kw in ["in", "at", "near"]:
            if kw in cmd:
                location = cmd.split(kw)[-1].strip()
                break
        url = f"https://www.google.com/travel/hotels?q=hotels+in+{location.replace(' ', '+')}" if location else \
              f"https://www.google.com/travel/hotels"
        return ("hotel", url, f"hotels in {location}")

    # --- Weather ---
    elif any(w in cmd for w in ["weather", "temperature", "forecast", "rain", "humidity"]):
        location = ""
        for kw in ["in", "at", "of", "for"]:
            if kw in cmd:
                location = cmd.split(kw)[-1].strip()
                break
        url = f"https://www.google.com/search?q=weather+{location.replace(' ', '+')}"
        return ("weather", url, f"weather in {location}")

    # --- Maps / Directions ---
    elif any(w in cmd for w in ["map", "maps", "direction", "directions", "navigate", "route", "how to reach", "how to go"]):
        destination = ""
        for kw in ["to", "of", "for", "navigate to", "directions to"]:
            if kw in cmd:
                destination = cmd.split(kw)[-1].strip()
                break
        url = f"https://www.google.com/maps/search/{destination.replace(' ', '+')}" if destination else \
              "https://www.google.com/maps"
        return ("map", url, f"directions to {destination}")

    # --- News ---
    elif any(w in cmd for w in ["news", "latest news", "headlines", "breaking"]):
        topic = ""
        for kw in ["about", "on", "of", "news"]:
            if kw in cmd:
                topic = cmd.split(kw)[-1].strip()
                break
        url = f"https://news.google.com/search?q={topic.replace(' ', '+')}" if topic else "https://news.google.com"
        return ("news", url, f"latest news about {topic}")

    # --- Shopping ---
    elif any(w in cmd for w in ["buy", "shop", "price", "amazon", "flipkart", "order"]):
        item = ""
        for kw in ["buy", "shop for", "price of", "order"]:
            if kw in cmd:
                item = cmd.split(kw)[-1].strip()
                break
        if "amazon" in cmd:
            url = f"https://www.amazon.in/s?k={item.replace(' ', '+')}"
        elif "flipkart" in cmd:
            url = f"https://www.flipkart.com/search?q={item.replace(' ', '+')}"
        else:
            url = f"https://www.google.com/search?q=buy+{item.replace(' ', '+')}"
        return ("shopping", url, f"buy {item}")

    # --- Generic web search ---
    else:
        clean = cmd
        for prefix in ["search for", "search", "who is", "what is the", "what is",
                       "news about", "price of", "tell me about", "how to", "define", "show me"]:
            if prefix in clean:
                clean = clean.split(prefix)[-1].strip()
                break
        url = f"https://www.google.com/search?q={clean.replace(' ', '+')}"
        return ("search", url, clean)


def web_search(query: str) -> tuple:
    """Returns (response_text, url_to_open)""" 
    try:
        cmd = query.lower().strip()
        intent, url, search_query = _detect_intent(cmd)

        # --- Special handler for weather ---
        if intent == "weather":
            location = search_query.replace("weather in ", "").replace("weather ", "")
            weather_result = _get_weather(location)
            return weather_result, url

        # Get live web context from DuckDuckGo
        web_context = ""
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(search_query, max_results=3))
            if results:
                web_context = " | ".join([r.get("body", "")[:200] for r in results])
        except:
            pass

        # Use Groq for smart spoken response
        api_key = os.getenv("GROQ_API_KEY", "")
        spoken = ""
        if api_key and api_key != "your_groq_api_key_here":
            client = Groq(api_key=api_key)
            intent_prompts = {
                "flight":   f"Summarize flight options for '{search_query}' in 2 sentences for Raj.",
                "train":    f"Summarize train options for '{search_query}' in 2 sentences for Raj.",
                "hotel":    f"Summarize hotel options for '{search_query}' in 2 sentences for Raj.",
                "weather":  f"Give a brief weather summary for '{search_query}' in 1-2 sentences for Raj.",
                "map":      f"Give brief directions info for '{search_query}' in 1-2 sentences for Raj.",
                "news":     f"Summarize the latest news about '{search_query}' in 2 sentences for Raj.",
                "shopping": f"Give a brief shopping summary for '{search_query}' in 1-2 sentences for Raj.",
                "search":   f"Answer '{search_query}' concisely in 2-3 sentences for Raj.",
                "instagram": f"Open the Instagram profile for '{search_query}' and give one-sentence summary for Raj.",
                "youtube_episode": f"Search YouTube for '{search_query}' and return the top result title in one sentence for Raj.",
            }
            prompt = intent_prompts.get(intent, f"Answer '{search_query}' concisely for Raj.")
            if web_context:
                prompt += f" Use this context: {web_context}"

            r = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": "You are JARVIS. Always start with 'Raj,' and be concise. Max 2 sentences."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=80  # short spoken summaries only
            )
            spoken = r.choices[0].message.content.strip()
        else:
            if intent == 'instagram':
                # search_query example: "instagram profile avneetkaur_13"
                spoken = f"Raj, opening Instagram profile {search_query.split()[-1]}."
            elif intent == 'youtube_episode':
                spoken = f"Raj, searching YouTube for {search_query}."
            else:
                spoken = f"Raj, opening {intent} results for {search_query}. Check the new tab."

        # Try to resolve exact YouTube video for episode queries
        if intent == 'youtube_episode' and url:
            try:
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
                r = requests.get(url, headers=headers, timeout=5)
                html = r.text
                # Try to find videoId in initial data
                m = re.search(r'"videoId"\s*:\s*"([A-Za-z0-9_-]{11})"', html)
                if not m:
                    # fallback: look for /watch?v= links
                    m2 = re.search(r'/watch\?v=([A-Za-z0-9_-]{11})', html)
                    if m2:
                        vid = m2.group(1)
                    else:
                        vid = None
                else:
                    vid = m.group(1)

                if vid:
                    video_url = f"https://www.youtube.com/watch?v={vid}"
                    spoken = f"Raj, opening YouTube episode {search_query}."
                    return spoken, video_url
            except Exception:
                # network or parsing failed — fall back to search results URL
                pass

        return spoken, url

    except Exception as e:
        return f"Raj, web search failed: {str(e)}", None

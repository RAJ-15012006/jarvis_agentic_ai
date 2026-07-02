import os
import requests
import yfinance as yf
from dotenv import load_dotenv

load_dotenv()

OWM_API_KEY  = os.getenv("OWM_API_KEY", "")
NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")

STOCK_SYMBOLS = {
    "reliance":    "RELIANCE.NS",
    "tcs":         "TCS.NS",
    "infosys":     "INFY.NS",
    "wipro":       "WIPRO.NS",
    "hdfc":        "HDFCBANK.NS",
    "hdfc bank":   "HDFCBANK.NS",
    "icici":       "ICICIBANK.NS",
    "icici bank":  "ICICIBANK.NS",
    "sbi":         "SBIN.NS",
    "bajaj":       "BAJFINANCE.NS",
    "adani":       "ADANIENT.NS",
    "tata motors": "TATAMOTORS.NS",
    "tata steel":  "TATASTEEL.NS",
    "airtel":      "BHARTIARTL.NS",
    "zomato":      "ZOMATO.NS",
    "paytm":       "PAYTM.NS",
    "nifty":       "^NSEI",
    "sensex":      "^BSESN",
    "apple":       "AAPL",
    "google":      "GOOGL",
    "microsoft":   "MSFT",
    "tesla":       "TSLA",
    "amazon":      "AMZN",
    "meta":        "META",
    "nvidia":      "NVDA",
    "bitcoin":     "BTC-USD",
    "ethereum":    "ETH-USD",
}

# Currency pairs — base INR
CURRENCY_MAP = {
    "dollar":      "USD",
    "usd":         "USD",
    "euro":        "EUR",
    "eur":         "EUR",
    "pound":       "GBP",
    "gbp":         "GBP",
    "yen":         "JPY",
    "jpy":         "JPY",
    "dirham":      "AED",
    "aed":         "AED",
    "riyal":       "SAR",
    "sar":         "SAR",
    "yuan":        "CNY",
    "cny":         "CNY",
    "canadian":    "CAD",
    "cad":         "CAD",
    "australian":  "AUD",
    "aud":         "AUD",
    "singapore":   "SGD",
    "sgd":         "SGD",
}

CITY_MAP = {
    "bangalore": "Bengaluru",
    "bengaluru": "Bengaluru",
    "bombay":    "Mumbai",
    "calcutta":  "Kolkata",
    "madras":    "Chennai",
}


def get_live_weather(city: str) -> str:
    city = CITY_MAP.get(city.lower().strip(), city.strip().title())
    if OWM_API_KEY and OWM_API_KEY != "your_openweathermap_api_key_here":
        try:
            url = (f"https://api.openweathermap.org/data/2.5/weather"
                   f"?q={city}&appid={OWM_API_KEY}&units=metric")
            r = requests.get(url, timeout=5)
            d = r.json()
            if d.get("cod") == 200:
                temp       = d["main"]["temp"]
                feels_like = d["main"]["feels_like"]
                humidity   = d["main"]["humidity"]
                desc       = d["weather"][0]["description"].capitalize()
                wind       = d["wind"]["speed"]
                return (f"Raj, live weather in {city}: {desc}, {temp:.1f}°C, "
                        f"feels like {feels_like:.1f}°C, humidity {humidity}%, wind {wind} m/s.")
        except Exception:
            pass
            
    # Keyless Fallback (Open-Meteo / DuckDuckGo search)
    try:
        from agents.web_agent import _get_weather
        return _get_weather(city)
    except Exception as e:
        return f"Raj, weather fetch failed for {city}: {str(e)}"


def _safe_get_price(ticker):
    """Safely fetch price and prev close, falling back to history if fast_info fails."""
    try:
        price = ticker.fast_info.last_price
        prev  = ticker.fast_info.previous_close
        return price, prev
    except Exception:
        hist = ticker.history(period="5d")
        if len(hist) > 0:
            price = hist["Close"].iloc[-1]
            prev  = hist["Close"].iloc[-2] if len(hist) > 1 else price
            return price, prev
        return 0.0, 0.0

def get_live_stock(query: str) -> str:
    query_lower = query.lower().strip()
    symbol = next((v for k, v in STOCK_SYMBOLS.items() if k in query_lower), None)
    if not symbol:
        symbol = query_lower.upper().replace(" ", "") + ".NS"
    try:
        ticker    = yf.Ticker(symbol)
        price, prev = _safe_get_price(ticker)
        
        change    = price - prev
        pct       = (change / prev) * 100 if prev else 0
        direction = "up" if change >= 0 else "down"
        name      = symbol.replace(".NS", "").replace("-USD", "").replace("^", "")
        currency  = "Rs." if ".NS" in symbol else "$"
        return (f"Raj, {name} is at {currency}{price:,.2f}, "
                f"{direction} {abs(change):.2f} ({abs(pct):.2f}%) from yesterday.")
    except Exception as e:
        return f"Raj, I couldn't fetch the stock price: {str(e)}"


def get_live_currency(query: str) -> str:
    """Get live currency rate against INR using yfinance."""
    cmd = query.lower()
    currency_code = next((v for k, v in CURRENCY_MAP.items() if k in cmd), None)
    if not currency_code:
        return "Raj, I couldn't identify the currency. Try saying dollar rate or euro rate."
    try:
        ticker = yf.Ticker(f"{currency_code}INR=X")
        rate, _ = _safe_get_price(ticker)
        return f"Raj, 1 {currency_code} = Rs.{rate:.2f} Indian Rupees right now."
    except Exception as e:
        return f"Raj, currency fetch failed: {str(e)}"


def get_gold_price() -> str:
    """Get live gold price in INR per 10 grams using yfinance."""
    try:
        # GC=F is gold futures in USD per troy ounce
        ticker    = yf.Ticker("GC=F")
        usd_oz, _ = _safe_get_price(ticker)

        # Convert to INR per 10 grams
        # 1 troy oz = 31.1035 grams
        usd_10g   = (usd_oz / 31.1035) * 10

        # Get USD to INR rate
        inr_rate, _ = _safe_get_price(yf.Ticker("USDINR=X"))
        inr_10g   = usd_10g * inr_rate

        return (f"Raj, live gold price: Rs.{inr_10g:,.0f} per 10 grams "
                f"(${usd_oz:,.0f} per troy ounce internationally).")
    except Exception as e:
        return f"Raj, gold price fetch failed: {str(e)}"


def get_live_news(topic: str = "") -> str:
    """Fetch top news headlines using NewsAPI or RSS fallback."""
    try:
        if NEWS_API_KEY:
            if topic:
                url = (f"https://newsapi.org/v2/everything?q={topic.replace(' ', '+')}"
                       f"&sortBy=publishedAt&pageSize=3&apiKey={NEWS_API_KEY}")
            else:
                url = (f"https://newsapi.org/v2/top-headlines?country=in"
                       f"&pageSize=3&apiKey={NEWS_API_KEY}")
            r    = requests.get(url, timeout=5)
            data = r.json()
            articles = data.get("articles", [])
            if articles:
                headlines = [a["title"] for a in articles[:3] if a.get("title")]
                return "Raj, top headlines: " + " | ".join(headlines)

        # Fallback — Google News RSS (no key needed)
        query = topic.replace(" ", "+") if topic else "India"
        rss   = f"https://news.google.com/rss/search?q={query}&hl=en-IN&gl=IN&ceid=IN:en"
        r     = requests.get(rss, timeout=5)
        import xml.etree.ElementTree as ET
        root  = ET.fromstring(r.content)
        items = root.findall(".//item")[:3]
        headlines = [item.find("title").text for item in items if item.find("title") is not None]
        if headlines:
            return "Raj, top headlines: " + " | ".join(headlines)
        return "Raj, no news found right now."

    except Exception as e:
        return f"Raj, news fetch failed: {str(e)}"


IPL_TEAMS = {
    "lsg":  "lucknow super giants",
    "lucknow": "lucknow super giants",
    "csk":  "chennai super kings",
    "chennai": "chennai super kings",
    "mi":   "mumbai indians",
    "mumbai": "mumbai indians",
    "rcb":  "royal challengers bengaluru",
    "bangalore": "royal challengers bengaluru",
    "bengaluru": "royal challengers bengaluru",
    "kkr":  "kolkata knight riders",
    "kolkata": "kolkata knight riders",
    "dc":   "delhi capitals",
    "delhi": "delhi capitals",
    "srh":  "sunrisers hyderabad",
    "hyderabad": "sunrisers hyderabad",
    "pbks": "punjab kings",
    "punjab": "punjab kings",
    "rr":   "rajasthan royals",
    "rajasthan": "rajasthan royals",
    "gt":   "gujarat titans",
    "gujarat": "gujarat titans",
}

def get_live_cricket(team_query: str = "") -> str:
    try:
        # Try cricapi first
        r    = requests.get("https://api.cricapi.com/v1/currentMatches?apikey=free&offset=0", timeout=5)
        data = r.json()
        matches = data.get("data", [])

        if matches:
            lines = []
            for m in matches[:5]:
                name   = m.get("name", "Match")
                status = m.get("status", "")
                score  = m.get("score", [])
                score_str = " | ".join(
                    [f"{s.get('inning','')}: {s.get('r','0')}/{s.get('w','0')} ({s.get('o','0')} ov)"
                     for s in score]
                ) if score else ""
                # Filter by team if specified
                if team_query and team_query.lower() not in name.lower():
                    continue
                lines.append(f"{name} — {score_str} — {status}")

            if lines:
                return "Raj, live cricket: " + " || ".join(lines)

        # Fallback — scrape Google search snippet
        search_term = f"{team_query} ipl score today" if team_query else "ipl live score today"
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(
            f"https://www.google.com/search?q={search_term.replace(' ', '+')}",
            headers=headers, timeout=5
        )
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(res.text, "html.parser")

        # Google shows score in a featured snippet or sports card
        score_divs = soup.find_all("div", class_="BNeawe")
        snippets = [d.get_text() for d in score_divs if any(
            kw in d.get_text().lower() for kw in ["over", "run", "/", "wicket", "batting", "bowling"]
        )]
        if snippets:
            return f"Raj, {search_term}: {snippets[0]}"

        return f"Raj, couldn't find live score for {team_query or 'IPL'} right now."

    except Exception as e:
        return f"Raj, cricket score fetch failed: {str(e)}"


def handle_live_query(command: str) -> str:
    cmd = command.lower()

    def contains_any(text: str, kws) -> bool:
        import re
        for w in kws:
            if re.search(r"\b" + re.escape(w) + r"\b", text):
                return True
        return False

    # Weather
    if contains_any(cmd, ["weather", "temperature", "forecast", "rain", "humidity"]):
        city = "Vadodara"
        for kw in ["in", "at", "of", "for"]:
            if f" {kw} " in cmd:
                candidate = cmd.split(f" {kw} ")[-1].strip()
                for noise in ["today", "now", "current", "live", "outside", "please"]:
                    candidate = candidate.replace(noise, "").strip()
                if candidate:
                    city = candidate
                    break
        return get_live_weather(city)

    # Gold price
    if contains_any(cmd, ["gold price", "gold rate", "gold today", "price of gold",
                               "silver price", "silver rate"]):
        if "silver" in cmd:
            try:
                usd_oz, _ = _safe_get_price(yf.Ticker("SI=F"))
                inr, _    = _safe_get_price(yf.Ticker("USDINR=X"))
                inr_kg = (usd_oz / 31.1035) * 1000 * inr
                return f"Raj, silver price is Rs.{inr_kg:,.0f} per kg right now."
            except Exception as e:
                return f"Raj, silver price fetch failed: {str(e)}"
        return get_gold_price()

    # Currency rates
    if contains_any(cmd, ["currency", "exchange rate", "exchange", "rupee to", "inr rate",
                               "dollar rate", "dollar price", "euro rate", "pound rate",
                               "yen rate", "dirham rate", "riyal rate", "yuan rate", "forex"]):
        return get_live_currency(cmd)

    # News
    if contains_any(cmd, ["news", "headlines", "latest news", "top news",
                               "what is happening", "current events", "briefing"]):
        topic = ""
        for kw in ["about", "on", "for", "related to"]:
            if kw in cmd:
                candidate = cmd.split(kw)[-1].strip()
                for noise in ["news", "headlines", "today", "latest", "please"]:
                    candidate = candidate.replace(noise, "").strip()
                if candidate:
                    topic = candidate
                    break
        return get_live_news(topic)

    # Stocks
    if contains_any(cmd, ["stock", "share", "market", "nifty", "sensex",
                               "bitcoin", "crypto", "ethereum"]):
        return get_live_stock(cmd)

    # Cricket
    if contains_any(cmd, ["cricket", "ipl score", "ipl match", "match score", "live score",
                               "cricket score", "who is batting", "live match", "live cricket"]):
        # Detect team name
        team = ""
        for short, full in IPL_TEAMS.items():
            if short in cmd.split() or full in cmd:
                team = full
                break
        return get_live_cricket(team)

    return ""

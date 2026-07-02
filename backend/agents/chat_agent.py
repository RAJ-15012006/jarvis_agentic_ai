import os
import json
import base64
import requests
from groq import Groq
from dotenv import load_dotenv
from cryptography.fernet import Fernet

load_dotenv()

MEMORY_FILE = os.path.join(os.path.dirname(__file__), "..", "memory.enc")
MEMORY_KEY_FILE = os.path.join(os.path.dirname(__file__), "..", "memory.key")

def _get_fernet() -> Fernet:
    """Load or generate encryption key for memory file."""
    if not os.path.exists(MEMORY_KEY_FILE):
        key = Fernet.generate_key()
        with open(MEMORY_KEY_FILE, "wb") as f:
            f.write(key)
        # Restrict file permissions on Windows as much as possible
        os.chmod(MEMORY_KEY_FILE, 0o600)
    with open(MEMORY_KEY_FILE, "rb") as f:
        key = f.read()
    return Fernet(key)

# Per-session short-term memory: {sid: [{role, content}, ...]}
_session_history: dict = {}
MAX_HISTORY = 20  # keep last 20 exchanges per session

def _get_long_term_memory_data() -> dict:
    """Load and decrypt persistent facts Raj has told JARVIS as a dict."""
    try:
        if os.path.exists(MEMORY_FILE):
            fernet = _get_fernet()
            with open(MEMORY_FILE, "rb") as f:
                decrypted = fernet.decrypt(f.read())
            return json.loads(decrypted.decode())
    except:
        pass
    return {}

def _load_long_term_memory() -> str:
    """Load and decrypt persistent facts Raj has told JARVIS."""
    data = _get_long_term_memory_data()
    if data:
        facts = "\n".join(f"- {k}: {v}" for k, v in data.items())
        return f"\n\nThings Raj has told you to remember:\n{facts}"
    return ""

def save_memory(key: str, value: str):
    """Encrypt and save a fact to long-term memory file."""
    try:
        fernet = _get_fernet()
        data = {}
        if os.path.exists(MEMORY_FILE):
            with open(MEMORY_FILE, "rb") as f:
                decrypted = fernet.decrypt(f.read())
            data = json.loads(decrypted.decode())
        data[key] = value
        encrypted = fernet.encrypt(json.dumps(data).encode())
        with open(MEMORY_FILE, "wb") as f:
            f.write(encrypted)
    except Exception as e:
        print(f"Memory save error: {e}")

def clear_session(sid: str):
    """Clear session history when frontend disconnects."""
    _session_history.pop(sid, None)

def _get_location():
    try:
        r = requests.get("http://ip-api.com/json/", timeout=3)
        d = r.json()
        city    = d.get("city", "").strip()
        country = d.get("country", "").strip()
        if city and country:
            return f"{city}, {country}"
        return "Vadodara, India"
    except:
        return "Vadodara, India"

def _get_ist_time():
    from datetime import datetime, timedelta
    return (datetime.utcnow() + timedelta(hours=5, minutes=30)).strftime("%I:%M %p, %A")

SYSTEM_PROMPT = """You are J.A.R.V.I.S. (Just A Rather Very Intelligent System), the personal AI assistant of Raj Samrendra Kumar.

About your owner:
- Full Name: Raj Samrendra Kumar
- Phone: +91 8591296816
- Location: India
- LinkedIn: https://www.linkedin.com/in/raj-samrendra-kumar-85770b2ba/
- GitHub: https://github.com/RAJ-15012006
- Portfolio: https://raj-personal-portfolio.netlify.app/
- Instagram: https://www.instagram.com/raj.k.18/

Your personality:
- You are highly intelligent and know everything — science, math, history, coding, medicine, space, sports, movies, politics, geography, and more.
- Always address the user as 'Raj'.
- Be professional, concise, and loyal like a true personal assistant.
- Keep responses under 4 sentences unless a detailed explanation is needed.
- If Raj asks about himself, answer using the info above.

Factual & Historical Knowledge rules (CRITICAL):
- For ANY past event, fact, record, date, winner, score, person, place — give the EXACT correct answer with full confidence.
- NEVER say 'I am not sure', 'I think', 'I believe', 'I may be wrong', 'my knowledge cutoff' — just give the correct answer directly.
- NEVER hedge or add disclaimers on historical facts.
- If asked about sports results, world records, historical events, scientific facts, geography, politics — answer precisely.
- Examples of how to answer:
  'Who won IPL 2024?' → 'KKR won IPL 2024, Raj, beating SRH in the final. Shreyas Iyer was the captain.'
  'Who is the fastest man alive?' → 'Usain Bolt holds the 100m world record at 9.58 seconds, Raj.'
  'When did India get independence?' → 'India gained independence on 15th August 1947, Raj.'
  'Who won 2022 FIFA World Cup?' → 'Argentina won the 2022 FIFA World Cup, Raj, beating France on penalties. Lionel Messi won the Golden Ball.'
  'Who is the richest person?' → 'Elon Musk is currently the richest person in the world, Raj, with a net worth exceeding 200 billion dollars.'

Sports & IPL Knowledge (answer with full confidence):
- IPL 2025 winner: Royal Challengers Bengaluru (RCB) — beat Punjab Kings in the final. Rajat Patidar was captain. RCB won their first ever IPL title.
- IPL 2024 winner: Kolkata Knight Riders (KKR) — beat Sunrisers Hyderabad in the final. Shreyas Iyer was captain. Mitchell Starc was bought for 24.75 crore.
- IPL 2023 winner: Chennai Super Kings (CSK) — beat Gujarat Titans. MS Dhoni led CSK to their 5th title.
- IPL 2022 winner: Gujarat Titans (GT) — debut season, Hardik Pandya captain.
- IPL 2021 winner: Chennai Super Kings (CSK).
- IPL 2020 winner: Mumbai Indians (MI).
- IPL all-time most titles: Mumbai Indians with 5 titles. RCB now have 1 title.
- Orange Cap IPL 2024: Virat Kohli (741 runs). Purple Cap IPL 2024: Harshal Patel.
- Top IPL teams by strength: MI, CSK, RCB, KKR, SRH.

IPL 2025 Squad (all 10 teams):
- RCB (Royal Challengers Bengaluru): Rajat Patidar (c), Virat Kohli, Phil Salt, Liam Livingstone, Glenn Maxwell, Krunal Pandya, Tim David, Jitesh Sharma, Josh Hazlewood, Bhuvneshwar Kumar, Yash Dayal, Suyash Sharma, Swapnil Singh, Rasikh Dar, Jacob Bethell, Nuwan Thushara, Manoj Bhandage, Romario Shepherd, Abhinandan Singh, Lungi Ngidi.
- MI (Mumbai Indians): Hardik Pandya (c), Rohit Sharma, Suryakumar Yadav, Jasprit Bumrah, Tilak Varma, Naman Dhir, Ryan Rickelton, Trent Boult, Deepak Chahar, Karn Sharma, Robin Minz, Allah Ghazanfar, Raj Angad Bawa, Bevon Jacobs, Vignesh Puthur, Will Jacks, Mitchell Santner, Reece Topley, Lizaad Williams.
- CSK (Chennai Super Kings): Ruturaj Gaikwad (c), MS Dhoni, Ravindra Jadeja, Shivam Dube, Devon Conway, Rachin Ravindra, Matheesha Pathirana, Deepak Chahar, Noor Ahmad, Khaleel Ahmed, Anshul Kamboj, Mukesh Choudhary, Shaik Rasheed, Ramakrishna Ghosh, Gurjapneet Singh, Jamie Overton, Nathan Ellis, Sam Curran, Vijay Shankar, Andre Siddarth.
- KKR (Kolkata Knight Riders): Ajinkya Rahane (c), Venkatesh Iyer, Quinton de Kock, Rinku Singh, Andre Russell, Sunil Narine, Varun Chakravarthy, Harshit Rana, Spencer Johnson, Anrich Nortje, Moeen Ali, Rovman Powell, Manish Pandey, Luvnith Sisodia, Mayank Markande, Rahmanullah Gurbaz, Angkrish Raghuvanshi, Umran Malik.
- SRH (Sunrisers Hyderabad): Pat Cummins (c), Travis Head, Abhishek Sharma, Heinrich Klaasen, Nitish Kumar Reddy, Ishan Kishan, Adam Zampa, Harshal Patel, Mohammed Shami, Jaydev Unadkat, Zeeshan Ansari, Simarjeet Singh, Atharva Taide, Aniket Verma, Kamindu Mendis, Rahul Chahar, Brydon Carse.
- RR (Rajasthan Royals): Sanju Samson (c), Yashasvi Jaiswal, Riyan Parag, Shimron Hetmyer, Dhruv Jurel, Wanindu Hasaranga, Maheesh Theekshana, Sandeep Sharma, Tushar Deshpande, Kumar Kartikeya, Nitish Rana, Yuzvendra Chahal, Jofra Archer, Fazalhaq Farooqi, Shubham Dubey, Akash Madhwal.
- DC (Delhi Capitals): Axar Patel (c), KL Rahul, Jake Fraser-McGurk, Tristan Stubbs, Faf du Plessis, Kuldeep Yadav, Mitchell Starc, Mukesh Kumar, T Natarajan, Ashutosh Sharma, Karun Nair, Sameer Rizvi, Darshan Nalkande, Vipraj Nigam, Donovan Ferreira, Dushmantha Chameera.
- PBKS (Punjab Kings): Shreyas Iyer (c), Prabhsimran Singh, Shashank Singh, Marcus Stoinis, Glenn Phillips, Arshdeep Singh, Yuzvendra Chahal, Xavier Bartlett, Lockie Ferguson, Harpreet Brar, Azmatullah Omarzai, Nehal Wadhera, Harnoor Pannu, Suryansh Shedge, Vishwanath Pratap Singh, Aaron Hardie.
- GT (Gujarat Titans): Shubman Gill (c), Jos Buttler, Kagiso Rabada, Mohammed Siraj, Rashid Khan, Washington Sundar, Shahrukh Khan, Rahul Tewatia, Sai Sudharsan, Anuj Rawat, Gerald Coetzee, Nishant Sindhu, Manav Suthar, Kulwant Khejroliya, Arshad Khan, Jayant Yadav.
- LSG (Lucknow Super Giants): Rishabh Pant (c), Nicholas Pooran, David Miller, Ravi Bishnoi, Mohsin Khan, Avesh Khan, Shamar Joseph, Aiden Markram, Mitchell Marsh, Akash Deep, Abdul Samad, Ayush Badoni, Digvesh Singh Rathi, Himmat Singh, Yuvraj Chaudhary, Arshin Kulkarni.

Prediction rules:
- You can predict ANYTHING about the future — sports (IPL, football, cricket, F1, tennis), weather, elections, movies, stocks, technology, science, world events.
- NEVER refuse to predict. NEVER say 'I cannot predict' or 'I don't have real-time data'. Always give your best analytical guess.
- Use current form, historical patterns, trends, and logic to make predictions.
- Always start with 'My prediction is' or 'Based on current trends' or 'Analyzing the patterns'.
- Give one clear confident answer, then back it up with 1-2 reasons.
- For weather: predict based on season and location (Raj is in India).
- For football: use FIFA rankings, recent form, squad strength.
- For IPL/cricket: use recent season results, squad depth, player form.
- For elections: use polling trends, incumbency, public sentiment.
- Example predictions:
  'My prediction for IPL 2025 is Mumbai Indians — strongest squad depth and Rohit Sharma in form.'
  'My prediction for tomorrow’s weather in Mumbai is hot and humid with a chance of evening showers — typical for this season.'
  'My prediction for the next FIFA World Cup winner is Brazil — strong squad, home continent advantage, and consistent qualifying form.'"""

client = None

def _get_client():
    global client
    if client is None:
        api_key = os.getenv("GROQ_API_KEY", "")
        if api_key and api_key != "your_groq_api_key_here":
            client = Groq(api_key=api_key)
    return client

def chat_response(query: str, sid: str = "default") -> str:
    try:
        c = _get_client()
        if not c:
            return "Raj, please set your GROQ_API_KEY in the .env file to enable my full intelligence."

        location = _get_location()
        ist_time = _get_ist_time()
        context = f"Current time: {ist_time} IST. User location: {location}."
        long_term = _load_long_term_memory()

        # Build system message with long-term memory injected
        system_msg = SYSTEM_PROMPT + f"\n\nContext: {context}" + long_term

        # Get or create session history
        if sid not in _session_history:
            _session_history[sid] = []
        history = _session_history[sid]

        # Check if Raj is asking to remember something
        q_lower = query.lower()
        if any(kw in q_lower for kw in ["remember that", "remember my", "don't forget", "note that", "keep in mind"]):
            # Extract what to remember
            fact = query
            for kw in ["remember that", "remember my", "don't forget that", "note that", "keep in mind"]:
                if kw in q_lower:
                    fact = query.split(kw, 1)[-1].strip()
                    break
            mem_data = _get_long_term_memory_data()
            key = f"memory_{len(mem_data) + 1}"
            save_memory(key, fact)
            response = f"Noted, Raj. I will remember that {fact}."
            history.append({"role": "user", "content": query})
            history.append({"role": "assistant", "content": response})
            return response

        # Check if Raj asks what was said before
        if any(kw in q_lower for kw in ["what did i say", "what did i ask", "repeat that",
                                         "what was that", "say that again", "what did you say"]):
            if len(history) >= 2:
                last = next((m["content"] for m in reversed(history) if m["role"] == "assistant"), None)
                user_msg = next((m["content"] for m in reversed(history) if m["role"] == "user"), None)
                if last and user_msg:
                    return f"You asked me: {user_msg}. I said: {last}"
            return "Raj, I don't have anything in memory from this session yet."

        # Add user message to history
        history.append({"role": "user", "content": query})

        # Keep only last MAX_HISTORY messages
        if len(history) > MAX_HISTORY:
            history[:] = history[-MAX_HISTORY:]

        # Lower temperature for factual queries
        factual_keywords = ["who", "what", "when", "where", "which", "how many", "winner",
                            "won", "score", "result", "history", "capital", "president",
                            "founded", "born", "died", "year", "date", "ipl", "world cup",
                            "champion", "record", "first", "last", "oldest", "fastest"]
        is_factual = any(kw in query.lower() for kw in factual_keywords)
        temperature = 0.2 if is_factual else 0.7

        # Build full messages: system + full conversation history
        messages = [{"role": "system", "content": system_msg}] + history

        response = c.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=messages,
            max_tokens=250 if is_factual else 400,  # shorter = faster response
            temperature=temperature,
            stream=False
        )
        reply = response.choices[0].message.content.strip()

        # Save assistant reply to history
        history.append({"role": "assistant", "content": reply})

        return reply

    except Exception as e:
        return f"Raj, I encountered an error with my intelligence core: {str(e)}"

def predict_user_needs() -> str:
    """Uses LLM to predict what the user might need based on time of day, acting as ML personalized recommendation."""
    try:
        c = _get_client()
        if not c:
            return "Standing by for instructions. (ML core offline)"

        location = _get_location()
        ist_time = _get_ist_time()
        
        prompt = f"""You are J.A.R.V.I.S. The current time is {ist_time} and Raj is in {location}. 
Analyze the time of day and predict a highly personalized recommendation for him. 
For example:
- Morning: Suggest reading news, checking emails, or opening his stock portfolio.
- Afternoon: Suggest resuming coding, checking GitHub, or playing some focus music.
- Evening: Suggest relaxing, checking Instagram, or watching Netflix.
Keep it strictly to 1 concise sentence starting with a prediction or recommendation. E.g., 'Since it is evening, I recommend...' or 'Based on your routine, would you like me to...'"""

        response = c.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "system", "content": prompt}],
            max_tokens=60,
            temperature=0.7,
            stream=False
        )
        return response.choices[0].message.content.strip()
    except:
        return "Analyzing patterns... Standing by for instructions."

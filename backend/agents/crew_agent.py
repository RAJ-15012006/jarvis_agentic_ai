import os
from duckduckgo_search import DDGS
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

def run_tech_digest_crew(topic: str = "AI and technology") -> str:
    """Executes a collaborative multi-agent workflow:
    1. Researcher Agent: Scrapes and finds the latest articles about the topic.
    2. Writer Agent: Synthesizes the raw search logs into a beautifully structured Markdown newsletter.
    """
    api_key = os.getenv("GROQ_API_KEY", "")
    if not api_key or api_key == "your_groq_api_key_here":
        return "Raj, I need a valid Groq API key to spin up the Collaborative Crew."

    client = Groq(api_key=api_key)

    # 1. Researcher Agent Work
    print(f"[Crew] Initializing Researcher Agent to search for: {topic}...")
    search_results = []
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(f"latest updates on {topic}", max_results=5))
            for r in results:
                search_results.append(f"Title: {r.get('title')}\nSnippet: {r.get('body')}\nLink: {r.get('href')}\n---")
    except Exception as e:
        search_results = [f"Search failed: {str(e)}"]

    research_payload = "\n".join(search_results)

    # 2. Writer Agent Work
    print("[Crew] Passing research data to Writer Agent for synthesis...")
    writer_prompt = f"""
    You are a professional Tech Newsletter Writer Agent.
    Your task is to take the following raw search logs gathered by the Researcher Agent and compile them into a highly engaging, professional weekly tech newsletter digest.

    Raw Research Logs:
    {research_payload}

    Requirements:
    1. Title: Create a catchy, futuristic header (e.g. "J.A.R.V.I.S. INTELLIGENCE DEBRIEF: {topic.upper()}").
    2. Sections: Group the findings into 2-3 logical categories.
    3. Formatting: Use extremely clean Markdown, bold highlights, bullets, and include links if provided.
    4. Tone: Intellectual, futuristic, concise, and addressed to "Sir" (Raj).
    5. Include an "Editor's Insight" section summarizing what this means for the future.

    Write the final polished markdown newsletter now:
    """

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "You are a professional tech editor. Address the user as 'Sir' or 'Raj'."},
                {"role": "user", "content": writer_prompt}
            ],
            temperature=0.3
        )
        newsletter_markdown = response.choices[0].message.content.strip()

        # Save to local public directory so the frontend can display it
        output_dir = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "public")
        os.makedirs(output_dir, exist_ok=True)
        file_path = os.path.join(output_dir, "newsletter.md")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(newsletter_markdown)

        return newsletter_markdown
    except Exception as e:
        return f"Raj, the Writer Agent encountered an error: {str(e)}"

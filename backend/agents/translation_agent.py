"""
translation_agent.py — JARVIS Real-Time Language Translation
=============================================================
Translates any text to/from any language using LLaMA via Groq.
No external API keys beyond Groq needed.

Voice commands:
  - "translate [text] to Hindi"
  - "translate this to Spanish"
  - "what does [word] mean in Japanese"
  - "say [phrase] in French"
  - "translate this page" (translates last webpage content)
  - "JARVIS baat kar Hindi mein" → responds in Hindi
"""

import os
import re

TRANSLATION_TRIGGERS = [
    "translate", "in hindi", "in spanish", "in french", "in japanese",
    "in german", "in italian", "in arabic", "in chinese", "in korean",
    "in tamil", "in telugu", "in bengali", "in gujarati", "in marathi",
    "in punjabi", "in urdu", "in russian", "in portuguese",
    "what does", "how do you say", "say it in", "baat kar", "bolna",
    "language", "translation", "convert to", "speak in",
]

LANGUAGE_MAP = {
    "hindi": "Hindi", "spanish": "Spanish", "french": "French",
    "japanese": "Japanese", "german": "German", "italian": "Italian",
    "arabic": "Arabic", "chinese": "Chinese (Simplified)", "korean": "Korean",
    "tamil": "Tamil", "telugu": "Telugu", "bengali": "Bengali",
    "gujarati": "Gujarati", "marathi": "Marathi", "punjabi": "Punjabi",
    "urdu": "Urdu", "russian": "Russian", "portuguese": "Portuguese",
    "dutch": "Dutch", "swedish": "Swedish", "turkish": "Turkish",
    "thai": "Thai", "vietnamese": "Vietnamese", "greek": "Greek",
    "english": "English", "kannada": "Kannada", "malayalam": "Malayalam",
}

def is_translation_command(command: str) -> bool:
    cmd = command.lower()
    return any(t in cmd for t in TRANSLATION_TRIGGERS)


def _detect_target_language(command: str) -> str:
    """Extract the target language from the command."""
    cmd = command.lower()
    for key, lang in LANGUAGE_MAP.items():
        if key in cmd:
            return lang
    return "Hindi"  # default


def _extract_text_to_translate(command: str) -> str:
    """Extract the text to be translated from the command."""
    cmd = command.lower()

    # Patterns: "translate [TEXT] to [LANG]", "say [TEXT] in [LANG]"
    for pattern in [
        r"translate (.+?) to \w+",
        r"translate (.+?) in \w+",
        r"say (.+?) in \w+",
        r"how do you say (.+?) in",
        r"what is (.+?) in \w+",
    ]:
        match = re.search(pattern, cmd)
        if match:
            return match.group(1).strip()

    # Remove translation command words to get the text
    for noise in list(LANGUAGE_MAP.keys()) + [
        "translate", "translation", "to", "in", "say it", "convert",
        "hindi mein", "baat kar", "bolna", "language", "speak in",
    ]:
        cmd = cmd.replace(noise, " ").strip()

    return re.sub(r"\s+", " ", cmd).strip()


def translate_text(text: str, target_language: str, source_language: str = "auto") -> str:
    """
    Translate text using LLaMA via Groq.
    """
    api_key = os.getenv("GROQ_API_KEY", "")
    if not api_key:
        return "Raj, Groq API key is required for translation."

    if not text or len(text.strip()) < 2:
        return "Raj, please provide some text to translate."

    try:
        from groq import Groq
        client = Groq(api_key=api_key)

        system_prompt = (
            "You are a professional multilingual translator. "
            "Translate the given text accurately and naturally. "
            "Provide ONLY the translation, nothing else — no explanations, no notes, no formatting. "
            "If translating to a script-based language (Hindi, Arabic, etc.), include both the script and a romanized pronunciation."
        )

        if source_language == "auto":
            user_prompt = f"Translate the following to {target_language}:\n\n{text}"
        else:
            user_prompt = f"Translate from {source_language} to {target_language}:\n\n{text}"

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1,
            max_tokens=500
        )

        translation = response.choices[0].message.content.strip()
        return f"🌐 Translation to {target_language}:\n\n{translation}"

    except Exception as e:
        return f"Raj, translation failed: {str(e)}"


def translate_command(command: str) -> str:
    """Main entry point for translation voice commands."""
    target_lang = _detect_target_language(command)
    text = _extract_text_to_translate(command)

    if not text:
        return f"Raj, please tell me what to translate to {target_lang}."

    return translate_text(text, target_lang)


def translate_bulk_text(text: str, target_language: str) -> str:
    """Translate a large block of text (for page translation etc.)"""
    # Break into chunks if too long
    MAX_CHUNK = 2000
    if len(text) <= MAX_CHUNK:
        return translate_text(text, target_language)

    chunks = [text[i:i+MAX_CHUNK] for i in range(0, len(text), MAX_CHUNK)]
    translations = []
    for chunk in chunks[:5]:  # Limit to 5 chunks
        result = translate_text(chunk, target_language)
        translations.append(result.replace(f"🌐 Translation to {target_language}:\n\n", ""))

    return f"🌐 Page Translation to {target_language}:\n\n" + "\n\n".join(translations)

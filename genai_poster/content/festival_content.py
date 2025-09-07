from __future__ import annotations
import datetime as dt
from typing import List, Optional
from ics import Calendar
import requests
from genai_poster.models import FestivalInfo
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

def fetch_festivals_from_calendar(url: str) -> List[FestivalInfo]:
    """
    Fetch events from an ICS calendar (public URL or local file) and convert to FestivalInfo list.
    """
    if url.startswith("http"):
        r = requests.get(url)
        r.raise_for_status()
        data = r.text
    else:
        with open(url, "r", encoding="utf-8") as f:
            data = f.read()

    cal = Calendar(data)
    festivals: List[FestivalInfo] = []
    for event in cal.events:
        if not event.begin:
            continue
        date = event.begin.date()
        festivals.append(FestivalInfo(
            name=event.name,
            date=date,
            region=None,
            emoji=None,
            colors=None,
        ))
    return festivals

def get_upcoming_festival(today: dt.date, calendar_url: str) -> Optional[FestivalInfo]:
    festivals = fetch_festivals_from_calendar(calendar_url)
    upcoming = [f for f in festivals if f.date >= today]
    if not upcoming:
        return None
    upcoming.sort(key=lambda f: f.date)
    return upcoming[1]

def make_llm(model: str) -> ChatOpenAI:
    return ChatOpenAI(model=model, temperature=0.7)

POST_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     """You are a world-class creative director and social media strategist, specializing in crafting emotionally resonant and culturally aware content for a discerning professional audience on LinkedIn.

Your mission is to create posts that are:
- **Authentic & Original:** Free from plagiarism, ethically responsible, and written with a unique voice.
- **Culturally Sensitive:** Inclusive, positive, and devoid of stereotypes or clichés. Your work celebrates diversity and fosters a sense of community.
- **Engaging & Professional:** Crisp, compelling (100-180 words), and written in flawless British/Indian English.
- **Visually Appealing:** Enhanced with 1-3 tasteful emojis and 3-5 highly relevant hashtags that amplify the message.

Your writing should always reflect the brand’s core values and tone, prioritizing authenticity, cultural nuance, and relevance to a modern professional audience across India."""),
    
    ("human",
     """Craft a LinkedIn post for the upcoming festival, following these creative guidelines:

**Festival:** {festival_name}
**Date:** {festival_date}
**Emoji:** {festival_emoji}

**Company Information:**
- **Brand:** {brand_name}
- **Tone:** {brand_tone}

**Suggested Hashtags:** {hashtags}

**Research:**
{search_results}

**Creative Mandate:**
1.  **The Hook (1-2 lines):** Start with a powerful, thought-provoking opening that captures the essence of the festival, informed by the research provided.
2.  **The Insight (3-4 lines):** Share a practical, inspiring insight on how professionals can integrate the festival's spirit into their work or personal growth, using details from the research and tailoring it to the company's industry and profile.
3.  **The Call-to-Action (1 line):** End with a warm, inviting CTA that encourages engagement (e.g., sharing stories, reflections, or visiting a link).

**Crucially, ensure your content is original, culturally respectful, and aligns with the highest professional and ethical standards."""),
])


BANNER_PROMPT_TMPL = """Create a visually stunning, clean, and modern LinkedIn banner that celebrates {festival_name} for a sophisticated Indian professional audience. The design should be a masterpiece of minimalist elegance, blending cultural authenticity with a contemporary corporate aesthetic.

**Core Mandate:**
- **Evoke the Spirit:** Capture the essence of {festival_name} with warmth, grace, and cultural sensitivity. Avoid all clichés, stereotypes, and religious overtones.
- **Brand Identity:** The banner must align with the brand identity of **{brand_name}** and its tone of **{brand_tone}**.
- **Visual Style:** Prioritize a typography-led layout with a beautiful, elegant font. Incorporate tasteful, subtle festive motifs (e.g., abstract representations of lamps, rangoli, diyas, or florals, depending on a festival).
- **Color Palette:** If a color palette is provided ({palette}), use it as the primary inspiration. Otherwise, draw from a sophisticated and modern color scheme that reflects the festival's mood.
- **Composition:** The design must be balanced, with ample negative space. It should include a clear focal point and a headline that reads: **'Happy {festival_name}!'**. Leave a designated area for a subtle brand logo.

**Negative Constraints:**
- No garish colors or overly ornate designs.
- No stock imagery or generic illustrations.
- No direct religious symbolism.

**The final design must be a work of art that is both culturally respectful and visually harmonious for a professional audience.**"""

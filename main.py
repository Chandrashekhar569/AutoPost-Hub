from __future__ import annotations
import os
import sys
import logging
from pydantic import ValidationError
from genai_poster.workflow.langgraph_flow import build_graph, GraphState
from genai_poster.models import AppConfig
from genai_poster.config.settings import DEFAULT_OPENAI_MODEL, DEFAULT_IMAGE_MODEL
from genai_poster.publisher.post_manager import LinkedInClient

LOG = logging.getLogger("festival_linkedin_bot")

def get_config_interactively() -> AppConfig:
    """Get configuration from the user interactively."""
    print("Welcome to the GenAI Poster setup!")
    print("Please provide the following information:")

    openai_api_key = os.getenv("OPENAI_API_KEY") or input("OpenAI API Key: ")
    linkedin_access_token = os.getenv("LINKEDIN_ACCESS_TOKEN") or input("LinkedIn Access Token: ")
    brand_name = os.getenv("BRAND_NAME") or input("Brand Name: ")
    brand_tone = os.getenv("BRAND_TONE") or input("Brand Tone (e.g., warm, celebratory): ")
    hashtags_input = os.getenv("HASHTAGS") or input("Hashtags (comma-separated): ")
    calendar_url = os.getenv("CALENDAR_URL") or input("Calendar URL (ICS file or feed): ")

    os.environ["OPENAI_API_KEY"] = openai_api_key
    os.environ["LINKEDIN_ACCESS_TOKEN"] = linkedin_access_token

    # Get LinkedIn Author URN from the access token
    try:
        linkedin_client = LinkedInClient(linkedin_access_token)
        profile = linkedin_client.get_self_profile()
        linkedin_author_urn = profile["id"]
        print(f"Successfully retrieved LinkedIn Author URN: {linkedin_author_urn}")
    except Exception as e:
        LOG.error("Could not retrieve LinkedIn Author URN: %s", e)
        sys.exit(1)

    hashtags = [h.strip() for h in hashtags_input.split(",") if h.strip()]

    return AppConfig(
        brand_name=brand_name,
        brand_tone=brand_tone,
        hashtags=hashtags,
        linkedin_author_urn=linkedin_author_urn,
        openai_model=os.getenv("OPENAI_MODEL", DEFAULT_OPENAI_MODEL),
        image_model=os.getenv("IMAGE_MODEL", DEFAULT_IMAGE_MODEL),
    )

def main() -> None:
    try:
        cfg = get_config_interactively()
        initial_state: GraphState = {
            "config": cfg,
            "festival": None,
            "post": None,
            "banner": None,
            "banner_path": None,
            "linkedin_result": None,
        }
        app = build_graph().compile()
        final_state = app.invoke(initial_state)

        fest = final_state["festival"]
        post = final_state["post"]
        result = final_state["linkedin_result"]

        LOG.info("Done. Festival: %s | Banner: %s | Post URN: %s", 
                 fest.name if fest else None, final_state.get("banner_path"), result.post_urn if result else None)
        print("\n=== Summary ===")
        print(f"Festival: {fest.name} on {fest.date.isoformat()}" if fest else "Festival: n/a")
        print(f"Banner saved to: {final_state.get('banner_path')}")
        print(f"LinkedIn Post URN: {result.post_urn if result else 'n/a'}")
    except ValidationError as ve:
        LOG.error("Validation error: %s", ve)
        sys.exit(2)
    except Exception as e:
        LOG.exception("Fatal error: %s", e)
        sys.exit(1)

if __name__ == "__main__":
    main()
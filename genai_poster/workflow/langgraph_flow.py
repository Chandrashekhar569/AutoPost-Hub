from __future__ import annotations
import datetime as dt
import logging
import os
from typing import Optional
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, END
from genai_poster.models import AppConfig, FestivalInfo, PostDraft, BannerSpec, LinkedInPostResult
from genai_poster.content.festival_content import get_upcoming_festival, make_llm, POST_PROMPT, BANNER_PROMPT_TMPL
from genai_poster.media.image_generator import generate_image_bytes, save_png
from genai_poster.publisher.post_manager import LinkedInClient
from genai_poster.config.settings import INDIA_TZ, DOWNLOAD_DIR

LOG = logging.getLogger(__name__)

class GraphState(TypedDict):
    config: AppConfig
    festival: Optional[FestivalInfo]
    search_results: Optional[str]
    post: Optional[PostDraft]
    banner: Optional[BannerSpec]
    banner_path: Optional[str]
    linkedin_result: Optional[LinkedInPostResult]

def node_select_festival(state: GraphState) -> GraphState:
    LOG.info("Selecting upcoming festival from client calendar ...")
    today = dt.datetime.now(tz=INDIA_TZ).date()

    calendar_url = os.getenv("CALENDAR_URL")
    if not calendar_url:
        raise RuntimeError("CALENDAR_URL env var required (ICS file or feed URL).")

    fest = get_upcoming_festival(today, calendar_url)
    if not fest:
        raise RuntimeError("No upcoming festivals found in client calendar.")

    state["festival"] = fest
    return state

def node_search_company_info(state: GraphState) -> GraphState:
    LOG.info("Searching for company information ...")
    cfg = state["config"]
    brand_name = cfg.brand_name
    assert brand_name is not None

    try:
        from googlesearch import search
    except ImportError:
        raise RuntimeError("googlesearch-python is not installed. Please install it with `pip install googlesearch-python`")

    query = f"{brand_name} company profile"
    search_results = ""
    for url in search(query, num_results=5):
        search_results += f"- {url}\n"

    state["search_results"] = search_results
    return state

def node_write_post(state: GraphState) -> GraphState:
    LOG.info("Generating LinkedIn post copy via LLM ...")
    cfg = state["config"]
    fest = state["festival"]
    search_results = state["search_results"]
    assert fest is not None

    hashtags_input = os.getenv("HASHTAGS")
    hashtags = (
        [h.strip() for h in hashtags_input.split(",") if h.strip()]
        if hashtags_input else cfg.hashtags
    )

    llm = make_llm(cfg.openai_model)
    prompt = POST_PROMPT.format_messages(
        festival_name=f"{fest.emoji + ' ' if fest.emoji else ''}{fest.name}",
        festival_date=fest.date.isoformat(),
        festival_emoji=fest.emoji or "",
        brand_name=cfg.brand_name or "",
        brand_tone=cfg.brand_tone or "warm, celebratory, professional",
        hashtags=", ".join(hashtags),
        search_results=search_results or "No additional information found."
    )
    msg = llm.invoke(prompt)
    body = msg.content.strip()

    title = f"{fest.emoji + ' ' if fest.emoji else ''}{fest.name}: Celebrating Together"
    state["post"] = PostDraft(festival=fest, title=title, body=body, hashtags=hashtags)
    return state

def node_make_banner(state: GraphState) -> GraphState:
    LOG.info("Generating banner image ...")
    cfg = state["config"]
    fest = state["festival"]
    assert fest is not None

    palette = ", ".join(fest.colors or ["brand palette"])
    prompt = BANNER_PROMPT_TMPL.format(
        festival_name=fest.name,
        brand_tone=cfg.brand_tone,
        palette=palette,
        brand_name=cfg.brand_name
    )

    banner = BannerSpec(festival=fest, prompt=prompt)
    png = generate_image_bytes(prompt=banner.prompt, width=banner.width, height=banner.height, image_model=cfg.image_model)

    filename = f"banner_{fest.date.isoformat()}_{fest.name.lower().replace(' ', '_')}.png"
    out_path = DOWNLOAD_DIR / filename
    save_png(png, out_path)

    state["banner"] = banner
    state["banner_path"] = str(out_path)
    return state

def node_post_linkedin(state: GraphState) -> GraphState:
    LOG.info("Posting to LinkedIn ...")
    cfg = state["config"]
    post = state["post"]
    banner_path = state["banner_path"]
    assert post is not None and banner_path is not None

    access_token = os.getenv("LINKEDIN_ACCESS_TOKEN")
    if not access_token:
        raise RuntimeError("LINKEDIN_ACCESS_TOKEN not set.")

    client = LinkedInClient(access_token)
    asset_urn, upload_url = client.register_image_upload(cfg.linkedin_author_urn)
    print(upload_url)
    with open(banner_path, "rb") as f:
        binary = f.read()
    client.upload_binary(upload_url, binary, content_type="image/png")

    # Compose text: title + body (LinkedIn ignores titles for UGC; keep in text)
    text = f"{post.title}\n\n{post.body}"
    result = client.create_post_with_image(cfg.linkedin_author_urn, asset_urn, text)

    state["linkedin_result"] = result
    return state

def build_graph() -> StateGraph:
    graph = StateGraph(GraphState)
    graph.add_node("select_festival", node_select_festival)
    graph.add_node("search_company_info", node_search_company_info)
    graph.add_node("write_post", node_write_post)
    graph.add_node("make_banner", node_make_banner)
    graph.add_node("post_linkedin", node_post_linkedin)

    graph.set_entry_point("select_festival")
    graph.add_edge("select_festival", "search_company_info")
    graph.add_edge("search_company_info", "write_post")
    graph.add_edge("write_post", "make_banner")
    graph.add_edge("make_banner", "post_linkedin")
    graph.add_edge("post_linkedin", END)
    return graph

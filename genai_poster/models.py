
from __future__ import annotations
import datetime as dt
from typing import List, Optional
from pydantic import BaseModel, Field
from genai_poster.config.settings import DEFAULT_OPENAI_MODEL, DEFAULT_IMAGE_MODEL

class FestivalInfo(BaseModel):
    name: str
    date: dt.date
    region: Optional[str] = None
    emoji: Optional[str] = None
    colors: Optional[List[str]] = None

class PostDraft(BaseModel):
    festival: FestivalInfo
    title: str
    body: str
    hashtags: List[str]

class BannerSpec(BaseModel):
    festival: FestivalInfo
    prompt: str
    width: int = 1024
    height: int = 1024

class LinkedInPostResult(BaseModel):
    post_urn: Optional[str]
    asset_urn: Optional[str]
    share_url: Optional[str]

class AppConfig(BaseModel):
    brand_name: Optional[str] = Field(default=None, description="Brand name to include")
    brand_tone: Optional[str] = Field(default="warm, celebratory, professional")
    hashtags: List[str] = Field(default_factory=lambda: ["#Festival", "#Celebration", "#Community"]) 
    linkedin_author_urn: str = Field(..., description="urn:li:person:XXXX or urn:li:organization:XXXX")
    openai_model: str = Field(default=DEFAULT_OPENAI_MODEL)
    image_model: str = Field(default=DEFAULT_IMAGE_MODEL)

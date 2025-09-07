from __future__ import annotations
from typing import Tuple
import requests
from genai_poster.models import LinkedInPostResult

class LinkedInClient:
    def __init__(self, access_token: str):
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {access_token}",
            "X-Restli-Protocol-Version": "2.0.0",
            "Content-Type": "application/json",
        })
        self.api_base = "https://api.linkedin.com/v2"

    def register_image_upload(self, owner_urn: str) -> Tuple[str, str]:
        url = f"{self.api_base}/assets?action=registerUpload"
        payload = {
            "registerUploadRequest": {
                "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
                "owner": owner_urn,
                "serviceRelationships": [
                    {"relationshipType": "OWNER", "identifier": "urn:li:userGeneratedContent"}
                ],
            }
        }
        r = self.session.post(url, json=payload)
        if r.status_code >= 300:
            raise RuntimeError(f"LinkedIn registerUpload failed: {r.status_code} {r.text}")
        data = r.json()
        asset_urn = data.get("value", {}).get("asset")
        upload_url = data.get("value", {}).get("uploadMechanism", {}) \
            .get("com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest", {}) \
            .get("uploadUrl")
        if not asset_urn or not upload_url:
            raise RuntimeError(f"Invalid registerUpload response: {data}")
        return asset_urn, upload_url

    def upload_binary(self, upload_url: str, binary: bytes, content_type: str = "image/png") -> None:
        headers = {"Content-Type": content_type}
        r = requests.put(upload_url, data=binary, headers=headers)
        if r.status_code >= 300:
            raise RuntimeError(f"LinkedIn binary upload failed: {r.status_code} {r.text}")

    def create_post_with_image(self, owner_urn: str, asset_urn: str, text: str) -> LinkedInPostResult:
        url = f"{self.api_base}/ugcPosts"
        payload = {
            "author": owner_urn,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {"text": text},
                    "shareMediaCategory": "IMAGE",
                    "media": [
                        {
                            "status": "READY",
                            "description": {"text": ""},
                            "media": asset_urn,
                            "title": {"text": ""},
                        }
                    ],
                }
            },
            "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
        }
        r = self.session.post(url, json=payload)
        if r.status_code >= 300:
            raise RuntimeError(f"LinkedIn post failed: {r.status_code} {r.text}")
        post_urn = r.headers.get("x-restli-id")
        return LinkedInPostResult(post_urn=post_urn, asset_urn=asset_urn, share_url=None)

    def get_self_profile(self) -> dict:
        url = f"{self.api_base}/userinfo"
        r = self.session.get(url)
        r.raise_for_status()
        return r.json()

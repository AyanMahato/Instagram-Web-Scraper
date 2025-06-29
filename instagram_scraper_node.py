import os
import logging
import requests
from typing import Literal, Optional
from pydantic import BaseModel, Field
from fastapi import HTTPException

logger = logging.getLogger("uvicorn.error")
logger.setLevel(logging.INFO)


class InstagramScraperNodeParams(BaseModel):
    search_type: Literal['Hashtag', 'User Profile'] = Field(...)
    search_term: str = Field(...)
    posts_limit: int = Field(default=10, ge=0, le=1000)
    timeframe: Literal[
        'Last 24 hours', 'Last 7 days', 'Last 30 days', 'Last 6 months', 'Any time'
    ] = Field(default='Any time')
    include_comments: bool = Field(default=False)
    comments_per_post_limit: int = Field(default=20, ge=0, le=200)
    location: Optional[str] = None


class InstagramScraperNode:
    def __init__(self, params: InstagramScraperNodeParams):
        self.params = params
        self.api_key = os.getenv("INSTAGRAM_SCRAPER_API_KEY")
        self.actor_id = os.getenv("INSTAGRAM_SCRAPER_ACTOR_ID")

        if not self.api_key:
            raise HTTPException(status_code=401, detail="API key not found in environment")
        if not self.actor_id:
            raise HTTPException(status_code=500, detail="Actor ID not set in environment")

        self.api_url = f"https://api.apify.com/v2/acts/{self.actor_id}/run-sync-get-dataset-items?token={self.api_key}"

    def _map_timeframe(self) -> Optional[str]:
        return {
            'Last 24 hours': '1 day',
            'Last 7 days': '7 days',
            'Last 30 days': '30 days',
            'Last 6 months': '180 days',
            'Any time': None
        }[self.params.timeframe]

    def _get_common_fields(self) -> dict:
        payload = {
            "addParentData": False,
            "enhanceUserSearchWithFacebookPage": False,
            "isUserReelFeedURL": False,
            "isUserTaggedFeedURL": False,
        }
        if self.params.include_comments:
            payload["includeComments"] = True
            payload["commentsLimit"] = self.params.comments_per_post_limit
        if self.params.location:
            payload["location"] = self.params.location
        if tf := self._map_timeframe():
            payload["onlyPostsNewerThan"] = tf
        return payload

    def _fetch_from_apify(self, payload: dict) -> list:
        try:
            logger.info("Sending Apify request with payload: %s", payload)
            response = requests.post(self.api_url, json=payload, timeout=90)
            if response.status_code not in [200, 201]:
                raise HTTPException(
                    status_code=502,
                    detail=f"Apify API error: {response.status_code}, {response.text}"
                )
            return response.json()
        except requests.exceptions.Timeout:
            raise HTTPException(status_code=504, detail="Timeout contacting Apify")
        except requests.RequestException as e:
            raise HTTPException(status_code=502, detail=f"Request failed: {str(e)}")

    def execute(self) -> dict:
        if self.params.search_type == "Hashtag":
            if self.params.posts_limit == 0:
                raise HTTPException(status_code=400, detail="posts_limit must be > 0 for hashtag search")

            payload = {
                **self._get_common_fields(),
                "searchType": "hashtag",
                "resultsType": "posts",
                "search": self.params.search_term.lstrip("#"),
                "resultsLimit": self.params.posts_limit,
                "searchLimit": self.params.posts_limit,
            }
            result = self._fetch_from_apify(payload)
            return {"posts": result}

        elif self.params.search_type == "User Profile":

            direct_url = f"https://www.instagram.com/{self.params.search_term}/"
            posts = []
            if self.params.posts_limit > 0:
                post_payload = {
                    **self._get_common_fields(),
                    "searchType": "user",
                    "resultsType": "posts",
                    "directUrls": [direct_url],
                    "resultsLimit": self.params.posts_limit,
                    "searchLimit": self.params.posts_limit,
                }
                posts = self._fetch_from_apify(post_payload)

            # Fetch profile details
            details_payload = {
                **self._get_common_fields(),
                "searchType": "user",
                "resultsType": "details",
                "directUrls": [direct_url],
            }
            details = self._fetch_from_apify(details_payload)

            return {
                "profile": details[0] if isinstance(details, list) and len(details) > 0 else details,
                "posts": posts,
            }

        else:
            raise HTTPException(status_code=400, detail="Invalid search_type")

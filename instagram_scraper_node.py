import os
import time
import requests
import datetime
import logging
from typing import List, Optional, Literal
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Use uvicorn's logger
logger = logging.getLogger("uvicorn")

load_dotenv(".env")


class Comment(BaseModel):
    author_username: str
    comment_text: str
    timestamp: Optional[datetime.datetime]


class Post(BaseModel):
    post_url: Optional[str]
    author_username: Optional[str]
    author_follower_count: int
    post_content: Optional[str]
    timestamp: Optional[datetime.datetime]
    like_count: int
    comment_count: int
    view_count: Optional[int] = None
    media_urls: List[str] = Field(default_factory=list)
    image_urls: List[str] = Field(default_factory=list)
    comments: List[Comment] = Field(default_factory=list)


class Profile(BaseModel):
    username: str
    follower_count: int
    following_count: int
    post_count: int
    bio_text: Optional[str] = None
    external_url: Optional[str] = None
    recent_posts: List[Post]


class InstagramScraperNodeParams(BaseModel):
    search_type: Literal['Hashtag', 'Keyword Search', 'User Profile']
    search_term: str
    posts_limit: int = Field(default=10, gt=0, le=1000)
    timeframe: Literal['Last 24 hours', 'Last 7 days', 'Last 30 days', 'Last 6 months', 'Any time'] = 'Any time'
    include_comments: bool = False
    comments_per_post_limit: int = Field(default=5, gt=0, le=200)
    location: Optional[str] = None


class InstagramScraperNode:
    def __init__(self, params: InstagramScraperNodeParams):
        self.params = params
        self.api_key = os.getenv("INSTAGRAM_SCRAPER_API_KEY")
        self.actor_id = os.getenv("INSTAGRAM_SCRAPER_ACTOR_ID")

        if not self.api_key:
            raise Exception("Missing Apify API key")
        if not self.actor_id:
            raise Exception("Missing Actor ID")

        logger.info(f"Initialized InstagramScraperNode with type={params.search_type}, term={params.search_term}")

    def execute(self) -> dict:
        search_type_map = {
            "Hashtag": "hashtag",
            "Keyword Search": "keyword",
            "User Profile": "user"
        }

        search_type = search_type_map[self.params.search_type]

        payload = {
            "searchType": search_type,
            "search": self.params.search_term,
            "resultsLimit": self.params.posts_limit,
            "resultsType": "posts",
            "addParentData": False,
            "enhanceUserSearchWithFacebookPage": False,
            "isUserReelFeedURL": False,
            "isUserTaggedFeedURL": False,
            "searchLimit": 1
        }

        # Add directUrls for profile
        if self.params.search_type == "User Profile":
            payload["directUrls"] = [f"https://www.instagram.com/{self.params.search_term}/"]

        # Add timeframe filter
        if self.params.timeframe != "Any time":
            delta_map = {
                "Last 24 hours": datetime.timedelta(days=1),
                "Last 7 days": datetime.timedelta(days=7),
                "Last 30 days": datetime.timedelta(days=30),
                "Last 6 months": datetime.timedelta(days=180),
            }
            delta = delta_map.get(self.params.timeframe)
            since_date = datetime.datetime.utcnow() - delta
            payload["onlyPostsNewerThan"] = since_date.strftime("%Y-%m-%d")

        logger.info(f"Sending payload to Apify: {payload}")

        # Step 1: Start actor
        run_url = f"https://api.apify.com/v2/acts/{self.actor_id}/runs"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        response = requests.post(run_url, headers=headers, json=payload)
        if response.status_code != 201:
            raise Exception(f"Failed to start Apify actor. Response: {response.text}")

        run_id = response.json()["data"]["id"]
        logger.info(f"Actor started with run_id: {run_id}")

        # Step 2: Poll status
        status_url = f"https://api.apify.com/v2/actor-runs/{run_id}"
        for _ in range(60):
            status_resp = requests.get(status_url, headers=headers).json()
            status = status_resp['data']['status']
            if status == "SUCCEEDED":
                dataset_id = status_resp['data']['defaultDatasetId']
                logger.info(f"Actor run succeeded. Dataset ID: {dataset_id}")
                break
            elif status == "FAILED":
                raise Exception("Apify actor run failed.")
            time.sleep(5)
        else:
            raise Exception("Timeout: Actor run did not complete in time.")

        # Step 3: Fetch data
        data_url = f"https://api.apify.com/v2/datasets/{dataset_id}/items?format=json&clean=1"
        data = requests.get(data_url, headers=headers).json()

        if not data:
            raise Exception("No data returned from dataset.")

        # Parse results
        if self.params.search_type == "User Profile":
            item = data[0]
            profile = Profile(
                username=item.get('username', ''),
                follower_count=item.get('followers', 0),
                following_count=item.get('following', 0),
                post_count=item.get('postsCount', 0),
                bio_text=item.get('bio', ''),
                external_url=item.get('externalUrl'),
                recent_posts=[self._parse_post(p) for p in item.get('latestPosts', [])]
            )
            return {"instagram_results": profile.dict()}

        return {
            "instagram_results": [self._parse_post(post).dict() for post in data]
        }

    def _parse_post(self, post: dict) -> Post:
        comments = []
        for c in post.get('comments', [])[:self.params.comments_per_post_limit]:
            try:
                timestamp = datetime.datetime.fromisoformat(c.get('timestamp')) if c.get('timestamp') else None
            except ValueError:
                timestamp = None

            comments.append(Comment(
                author_username=c.get('ownerUsername', 'unknown'),
                comment_text=c.get('text', ''),
                timestamp=timestamp
            ))

        try:
            post_timestamp = datetime.datetime.fromisoformat(post.get('timestamp')) if post.get('timestamp') else None
        except ValueError:
            post_timestamp = None

        return Post(
            post_url=post.get('url'),
            author_username=post.get('ownerUsername') or post.get('username'),
            author_follower_count=post.get('ownerFollowers', 0),
            post_content=post.get('caption', ''),
            timestamp=post_timestamp,
            like_count=post.get('likesCount', 0),
            comment_count=post.get('commentsCount', 0),
            image_urls=post.get('imageUrls', []),
            media_urls=post.get('mediaUrls', post.get('imageUrls', [])),
            comments=comments
        )
